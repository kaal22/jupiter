"""Jupiter Agent Daemon — planner + executor."""
import sys
from typing import Optional
from jupiter.config import ensure_dirs
from jupiter.safety.broker import SafetyBroker, Scope
from jupiter.storage.audit import AuditStore
from jupiter.storage.memory import MemoryStore
from jupiter.agent.planner import JupiterPlanner
from jupiter.tools.system import system_status, system_logs_tail, system_diagnostics
from jupiter.tools.terminal import terminal_explain, terminal_exec


def execute_plan(plan: dict, broker: SafetyBroker) -> str:
    action = plan.get("action", "reply")
    if action == "reply":
        return plan.get("content", "No reply generated.")
    if action != "tool":
        return "Unknown action."
    tool = plan.get("tool", "")
    args = plan.get("args") or {}
    confirmed = plan.get("confirmed", False)
    tool_map = {
        "system_status": (Scope.SYSTEM_READ, lambda: system_status()),
        "system_logs_tail": (Scope.SYSTEM_READ, lambda: system_logs_tail(args.get("service"), args.get("lines", 20))),
        "system_diagnostics": (Scope.SYSTEM_READ, lambda: system_diagnostics()),
        "terminal_explain": (Scope.TERMINAL_READ, lambda: terminal_explain(args.get("command", ""))),
        "terminal_exec": (Scope.TERMINAL_EXEC, lambda: terminal_exec(args.get("command", ""), args.get("timeout_seconds", 30))),
    }
    if tool not in tool_map:
        return f"Unknown tool: {tool}"
    scope, fn = tool_map[tool]
    result = broker.execute(tool, scope, fn, confirmed=confirmed)
    return result.error or result.output


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
            memory.session_append("user", user_message)
            plan = planner.plan(user_message)
            output = execute_plan(plan, broker)
            memory.session_append("assistant", output)
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
