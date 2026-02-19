"""Terminal tools — explain (read-only), exec."""
import subprocess
from typing import Optional
from jupiter.safety.broker import ToolResult

SAFE_READ_ONLY = frozenset({
    "cat", "head", "tail", "less", "grep", "ls", "pwd", "whoami", "date",
    "echo", "env", "which", "type", "man", "help",
    # Network/system info
    "ip", "ifconfig", "nmap", "netstat", "ss", "arp", "route", "traceroute",
    "ping", "dig", "host", "whois", "curl", "wget",
    # Process/system info
    "ps", "top", "htop", "who", "w", "id", "uname", "hostname",
    "df", "du", "free", "uptime", "lsblk", "lsusb", "lspci",
    # File info
    "file", "find", "locate", "wc", "sort", "uniq", "stat",
    "md5sum", "sha256sum", "strings",
})


def terminal_explain(command: str) -> ToolResult:
    cmd = command.strip().split()
    name = cmd[0].lower() if cmd else ""
    note = "This is a common read-only command." if name in SAFE_READ_ONLY else "This command may modify system state. Confirm before executing."
    return ToolResult(success=True, output=f"Command: {command}\nNote: {note}")


def terminal_exec(command: str, timeout_seconds: int = 120) -> ToolResult:
    if not command or not command.strip():
        return ToolResult(success=False, output="", error="Empty command")
    try:
        # Pass input="" to ensure we don't hang on stdin prompts (like sudo password)
        # This causes sudo to fail immediately instead of hanging
        r = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            input="", 
            timeout=timeout_seconds
        )
        out = (r.stdout or "") + (r.stderr or "")
        
        # Detect sudo failure explicitly
        if "sudo: a password is required" in out or "sudo: no tty present" in out:
            return ToolResult(
                success=False, 
                output=out, 
                error="Command requires sudo password (cannot run interactively). Please run manually in terminal.", 
                audit_action="terminal_exec_sudo_fail"
            )
            
        return ToolResult(
            success=r.returncode == 0, 
            output=out[:8192], 
            error=None if r.returncode == 0 else f"Exit code {r.returncode}\n{out}", 
            audit_action="terminal_exec"
        )
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, output="", error=f"Command timed out after {timeout_seconds}s", audit_action="terminal_exec_timeout")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e), audit_action="terminal_exec_error")
