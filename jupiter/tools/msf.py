"""Metasploit tools interacting with persistent session."""
from jupiter.agent.msf_session import get_msf
from jupiter.safety.broker import ToolResult

def msf_exec(command: str) -> ToolResult:
    """Execute Metasploit commands (use, set, run, jobs, show options)."""
    cmd = command.strip()
    if not cmd:
         return ToolResult(success=False, output="Empty command", audit_action="msf_empty")

    if cmd == "exit":
        try:
            get_msf().close()
        except:
            pass
        return ToolResult(success=True, output="Metasploit session closed.", audit_action="msf_close")
        
    try:
        output = get_msf().exec(cmd)
        
        # Clean up output slightly if needed (remove large banners)
        # But msfconsole -q handles most.
        
        return ToolResult(
            success=True, 
            output=output, 
            audit_action="msf_exec"
        )
    except Exception as e:
        return ToolResult(success=False, output="", error=f"MSF Error: {str(e)}", audit_action="msf_error")
