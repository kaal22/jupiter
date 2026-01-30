"""System tools — status, logs, diagnostics."""
import platform
import subprocess
from typing import Optional
from jupiter.safety.broker import ToolResult


def system_status() -> ToolResult:
    try:
        uname = platform.uname()
        out = f"System: {uname.system} {uname.release} ({uname.machine})\nNode: {uname.node}"
        try:
            with open("/proc/meminfo") as f:
                out += "\n" + " ".join(f.read().splitlines()[:3])
        except FileNotFoundError:
            pass
        return ToolResult(success=True, output=out)
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def system_logs_tail(service: Optional[str] = None, lines: int = 20) -> ToolResult:
    try:
        cmd = ["journalctl", "-n", str(lines), "--no-pager"]
        if service:
            cmd = ["journalctl", "-u", service, "-n", str(lines), "--no-pager"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return ToolResult(success=r.returncode == 0, output=(r.stdout or r.stderr or "")[:4096])
    except FileNotFoundError:
        return ToolResult(success=False, output="", error="journalctl not available")
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def system_diagnostics() -> ToolResult:
    try:
        parts = []
        try:
            with open("/proc/loadavg") as f:
                parts.append("Load: " + f.read().strip())
        except FileNotFoundError:
            pass
        r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            parts.append("Disk:\n" + r.stdout)
        return ToolResult(success=True, output="\n".join(parts))
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))
