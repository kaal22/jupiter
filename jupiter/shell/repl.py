"""Jupiter Native Shell REPL (V2 Architecture)."""
import os
import sys
import shlex
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import PathCompleter
from jupiter.config import JUPITER_DATA, ensure_dirs, OLLAMA_BASE_URL, DEFAULT_MODEL
from jupiter.agent.shell import ShellSession

# Agent Imports for /auto
from jupiter.agent.daemon import agent_loop, MAX_AGENT_STEPS
from jupiter.agent.planner import JupiterPlanner
from jupiter.safety.broker import SafetyBroker
from jupiter.storage.memory import MemoryStore
from jupiter.storage.audit import AuditStore

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

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

def print_welcome():
    """Display welcome screen with commands."""
    try:
        console = Console()
        
        # Commands Table
        table = Table(box=box.SIMPLE, show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Command", style="cyan", width=20)
        table.add_column("Description", style="white")
        table.add_column("Example", style="dim italic")

        table.add_row("/auto <goal>", "Autonomous Task Agent", "Scan 192.168.1.5 and find bugs")
        table.add_row("/trust", "Toggle Trust Mode", "Skip confirmations for this session")
        table.add_row("network_scan", "Nmap Scanner", "network_scan('10.0.0.5')")
        table.add_row("exploit_search", "SearchSploit", "exploit_search('vsftpd 2.3.4')")
        table.add_row("msf_exec", "Metasploit Console", "msf_exec('use exploit/...')")
        table.add_row("?", "AI Assistance", "? How do I scan port 80?")
        table.add_row("exit", "Quit Shell", "")

        panel = Panel(
            table,
            title="[bold cyan]Jupiter AI v2[/bold cyan] [green](Kali Edition)[/green]",
            subtitle="[dim]Autonomous Penetration Testing Environment[/dim]",
            border_style="blue",
            padding=(1, 2),
        )
        console.print(panel)
        console.print("[dim]Type natural language or commands below.[/dim]\n")
    except ImportError:
        print("Jupiter Native Shell (V2) - Type 'exit' to quit.")
    except Exception as e:
        print(f"Welcome screen error: {e}")

def repl_loop():
    print_welcome()
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
                # Handle /trust command
                if text.strip() == "/trust":
                    if session:
                        val = not getattr(session, "trust_mode", False)
                        setattr(session, "trust_mode", val)
                        print(f"Trust Mode: {'ENABLED (No confirmations)' if val else 'DISABLED'}")
                    else:
                        print("Trust mode not available in basic shell mode.")
                    continue
                
                # Handle /auto
                if text.startswith("/auto"):
                    goal = text[5:].strip()
                    if goal:
                        output = process_auto_command(session, goal)
                        print("\n[AGENT REPORT]\n" + output)
                    else:
                        print("Usage: /auto <goal>")
                    continue
                
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
    
    # Cleanup on exit
    if ShellSession._instance:
        ShellSession._instance.close()

def process_auto_command(session, goal: str) -> str:
    print(f"Starting Multi-Step Agent for goal: '{goal}'")
    
    is_trusted = getattr(session, "trust_mode", False) if session else False
    if is_trusted:
        print("[Trust Mode ENABLED] bypassing confirmations.")

    # Initialize Agent components
    memory = MemoryStore()
    audit = AuditStore()
    broker = SafetyBroker(audit=audit)
    planner = JupiterPlanner(
        base_url=OLLAMA_BASE_URL,
        model=memory.preference_get("model") or DEFAULT_MODEL, 
        memory=memory
    )

    def shell_confirm(msg: str) -> bool:
        if getattr(session, "trust_mode", False) if session else False:
            print(f"[Auto-Confirm] {msg} -> YES")
            return True
            
        if session:
            ans = session.prompt(f"\n[CONFIRM] {msg} (y/n): ")
        else:
            ans = input(f"\n[CONFIRM] {msg} (y/n): ")
        return ans.strip().lower().startswith('y')

    try:
        return agent_loop(
            user_message=goal,
            planner=planner,
            broker=broker,
            memory=memory,
            confirm_callback=shell_confirm,
            max_steps=MAX_AGENT_STEPS,
            on_tool_start=lambda s, t, a: print(f">> step {s}: {t} {a}"),
            on_tool_result=lambda s, t, r: None # don't print result, agent_loop summarizes
        )
    except Exception as e:
        return f"Agent Error: {e}"

def process_ai_command(session, query):
    from jupiter.shell.intelligence import suggest_command
    
    print(f"Thinking about '{query}'...")
    cmd, explanation = suggest_command(query)
    
    if cmd:
        print(f"\n> Suggested: {cmd}")
        print(f"  Reason: {explanation}")
        
        try:
            if getattr(session, "trust_mode", False) if session else False:
                print("[Auto-Confirm] Executing...")
                run_system_command(cmd)
                return

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
