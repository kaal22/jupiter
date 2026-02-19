"""Terminal tools — explain (read-only), exec."""
import subprocess
import sys
import os
import time
import select
from typing import Optional
from jupiter.safety.broker import ToolResult

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


def terminal_explain(command: str) -> ToolResult:
    cmd = command.strip().split()
    name = cmd[0].lower() if cmd else ""
    note = "This is a common read-only command." if name in SAFE_READ_ONLY else "This command may modify system state. Confirm before executing."
    return ToolResult(success=True, output=f"Command: {command}\nNote: {note}")


def terminal_exec(command: str, timeout_seconds: int = 120) -> ToolResult:
    if not command or not command.strip():
        return ToolResult(success=False, output="", error="Empty command")

    # Try using PTY (Linux/Mac) for better terminal behavior
    try:
        import pty
        use_pty = True
    except ImportError:
        use_pty = False

    if use_pty:
        master, slave = pty.openpty()
        try:
            p = subprocess.Popen(
                ["/bin/bash", "-c", command],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                close_fds=True
            )
            os.close(slave)  # Close slave in parent so EOF works correctly
            
            output_buffer = []
            start_time = time.time()
            
            while p.poll() is None:
                # Check for timeout
                if time.time() - start_time > timeout_seconds:
                    p.terminate()
                    return ToolResult(success=False, output="".join(output_buffer), error=f"Command timed out after {timeout_seconds}s", audit_action="terminal_exec_timeout")
                
                # Check for output on master fd
                r, _, _ = select.select([master], [], [], 0.1)
                if master in r:
                    try:
                        data = os.read(master, 1024)
                        if data:
                            chunk = data.decode('utf-8', errors='replace')
                            output_buffer.append(chunk)
                        else:
                            break  # EOF
                    except OSError:
                        break
            
            # Process finished, confirm return code (wait a tiny bit just in case)
            p.wait()
            
            # Read any remaining output
            try:
                # Non-blocking read until empty
                while True:
                    r, _, _ = select.select([master], [], [], 0)
                    if master in r:
                        data = os.read(master, 1024)
                        if data:
                            output_buffer.append(data.decode('utf-8', errors='replace'))
                        else:
                            break
                    else:
                        break
            except OSError:
                pass
            
            full_output = "".join(output_buffer)
            # Check for sudo failure specific string if present in output
            if "sudo: a password is required" in full_output:
                return ToolResult(success=False, output=full_output, error="Command requires sudo password. Run manually.", audit_action="terminal_exec_sudo_fail")

            return ToolResult(
                success=p.returncode == 0,
                output=full_output[:8192],
                error=None if p.returncode == 0 else f"Exit code {p.returncode}",
                audit_action="terminal_exec"
            )
            
        except Exception as e:
            return ToolResult(success=False, output="", error=f"PTY exec error: {str(e)}", audit_action="terminal_exec_error")
        finally:
            try:
                os.close(master)
            except OSError:
                pass

    else:
        # Fallback for Windows
        try:
            r = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                input="", 
                timeout=timeout_seconds
            )
            out = (r.stdout or "") + (r.stderr or "")
            if "sudo: a password is required" in out:
                 return ToolResult(success=False, output=out, error="Command requires sudo password. Run manually.", audit_action="terminal_exec_sudo_fail")
            
            return ToolResult(
                success=r.returncode == 0, 
                output=out[:8192], 
                error=None if r.returncode == 0 else f"Exit code {r.returncode}", 
                audit_action="terminal_exec"
            )
        except subprocess.TimeoutExpired:
             return ToolResult(success=False, output="", error=f"Command timed out after {timeout_seconds}s", audit_action="terminal_exec_timeout")
        except Exception as e:
             return ToolResult(success=False, output="", error=str(e), audit_action="terminal_exec_error")
