"""Jupiter CLI — jupiter command."""
import sys
import click
import httpx
from jupiter import __version__
from jupiter.config import API_HOST, API_PORT, OLLAMA_CHAT_TIMEOUT, ensure_dirs

JUPITER_API_URL = f"http://{API_HOST}:{API_PORT}"


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version=__version__)
def cli(ctx):
    """Jupiter OS — local AI agent. Just run 'jupiter' and tell it what to do."""
    ensure_dirs()
    if ctx.invoked_subcommand is None:
        ctx.invoke(chat)


@cli.command()
@click.option("--api-url", default=JUPITER_API_URL, envvar="JUPITER_API_URL")
def chat(api_url: str):
    """Start Jupiter interactive chat (default)."""
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
    click.echo("Jupiter ready. Tell me what to do. (Ctrl+D or 'exit' to quit)")
    while True:
        try:
            line = click.prompt("You", default="", show_default=False)
        except (EOFError, click.Abort):
            break
        if not line or line.strip().lower() in ("exit", "quit", "q"):
            break
        try:
            click.echo("  [working...]")
            r = httpx.post(url, json={"message": line.strip()}, timeout=OLLAMA_CHAT_TIMEOUT)
            r.raise_for_status()
            click.echo("Jupiter: " + r.json().get("reply", ""))
        except Exception as e:
            click.echo(f"Error: {e}", err=True)


def _chat_local():
    from jupiter.agent.daemon import agent_loop
    from jupiter.agent.planner import JupiterPlanner
    from jupiter.safety.broker import SafetyBroker
    from jupiter.storage.memory import MemoryStore
    from jupiter.storage.audit import AuditStore
    click.echo("Jupiter ready. Tell me what to do. (Ctrl+D or 'exit' to quit)")
    memory = MemoryStore()
    audit = AuditStore()
    broker = SafetyBroker(audit=audit)
    planner = JupiterPlanner(memory=memory)

    def on_thinking(step, num_obs):
        if step == 1:
            click.echo("  [thinking...]")
        else:
            click.echo("  [analyzing step " + str(step) + "...]")

    def on_tool_start(step, tool, args):
        cmd = args.get("command", "") if isinstance(args, dict) else ""
        if cmd:
            click.echo(f"  >> step {step}: running: {cmd}")
        else:
            click.echo(f"  >> step {step}: {tool}")

    while True:
        try:
            line = click.prompt("You", default="", show_default=False)
        except (EOFError, click.Abort):
            break
        if not line or line.strip().lower() in ("exit", "quit", "q"):
            break
        output = agent_loop(
            line.strip(), planner, broker, memory,
            on_tool_start=on_tool_start,
            on_thinking=on_thinking,
        )
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
        click.echo(f"Error: {e}. Is the API running?", err=True)


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
