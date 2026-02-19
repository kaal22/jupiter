"""Jupiter Native Shell REPL (V2 Architecture)."""
import os
import sys
import shlex
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import PathCompleter
from jupiter.config import JUPITER_DATA, ensure_dirs

def get_history_file():
    ensure_dirs()
    return os.path.join(JUPITER_DATA, "history.txt")

def handle_local_command(cmd_parts):
    cmd = cmd_parts[0]
    args = cmd_parts[1:]
    
    if cmd == "cd":
        try:
            target = args[0] if args else os.path.expanduser("~")
            os.chdir(target)
        except Exception as e:
            print(f"cd: {e}")
        return True
    
    if cmd == "exit":
        sys.exit(0)
        
    return False

def run_system_command(text):
    """Run command directly in the shell with full TTY support."""
    try:
        # Use shell=True for complex commands (pipes, etc)?
        # But shell=True spawns sh -c "...", which might mess up TTY?
        # Better: use shell=False and split args if simple.
        # BUT user might type "ls | grep foo".
        # So shell=True is needed for | and >.
        # On Linux/Kali, shell=True runs /bin/sh.
        subprocess.run(text, shell=True, check=False)
    except KeyboardInterrupt:
        print("^C")
    except Exception as e:
        print(f"Error: {e}")

def repl_loop():
    print("Jupiter Native Shell (V2) - Type 'exit' to quit.")
    session = PromptSession(
        history=FileHistory(get_history_file()),
        auto_suggest=AutoSuggestFromHistory(),
        completer=PathCompleter(),
    )

    while True:
        try:
            # Dynamic prompt
            cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
            text = session.prompt(f"jupiter:{cwd}$ ")
            
            if not text.strip():
                continue
                
            # Check for explicit AI command
            if text.startswith("?") or text.startswith("/"):
                query = text[1:].strip()
                if query:
                    process_ai_command(session, query)
                continue

            # Handle built-ins
            parts = shlex.split(text)
            if handle_local_command(parts):
                continue
            
            # Check if command exists
            from jupiter.shell.intelligence import is_valid_command
            if is_valid_command(parts[0]):
                # It's a real command (or we think so)
                run_system_command(text)
            else:
                # likely natural language
                process_ai_command(session, text)

        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception as e:
            print(f"Shell Error: {e}")

def process_ai_command(session, query):
    from jupiter.shell.intelligence import suggest_command
    
    print(f"Thinking about '{query}'...")
    cmd, explanation = suggest_command(query)
    
    if cmd:
        print(f"\n> Suggested: {cmd}")
        print(f"  Reason: {explanation}")
        
        try:
            ans = session.prompt(f"Execute? [Y/n] ")
            if ans.lower() in ('', 'y', 'yes'):
                run_system_command(cmd)
            else:
                print("Cancelled.")
        except KeyboardInterrupt:
            print("Cancelled.")
    else:
        print(f"AI could not suggest a command. {explanation}")



if __name__ == "__main__":
    repl_loop()
