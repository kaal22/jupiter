# Jupiter OS — Local Agentic Desktop Copilot (Phase 1)

Privacy-centric, local-first AI companion for Ubuntu Desktop. All inference and memory stay **on your machine**.

## All-in-one install (Ubuntu Desktop)

**Prerequisite:** Install `curl` if needed (required to download the installer):

```bash
sudo apt install curl
```

**One-line install (new user, fresh Ubuntu):**

```bash
curl -sSL https://raw.githubusercontent.com/kaal22/jupiter/main/install.sh | bash
```

If you see `git: command not found`, your shell may have an old cached script. Run with cache-bust:  
`curl -sSL "https://raw.githubusercontent.com/kaal22/jupiter/main/install.sh?t=$(date +%s)" | bash`

This downloads `install.sh` from the repo and clones [github.com/kaal22/jupiter](https://github.com/kaal22/jupiter) to install everything (deps, Ollama, model, Jupiter, systemd).

**From repo (if they already cloned):**

```bash
git clone https://github.com/kaal22/jupiter.git
cd jupiter
./install.sh
```

(Or set `JUPITER_INSTALL_SRC=/path/to/Jupiter` if the repo is already on disk.)

The installer will:

1. Install system dependencies (python3-venv, python3-pip, curl)
2. Install **Ollama** (local LLM runtime)
3. Create a virtualenv and install **Jupiter** from the repo
4. Detect hardware (GPU VRAM) and **pull the right Ollama model** (e.g. llama3.2:3b or 7b)
5. Initialize Jupiter data and DB
6. Install systemd user services (first-boot, agent)
7. Symlink `jupiter` to `~/.local/bin`

**After install**

- Run once (or open a new terminal): **`source ~/.bashrc`** — then run **`jupiter`**.
- Just run **`jupiter`** and ask in plain language. Examples: “what’s my system status?”, “list files in this folder”, “show recent audit log”. The AI figures out what to do; no need to remember subcommands.
- Optional: `jupiter status` (config/health), `jupiter audit` (audit log).

If you see **`jupiter: command not found`**, run `source ~/.bashrc` or open a new terminal.

If you see **`ModuleNotFoundError: No module named 'jupiter'`** (after an older install), the editable install pointed at a removed temp dir. Fix it by reinstalling from the permanent copy:
```bash
~/.local/share/jupiter/venv/bin/pip install -e ~/.local/share/jupiter-install
```
Then run `jupiter` again.

## Manual / development

```bash
cd Jupiter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .
jupiter status
jupiter
```

## Architecture

- **Welcome Wizard** — One-time GUI (optional)
- **Local API** — localhost-only HTTP API
- **Jupiter Agent** — Planner + executor (Ollama + tools)
- **Tool Safety Broker** — Permissions, confirmations, audit
- **Memory & Audit** — SQLite (local only)
- **Base** — Ubuntu Desktop 24.04+ (GNOME, systemd)

## Context, memory, and capabilities

**Local database:** All memory is stored in SQLite under `~/.local/share/jupiter/` (no cloud).

- **Session** — Current conversation; recent messages are sent to the model so it keeps context.
- **Episodic** — Summaries/facts you ask Jupiter to remember (e.g. “remember that I use vim”); these are included in future context.
- **Preferences** — Stored key/value (e.g. editor, theme); included in context so the AI knows your preferences.

**How the AI learns:** When you say “remember that …” or “save that”, Jupiter can store a preference (`remember_preference`) or a short summary (`remember_summary`). It only stores when you ask; nothing is remembered without consent.

**System awareness:** The AI is given the host OS, hostname, and machine type so it suggests correct commands (e.g. `apt` on Ubuntu, `dnf` on Fedora). It runs as your user (no sudo).

**Executing commands and reading output:** Jupiter can run shell commands and return their stdout/stderr via the `terminal_exec` tool. For read-only commands (e.g. `ls`, `cat`, `grep`) it can run them directly; for commands that change state it asks for confirmation first. All tool use is logged in the local audit store.

## Requirements

- Ubuntu Desktop 24.04+ (or Debian-based)
- Python 3.10+
- Ollama (installed by the installer)
- Optional: NVIDIA/AMD GPU for faster inference

## License & trademark

"Jupiter OS" — verify trademark before commercial use.
