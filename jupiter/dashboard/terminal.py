import os
import sys
import asyncio
import platform
import struct
from fastapi import WebSocket, WebSocketDisconnect

# Check OS
IS_WINDOWS = platform.system() == "Windows"

if not IS_WINDOWS:
    import pty
    import fcntl
    import termios

class TerminalManager:
    """Manages WebSocket-based PTY sessions for the dashboard."""
    
    async def handle_websocket(self, websocket: WebSocket):
        await websocket.accept()
        
        if IS_WINDOWS:
            await websocket.send_text("Terminal streaming requires Linux/macOS.\r\n")
            await websocket.close()
            return

        # Fork PTY
        # pid=0 -> child (bash), pid>0 -> parent (server)
        pid, fd = pty.fork()
        
        if pid == 0:
            # CHILD PROCESS
            # Set TERM so tools know how to render colors
            os.environ["TERM"] = "xterm-256color"
            os.environ["JUPITER_SHELL"] = "dashboard"
            
            # Execute bash with auto-launch of Jupiter
            # -l: Login shell (loads PATH)
            # -c: Run command and then drop to shell
            cmd = ["/bin/bash", "-l", "-c", "echo '[JUPITER] Establishing Neural Link...'; jupiter shell; exec bash"]
            try:
                os.execvp(cmd[0], cmd)
            except Exception as e:
                print(f"Failed to start bash: {e}")
                sys.exit(1)
        else:
            # PARENT PROCESS (FastAPI)
            loop = asyncio.get_running_loop()
            
            # 1. Read from PTY -> Send to WebSocket
            def read_from_pty():
                try:
                    data = os.read(fd, 4096)
                    if data:
                        # Use ensure_future to call async send from sync callback
                        asyncio.ensure_future(websocket.send_text(data.decode(errors="ignore")))
                    else:
                        # EOF (shell exited)
                        loop.remove_reader(fd)
                        asyncio.ensure_future(websocket.close())
                except OSError:
                    loop.remove_reader(fd)
                except Exception:
                    pass

            loop.add_reader(fd, read_from_pty)

            # 2. Read from WebSocket -> Write to PTY
            try:
                while True:
                    text = await websocket.receive_text()
                    
                    # Handle resize events: "__RESIZE__:rows:cols"
                    if text.startswith("__RESIZE__:"):
                        try:
                            _, rows, cols = text.split(":")
                            winsize = struct.pack("HHHH", int(rows), int(cols), 0, 0)
                            fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)
                        except Exception:
                            pass
                        continue
                        
                    # Standard input
                    os.write(fd, text.encode())
            except WebSocketDisconnect:
                pass
            finally:
                # Cleanup
                if fd:
                    try:
                        loop.remove_reader(fd)
                        os.close(fd)
                    except:
                        pass
                try:
                    os.kill(pid, 9)
                    os.waitpid(pid, 0) 
                except:
                    pass
