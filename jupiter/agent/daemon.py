"""Jupiter Agent Daemon — planner + executor with ReAct agentic loop."""
import sys
from typing import Optional, Callable
from jupiter.config import ensure_dirs
from jupiter.safety.broker import SafetyBroker, Scope
from jupiter.storage.audit import AuditStore
from jupiter.storage.memory import MemoryStore
from jupiter.agent.planner import JupiterPlanner
from jupiter.tools.system import system_status, system_logs_tail, system_diagnostics
from jupiter.tools.terminal import terminal_explain, terminal_exec

MAX_AGENT_STEPS = 10


def execute_plan(plan: dict, broker: SafetyBroker, memory: MemoryStore) -> str:
    action = plan.get("action", "reply")
    if action == "reply":
        return plan.get("content", "No reply generated.")
    if action != "tool":
        return "Unknown action."
    tool = plan.get("tool", "")
    args = plan.get("args") or {}
    confirmed = plan.get("confirmed", False)

    # Memory tools
    if tool == "remember_preference":
        if not confirmed:
            return "User must confirm before I store a preference."
        key, value = args.get("key"), args.get("value")
        if not key:
            return "remember_preference needs args: key, value"
        memory.preference_set(key, value or "")
        return f"Stored preference: {key} = {value}"
    if tool == "remember_summary":
        if not confirmed:
            return "User must confirm before I remember that."
        summary = args.get("summary") or ""
        if not summary:
            return "remember_summary needs args: summary"
        memory.episodic_add(summary)
        return f"Remembered: {summary}"

    # Audit log
    if tool == "audit_log":
        limit = int(args.get("limit", 20))
        entries = broker.audit.get_recent(limit)
        if not entries:
            return "No audit entries yet."
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
    result = broker.execute(tool, scope, fn, confirmed=confirmed)
    return result.error or result.output


def agent_loop(
    user_message: str,
    planner: JupiterPlanner,
    broker: SafetyBroker,
    memory: MemoryStore,
    max_steps: int = MAX_AGENT_STEPS,
    on_tool_start: Optional[Callable] = None,
) -> str:
    """ReAct-style agentic loop: plan -> execute -> observe -> repeat until reply."""
    memory.session_append("user", user_message)
    observations = []

    for step in range(max_steps):
        plan = planner.plan(user_message, observations=observations)

        if plan.get("action") == "reply":
            reply = plan.get("content", "No reply generated.")
            memory.session_append("assistant", reply)
            return reply

        if plan.get("action") == "tool":
            tool_name = plan.get("tool", "unknown")
            tool_args = plan.get("args", {})
            if on_tool_start:
                on_tool_start(step + 1, tool_name, tool_args)
            result = execute_plan(plan, broker, memory)
            observations.append({
                "step": step + 1,
                "tool": tool_name,
                "args": tool_args,
                "result": result[:4096],
            })
            continue

        # Unknown action
        reply = plan.get("content", str(plan))
        memory.session_append("assistant", reply)
        return reply

    # Max steps — compile results
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
            output = agent_loop(user_message, planner, broker, memory)
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
