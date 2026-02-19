"""Persistent Shell Session for Jupiter (System-Native Agent)."""
import os
import sys
import time
import select
import subprocess
import threading
import re
from typing import Optional, List

# Check for PTY support (Linux/Mac)
try:
    import pty
    HAS_PTY = True
except ImportError:
    HAS_PTY = False

PROMPT_MARKER = "[JUPITER]>"  # Unique prompt to wait for

class ShellSession:
    """A persistent shell session (bash/zsh) that maintains state."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShellSession, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self._initialized = True
        
        self.shell_cmd = "/bin/bash"
        self.master_fd = None
        self.process = None
        self.buffer = []
        self.running = False
        self._output_thread = None
        self._lock = threading.Lock()
        
        if HAS_PTY:
            self._start_pty()
        else:
            self._start_subprocess()

    def _start_pty(self):
        """Start shell with PTY (Linux/Mac) for full interactive support."""
        self.master_fd, slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            [self.shell_cmd, "--noprofile", "--norc"], # Clean shell
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            env=os.environ.copy()
        )
        os.close(slave_fd)
        self.running = True
        
        # Start background reader
        self._output_thread = threading.Thread(target=self._read_loop_pty, daemon=True)
        self._output_thread.start()
        
        # Set prompt immediately (blind write)
        time.sleep(0.5)
        self._write(f"export PS1='{PROMPT_MARKER} '\n")
        time.sleep(0.5)
        # Clear detected output so far
        with self._lock:
            self.buffer = []

    def _start_subprocess(self):
        """Fallback for Windows (simulated persistence via one-off calls)."""
        pass

    def _read_loop_pty(self):
        """Background thread to read PTY output continuously."""
        while self.running and self.process.poll() is None:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 4096)
                    if not data: break
                    chunk = data.decode('utf-8', errors='replace')
                    with self._lock:
                        self.buffer.append(chunk)
            except (OSError, ValueError):
                break
        self.running = False

    def _write(self, text: str):
        if HAS_PTY and self.master_fd:
            os.write(self.master_fd, text.encode('utf-8'))

    def exec(self, command: str, timeout: int = 30) -> str:
        """Execute a command and return output until prompt reappears (blocking)."""
        if not HAS_PTY:
            # Windows fallback: one-off execution
            try:
                r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
                return (r.stdout or "") + (r.stderr or "")
            except subprocess.TimeoutExpired:
                 return f"Timeout after {timeout}s"

        with self._lock:
            self.buffer = [] # Clear previous output
            
        self._write(command + "\n")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            time.sleep(0.1)
            with self._lock:
                full_text = "".join(self.buffer)
                
            # Check for prompt marker
            if PROMPT_MARKER in full_text:
                # Remove the command echo and prompt
                # Often output is: "command\r\noutput\r\n[JUPITER]> "
                # We want just "output"
                clean = full_text.replace(f"{PROMPT_MARKER} ", "").strip()
                # Try to remove echoed command
                if clean.startswith(command):
                    clean = clean[len(command):].strip()
                return clean

            # Check for sudo password prompt
            # Sudo usually: "[sudo] password for user: "
            if "password for" in full_text.lower() or "password:" in full_text.lower():
                # We detected a password prompt! 
                # We return a special signal so the agent knows to ask user
                return f"INTERACTIVE_PROMPT_NEEDED: {full_text.strip()}"

        # Timeout return whatever we have
        return "".join(self.buffer).strip() + "\n(Command Timed Out)"

    def close(self):
        self.running = False
        if HAS_PTY and self.process:
            self.process.terminate()
            if self.master_fd:
                try: os.close(self.master_fd)
                except: pass

def get_shell() -> ShellSession:
    return ShellSession()
