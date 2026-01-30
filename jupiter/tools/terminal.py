"""Terminal tools — explain (read-only), exec (restricted)."""
import subprocess
from typing import Optional
from jupiter.safety.broker import ToolResult

SAFE_READ_ONLY = frozenset({"cat", "head", "tail", "less", "grep", "ls", "pwd", "whoami", "date", "echo", "env", "which", "type", "man", "help"})


def terminal_explain(command: str) -> ToolResult:
    cmd = command.strip().split()
    name = cmd[0].lower() if cmd else ""
    note = "This is a common read-only command." if name in SAFE_READ_ONLY else "This command may modify system state. Confirm before executing."
    return ToolResult(success=True, output=f"Command: {command}\nNote: {note}")


def terminal_exec(command: str, timeout_seconds: int = 30) -> ToolResult:
    if not command or not command.strip():
        return ToolResult(success=False, output="", error="Empty command")
    if command.strip().lower().startswith("sudo"):
        return ToolResult(success=False, output="", error="sudo is not allowed via Jupiter")
    try:
        r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout_seconds)
        out = (r.stdout or "") + (r.stderr or "")
        return ToolResult(success=r.returncode == 0, output=out[:8192], error=None if r.returncode == 0 else f"Exit code {r.returncode}", audit_action="terminal_exec")
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output="", error="Command timed out", audit_action="terminal_exec_timeout")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e), audit_action="terminal_exec_error")
