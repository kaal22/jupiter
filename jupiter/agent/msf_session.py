"""Persistent Metasploit Session (msfconsole) for Jupiter."""
import os
import time
import select
import subprocess
import threading
import re

try:
    import pty
    HAS_PTY = True
except ImportError:
    HAS_PTY = False

class MetasploitSession:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetasploitSession, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized: return
        self._initialized = True
        
        # Start quiet, no banner
        self.cmd = ["msfconsole", "-q", "-n"] 
        
        self.master_fd = None
        self.process = None
        self.buffer = []
        self.running = False
        self._lock = threading.Lock()
        
        if HAS_PTY:
            self._start_pty()
            
    def _start_pty(self):
        """Start msfconsole with PTY."""
        self.master_fd, slave_fd = pty.openpty()
        self.process = subprocess.Popen(
            self.cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            env=os.environ.copy()
        )
        os.close(slave_fd)
        self.running = True
        
        # Reader thread
        t = threading.Thread(target=self._read_loop, daemon=True)
        t.start()
        
        # Wait for initial prompt properly
        time.sleep(2)
        # Clear buffer (banner might still appear or initial loading text)
        with self._lock:
            self.buffer = []

    def _read_loop(self):
        while self.running and self.process.poll() is None:
            try:
                r, _, _ = select.select([self.master_fd], [], [], 0.1)
                if self.master_fd in r:
                    data = os.read(self.master_fd, 4096)
                    if not data: break
                    try:
                        chunk = data.decode('utf-8')
                    except UnicodeDecodeError:
                        chunk = data.decode('utf-8', errors='replace')
                    
                    with self._lock:
                        self.buffer.append(chunk)
            except (OSError, ValueError):
                break
        self.running = False

    def exec(self, command: str, timeout: int = 120) -> str:
        """Execute command in msfconsole and return output."""
        if not HAS_PTY:
            return "Metasploit integration requires PTY (Linux/Kali) and does not work on Windows."

        if not self.running:
            return "Metasploit session is not running (failed to start?)."

        with self._lock:
            self.buffer = []
            
        # Send command
        os.write(self.master_fd, (command + "\n").encode())
        
        start = time.time()
        while time.time() - start < timeout:
            time.sleep(0.5)
            with self._lock:
                full = "".join(self.buffer)
            
            # Simple heuristic for prompt return:
            # Ends with '> ' or 'msf6 >'
            lines = full.splitlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line.endswith(">") or "msf6" in last_line:
                    # We assume command finished if we see the prompt
                    # But command echo might be the first thing.
                    
                    # Remove echo of command
                    if full.strip().startswith(command):
                         # naive clean
                         pass
                    
                    return full
                
        return "".join(self.buffer) + f"\n(Timeout {timeout}s)"

    def close(self):
        self.running = False
        if self.process:
            self.process.terminate()
            if self.master_fd:
                try: os.close(self.master_fd)
                except: pass

def get_msf() -> MetasploitSession:
    return MetasploitSession()
