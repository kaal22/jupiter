"""Jupiter Agent Daemon — planner + executor with ReAct agentic loop."""
import sys
from typing import Optional, Callable, Union
from jupiter.config import ensure_dirs
from jupiter.safety.broker import SafetyBroker, Scope, ToolResult
from jupiter.storage.audit import AuditStore
from jupiter.storage.memory import MemoryStore
from jupiter.agent.planner import JupiterPlanner
from jupiter.tools.system import system_status, system_logs_tail, system_diagnostics
from jupiter.tools.terminal import terminal_explain, terminal_exec

MAX_AGENT_STEPS = 6

# All valid tool action names
TOOL_ACTIONS = frozenset({
    "system_status", "system_logs_tail", "system_diagnostics",
    "terminal_explain", "terminal_exec",
    "remember_preference", "remember_summary", "audit_log",
})


def execute_plan(plan: dict, broker: SafetyBroker, memory: MemoryStore, confirm_callback: Optional[Callable[[str], bool]] = None) -> Union[str, ToolResult]:
    action = plan.get("action", "reply")
    if action == "reply":
        return plan.get("content", "No reply generated.")

    # Resolve tool name
    if action == "tool":
        tool = plan.get("tool", "")
    elif action in TOOL_ACTIONS:
        tool = action
    else:
        return f"Unknown action: {action}"

    args = plan.get("args") or {}
    initial_confirmed = plan.get("confirmed", False)
    
    def run_tool_logic(is_confirmed: bool) -> Union[str, ToolResult]:
        # Memory tools
        if tool == "remember_preference":
            if not is_confirmed: return "Action requires explicit user confirmation."
            key, value = args.get("key"), args.get("value")
            if not key: return "remember_preference needs args: key, value"
            memory.preference_set(key, value or "")
            return f"Stored preference: {key} = {value}"
        
        if tool == "remember_summary":
            if not is_confirmed: return "Action requires explicit user confirmation."
            summary = args.get("summary") or ""
            if not summary: return "remember_summary needs args: summary"
            memory.episodic_add(summary)
            return f"Remembered: {summary}"
            
        # Audit log
        if tool == "audit_log":
            limit = int(args.get("limit", 20))
            entries = broker.audit.get_recent(limit)
            if not entries: return "No audit entries yet."
            lines = [f"  {e.get('created_at')} | {e.get('action')} | {e.get('scope')} | {e.get('outcome')}" for e in entries]
            return "Recent audit log:\n" + "\n".join(lines)

        tool_map = {
            "system_status": (Scope.SYSTEM_READ, lambda: system_status()),
            "system_logs_tail": (Scope.SYSTEM_READ, lambda: system_logs_tail(args.get("service"), args.get("lines", 20))),
            "system_diagnostics": (Scope.SYSTEM_READ, lambda: system_diagnostics()),
            "terminal_explain": (Scope.TERMINAL_READ, lambda: terminal_explain(args.get("command", ""))),
            "terminal_exec": (Scope.TERMINAL_EXEC, lambda: terminal_exec(args.get("command", ""), args.get("timeout_seconds", 120))),
        }
        
        if tool not in tool_map:
            return f"Unknown tool: {tool}"
            
        scope, fn = tool_map[tool]
        return broker.execute(tool, scope, fn, confirmed=is_confirmed)

    # First attempt
    result = run_tool_logic(initial_confirmed)
    
    # Handle string confirmation request (memory tools)
    if isinstance(result, str):
        if result == "Action requires explicit user confirmation." and confirm_callback:
            if confirm_callback(f"Allow {tool} {args}?"):
                return run_tool_logic(True)
            return "User denied confirmation."
        return result
        
    # Handle ToolResult confirmation request (broker)
    if isinstance(result, ToolResult) and not result.success and "confirmation" in (result.error or "").lower():
        if confirm_callback:
            cmd_preview = args.get("command", "") if tool == "terminal_exec" else str(args)
            if confirm_callback(f"Allow {tool}: {cmd_preview}"):
                # Retry with confirmation
                retry_result = run_tool_logic(True)
                if isinstance(retry_result, ToolResult):
                    return retry_result.error or retry_result.output
                return retry_result
                
    if isinstance(result, ToolResult):
        return result.error or result.output
    return str(result)


def _is_loop(observations: list) -> bool:
    if len(observations) < 2:
        return False
    last = observations[-1]
    prev = observations[-2]
    return last["tool"] == prev["tool"] and last["args"] == prev["args"]


def agent_loop(
    user_message: str,
    planner: JupiterPlanner,
    broker: SafetyBroker,
    memory: MemoryStore,
    max_steps: int = MAX_AGENT_STEPS,
    on_tool_start: Optional[Callable] = None,
    on_tool_result: Optional[Callable] = None,
    on_thinking: Optional[Callable] = None,
    confirm_callback: Optional[Callable[[str], bool]] = None,
) -> str:
    memory.session_append("user", user_message)
    observations = []

    for step in range(max_steps):
        if on_thinking:
            on_thinking(step + 1, len(observations))

        plan = planner.plan(user_message, observations=observations)
        action = plan.get("action", "reply")

        if action == "reply":
            reply = plan.get("content", "No reply generated.")
            memory.session_append("assistant", reply)
            return reply

        if action in TOOL_ACTIONS or action == "tool":
            tool_name = plan.get("tool", action) if action == "tool" else action
            tool_args = plan.get("args", {})
            if on_tool_start:
                on_tool_start(step + 1, tool_name, tool_args)
            
            result = execute_plan(plan, broker, memory, confirm_callback=confirm_callback)
            
            obs = {
                "step": step + 1,
                "tool": tool_name,
                "args": tool_args,
                "result": result[:4096],
            }
            observations.append(obs)
            if on_tool_result:
                on_tool_result(step + 1, tool_name, result)

            if _is_loop(observations):
                parts = ["I ran into an issue (repeated command). Here's what I got:\n"]
                for o in observations:
                    parts.append(f"[{o['tool']}] {o['result'][:2000]}")
                final = "\n\n".join(parts)
                memory.session_append("assistant", final)
                return final
            continue

        reply = plan.get("content", str(plan))
        memory.session_append("assistant", reply)
        return reply

    parts = ["Completed multiple steps:\n"]
    for obs in observations:
        parts.append(f"[{obs['tool']}] {obs['result'][:2000]}")
    final = "\n\n".join(parts)
    memory.session_append("assistant", final)
    return final


def run_daemon_loop(planner: JupiterPlanner, broker: SafetyBroker, memory: MemoryStore):
    ensure_dirs()
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            user_message = line.strip()
            if not user_message:
                continue
            
            def cli_confirm(msg: str) -> bool:
                # Basic CLI confirmation interacting with stdin
                print(f"\n[CONFIRM] {msg} (y/n): ", end="", flush=True)
                ans = sys.stdin.readline().strip().lower()
                return ans.startswith('y')

            output = agent_loop(user_message, planner, broker, memory, confirm_callback=cli_confirm)
            print(output, flush=True)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr, flush=True)


def run_daemon(model: Optional[str] = None, ollama_base: Optional[str] = None):
    from jupiter.config import OLLAMA_BASE_URL, DEFAULT_MODEL
    ensure_dirs()
    memory = MemoryStore()
    audit = AuditStore()
    broker = SafetyBroker(audit=audit)
    planner = JupiterPlanner(base_url=ollama_base or OLLAMA_BASE_URL, model=model or memory.preference_get("model") or DEFAULT_MODEL, memory=memory)
    run_daemon_loop(planner, broker, memory)


if __name__ == "__main__":
    run_daemon()
