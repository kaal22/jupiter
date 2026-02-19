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
    """Run command directly in the shell. Returns exit code."""
    try:
        # shell=True essential for pipes/redirects
        proc = subprocess.run(text, shell=True, check=False)
        return proc.returncode
    except KeyboardInterrupt:
        print("^C")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1

def repl_loop():
    print("Jupiter Native Shell (V2) - Type 'exit' to quit.")
    try:
        session = PromptSession(
            history=FileHistory(get_history_file()),
            auto_suggest=AutoSuggestFromHistory(),
            completer=PathCompleter(),
        )
    except Exception:
        session = None

    while True:
        try:
            cwd = os.getcwd().replace(os.path.expanduser("~"), "~")
            prompt_str = f"jupiter:{cwd}$ "
            
            if session:
                text = session.prompt(prompt_str)
            else:
                text = input(prompt_str)
            
            text = text.strip()
            if not text:
                continue
                
            # Explicit AI trigger
            if text.startswith("?") or text.startswith("/"):
                query = text[1:].strip()
                if query:
                    process_ai_command(session, query)
                continue

            parts = shlex.split(text)
            if not parts:
                continue

            # Builtins
            if handle_local_command(parts):
                continue
            
            # Run system command
            ret = run_system_command(text)
            
            # Auto-AI Fallback
            if ret == 127:
                print(f"Command '{parts[0]}' not found. Asking Jupiter...")
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
            if session:
                ans = session.prompt(f"Execute? [Y/n] ")
            else:
                ans = input(f"Execute? [Y/n] ")
                
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
