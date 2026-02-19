"""Terminal tools — explain (read-only), exec (persistent shell), type (input)."""
import re
from typing import Optional
from jupiter.safety.broker import ToolResult
from jupiter.agent.shell import get_shell

SAFE_READ_ONLY = frozenset({
    "cat", "head", "tail", "less", "grep", "ls", "pwd", "whoami", "date",
    "echo", "env", "which", "type", "man", "help",
    "ip", "ifconfig", "nmap", "netstat", "ss", "arp", "route", "traceroute",
    "ping", "dig", "host", "whois", "curl", "wget",
    "ps", "top", "htop", "who", "w", "id", "uname", "hostname",
    "df", "du", "free", "uptime", "lsblk", "lsusb", "lspci",
    "file", "find", "locate", "wc", "sort", "uniq", "stat",
    "md5sum", "sha256sum", "strings",
})

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub('', text)

def terminal_explain(command: str) -> ToolResult:
    cmd = command.strip().split()
    name = cmd[0].lower() if cmd else ""
    note = "This is a common read-only command." if name in SAFE_READ_ONLY else "This command may modify system state. Confirm before executing."
    return ToolResult(success=True, output=f"Command: {command}\nNote: {note}")

def terminal_exec(command: str, timeout_seconds: int = 120) -> ToolResult:
    if not command or not command.strip():
        return ToolResult(success=False, output="", error="Empty command")

    try:
        shell = get_shell()
        output = shell.exec(command, timeout=timeout_seconds)
        
        # Check for interactive prompt signal from shell
        if output.startswith("INTERACTIVE_PROMPT_NEEDED:"):
            return ToolResult(
                success=False, 
                output=output, 
                error=f"Command requires interactive input (e.g. password). Use 'terminal_type' to provide it. prompt detected: {output}",
                audit_action="terminal_exec_interactive"
            )
        
        clean_out = strip_ansi(output).strip()
        return ToolResult(
            success=True, 
            output=clean_out[:16384],
            error=None,
            audit_action="terminal_exec"
        )
            
    except Exception as e:
        return ToolResult(success=False, output="", error=f"Shell error: {str(e)}", audit_action="terminal_exec_error")

def terminal_type(text: str, timeout_seconds: int = 30) -> ToolResult:
    """Type text into the running shell (e.g. for passwords/prompts)."""
    try:
        shell = get_shell()
        # reusing exec logic: writes text+newline, waits for prompt
        output = shell.exec(text, timeout=timeout_seconds)
        
        clean_out = strip_ansi(output).strip()
        return ToolResult(
            success=True, 
            output=f"(Input sent) Output:\n{clean_out[:16384]}",
            error=None,
            audit_action="terminal_input_hidden" # Don't log content in audit action name, though args will be logged by broker if not careful? 
            # Broker logs 'details'. We rely on SafetyBroker to handle sensitive args if needed, 
            # or accept that local audit logs have it.
        )
    except Exception as e:
        return ToolResult(success=False, output="", error=f"Shell error: {str(e)}", audit_action="terminal_input_error")
