import httpx
import json
import shutil
import subprocess
import os
from typing import Optional, Tuple
from jupiter.config import OLLAMA_BASE_URL, DEFAULT_MODEL, OLLAMA_CHAT_TIMEOUT

SYSTEM_PROMPT = """You are Jupiter Shell Assistant. 
Your goal is to translate natural language requests into precise, safe, and effective shell commands for Kali Linux.
Always prefer modern tools (nmap, ip, grep, fd, bat) over deprecated ones if possible.

RULES:
1. Output MUST be valid JSON: {"command": "...", "explanation": "..."}
2. command: The exact single-line command to run.
3. explanation: Brief reason for the command (max 10 words).
4. If the request is unsafe or unclear, set command to empty string and explain why.
5. Assume the user has sudo privileges if needed (preprint sudo).
6. Do not include markdown code blocks. Just raw JSON.
"""

def get_network_context() -> str:
    """Get active network interfaces and IPs."""
    try:
        # Try finding ip command
        ip_cmd = "ip"
        if shutil.which("ip") is None:
            if os.path.exists("/sbin/ip"): ip_cmd = "/sbin/ip"
            elif os.path.exists("/usr/sbin/ip"): ip_cmd = "/usr/sbin/ip"

        # unique list of IPs
        ips = []

        # Method 1: hostname -I (Simplest)
        try:
            res = subprocess.run(["hostname", "-I"], capture_output=True, text=True)
            if res.returncode == 0:
                for ip in res.stdout.split():
                    ips.append(f"IP: {ip}")
        except: pass

        # Method 2: ip command (More detailed)
        try:
            cmd = [ip_cmd, "-4", "-o", "addr", "show", "up"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                lines = [l.strip() for l in result.stdout.splitlines() if "lo" not in l]
                if lines: ips.extend(lines[:2])
            else:
                print(f"[DEBUG] ip cmd failed: {result.stderr}")
        except Exception as e:
            print(f"[DEBUG] ip cmd error: {e}")

        if ips:
            ctx = "\n".join(ips[:4])
            print(f"[DEBUG] Network Context:\n{ctx}")
            return ctx
            
    except Exception as e:
        print(f"[DEBUG] General Network Error: {e}")
        pass
    return "Unknown (check manually)"

def get_directory_context() -> str:
    """Get list of files in current directory to help AI infer context."""
    try:
        files = []
        with os.scandir(".") as entries:
            for entry in entries:
                if not entry.name.startswith("."):
                    kind = "DIR" if entry.is_dir() else "FILE"
                    files.append(f"{kind}: {entry.name}")
        
        # Limit to 30 files to avoid context bloat
        if len(files) > 30:
            return "\n".join(files[:30]) + "\n... (more files)"
        return "\n".join(files)
    except Exception:
        return "Unknown (check permissions)"

def suggest_command(user_text: str) -> Tuple[Optional[str], str]:
    """
    Ask LLM to translate text to a command.
    Returns: (command, explanation)
    """
    try:
        net_ctx = get_network_context()
    except: net_ctx = "Unknown"
    
    try:
        dir_ctx = get_directory_context()
    except: dir_ctx = "Unknown"
    
    # Dynamic System Prompt
    prompt = f"""{SYSTEM_PROMPT}

CONTEXT:
Working Directory: {os.getcwd()}
Files Present:
{dir_ctx}

Active Network Interfaces:
{net_ctx}

Use this context to infer correct filenames (e.g. if user says 'run install', check if 'install.sh' exists).
"""

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_text}
    ]
    
    try:
        with httpx.Client(timeout=OLLAMA_CHAT_TIMEOUT) as client:
            resp = client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": DEFAULT_MODEL,
                    "messages": messages,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.2}
                }
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "{}")
            
            try:
                parsed = json.loads(content)
                cmd = parsed.get("command", "").strip()
                expl = parsed.get("explanation", "").strip()
                return (cmd if cmd else None, expl)
            except json.JSONDecodeError:
                return (None, "Failed to parse AI response.")
                
    except Exception as e:
        return (None, f"AI Error: {e}")

def is_valid_command(cmd_plugin: str) -> bool:
    """Check if the first word of the command exists in PATH or is a builtin."""
    first_word = cmd_plugin.split()[0]
    if first_word in ["cd", "exit", "history", "help", "clear"]:
        return True
    return shutil.which(first_word) is not None
