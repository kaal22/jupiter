"""Jupiter CLI — jupiter command."""
import sys
import click
import httpx
from jupiter import __version__
from jupiter.config import API_HOST, API_PORT, ensure_dirs

JUPITER_API_URL = f"http://{API_HOST}:{API_PORT}"


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__)
def cli(ctx):
    """Jupiter OS — local AI assistant. Just run 'jupiter' and ask anything.
    You can say 'what's my system status?', 'show audit log', or chat. No need to remember commands."""
    ensure_dirs()
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)


@cli.command()
@click.option("--api-url", default=JUPITER_API_URL, envvar="JUPITER_API_URL")
def chat(api_url: str):
    """Start Jupiter and ask in plain language (default when you run 'jupiter')."""
    try:
        r = httpx.get(f"{api_url.rstrip('/')}/health", timeout=2.0)
        if r.status_code == 200:
            _chat_via_api(api_url)
            return
    except Exception:
        pass
    _chat_local()

def _chat_via_api(api_url: str):
    url = f"{api_url.rstrip('/')}/chat"
    click.echo("Jupiter — ask anything (e.g. 'what's my system status?', 'list files here', 'show audit log'). Type your question and Enter. Ctrl+D or 'exit' to quit.")
    while True:
        try:
            line = click.prompt("You", default="", show_default=False)
        except (EOFError, click.Abort):
            break
        if not line or line.strip().lower() in ("exit", "quit", "q"):
            break
        try:
            r = httpx.post(url, json={"message": line.strip()}, timeout=60.0)
            r.raise_for_status()
            click.echo("Jupiter: " + r.json().get("reply", ""))
        except Exception as e:
            click.echo(f"Error: {e}", err=True)

def _chat_local():
    from jupiter.agent.daemon import run_daemon_loop, execute_plan
    from jupiter.agent.planner import JupiterPlanner
    from jupiter.safety.broker import SafetyBroker
    from jupiter.storage.memory import MemoryStore
    from jupiter.storage.audit import AuditStore
    click.echo("Jupiter — ask anything (e.g. 'what's my system status?', 'list files here', 'show audit log'). Type your question and Enter. Ctrl+D or 'exit' to quit.")
    memory = MemoryStore()
    audit = AuditStore()
    broker = SafetyBroker(audit=audit)
    planner = JupiterPlanner(memory=memory)
    while True:
        try:
            line = click.prompt("You", default="", show_default=False)
        except (EOFError, click.Abort):
            break
        if not line or line.strip().lower() in ("exit", "quit", "q"):
            break
        user_message = line.strip()
        memory.session_append("user", user_message)
        plan = planner.plan(user_message)
        output = execute_plan(plan, broker, memory)
        memory.session_append("assistant", output)
        click.echo("Jupiter: " + output)

@cli.command()
@click.option("--api-url", default=JUPITER_API_URL)
@click.option("--limit", default=20)
def audit(api_url: str, limit: int):
    """Show recent audit log entries."""
    try:
        r = httpx.get(f"{api_url.rstrip('/')}/audit", params={"limit": limit}, timeout=5.0)
        r.raise_for_status()
        for e in r.json().get("entries", []):
            click.echo(f"  {e.get('created_at')} | {e.get('action')} | {e.get('scope')} | {e.get('outcome')}")
    except Exception as e:
        click.echo(f"Error: {e}. Is the API running? Try: python -m jupiter.api.main", err=True)

@cli.command()
def status():
    """Show Jupiter config and health."""
    from jupiter.config import JUPITER_DATA, JUPITER_CONFIG, OLLAMA_BASE_URL, DB_PATH
    ensure_dirs()
    click.echo("Jupiter OS")
    click.echo(f"  Data:   {JUPITER_DATA}")
    click.echo(f"  Config: {JUPITER_CONFIG}")
    click.echo(f"  DB:     {DB_PATH}")
    click.echo(f"  Ollama: {OLLAMA_BASE_URL}")
    try:
        r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3.0)
        if r.status_code == 200:
            tags = r.json().get("models", [])
            click.echo(f"  Models: {[m.get('name') for m in tags]}")
        else:
            click.echo("  Models: (Ollama not reachable)")
    except Exception:
        click.echo("  Models: (Ollama not reachable)")

def main():
    cli()

if __name__ == "__main__":
    main()
