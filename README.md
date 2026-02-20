# Jupiter OS — Local AI Agent & Native Shell

**Jupiter** is a local-first AI companion that lives in your terminal. It acts as an intelligent layer over your shell, helping you execute commands, automate tasks, and manage your system without leaving the command line.

> **Privacy First:** All AI inference and memory stay 100% on your machine (via Ollama). No data leaves your localhost.

## Quick Start (Kali Linux / Debian)

The recommended install for Kali uses `pipx` to avoid conflicts with system packages.

```bash
# 1. Get the Code
git clone https://github.com/kaal22/jupiter.git ~/.local/share/jupiter
cd ~/.local/share/jupiter
git pull origin main

# 2. Install dependencies (Kali)
sudo apt update && sudo apt install -y pipx python3-venv nmap curl build-essential python3-dev
pipx ensurepath
source ~/.bashrc  # Refresh PATH

# 3. Install Ollama (Required AI Backend)
command -v ollama >/dev/null 2>&1 || { curl -fsSL https://ollama.com/install.sh | sh; }
ollama pull llama3.2:3b

# 4. Install Jupiter (Isolated)
pipx install . --force
```

## Features

### 0. Real-time Dashboard (New!)

Monitor your operations via a futuristic web interface.

```bash
jupiter dashboard
```
- **Live Terminal:** Full interactive shell in your browser with auto-AI launch.
- **Activity Feed:** Watch exploits and commands execute in real-time.
- **Target List:** Automatically tracks discovered hosts from Nmap scans.
- **Access:** http://127.0.0.1:8000

### 1. Native Intelligent Shell (V2)

Jupiter replaces your standard shell with an AI-enhanced one.

```bash
jupiter shell
```

- **Natural Language Commands:** Don't know the flag for `nmap`? Just ask.
  ```bash
  jupiter:~$ scan my network
  > Suggested: sudo nmap -sP 192.168.50.0/24
  ```
- **Context Aware:** It knows your IP, OS, and checks if commands exist before running them.
- **Auto-Correction:** If you type a command that doesn't exist, Jupiter wakes up and suggests the correct one.

### 2. Autonomous Mode (`/auto`)

Need to do more than one thing? Trigger the autonomous agent directly from the shell.

```bash
jupiter:~$ /auto scan 192.168.50.15 and find open ports, then analyze the results
```

Jupiter will:
1. Run the scan.
2. Read the output.
3. Decide the next step (e.g., specific service scan).
4. Report the findings.

### 3. Trust Mode (`/trust`)

Tired of confirming every command? Enable **Trust Mode** for the current session.

```bash
jupiter:~$ /trust
> Trust Mode: ENABLED (No confirmations)
```

Now, `jupiter` (and `/auto`) will execute commands immediately without asking. Use with caution!

### 4. Deep Context Awareness

Jupiter now sees what you see:
- **Files**: It knows which files are in your current directory.
- **Network**: It knows your IP/Subnet.

Example: If you have a `requirements.txt` in your folder:
```bash
jupiter:~$ install the python deps
> Suggested: pip install -r requirements.txt
```

### 5. Classic Agent Mode

You can also run valid one-off tasks from your standard terminal:

```bash
jupiter "check system status and tail the last 20 auth logs"
```

## Update

To update to the latest version:

```bash
cd ~/.local/share/jupiter
git pull
pipx install . --force
```

## Architecture

- **Core:** Python 3.10+
- **Shell:** `prompt_toolkit` with custom REPL.
- **AI:** `Ollama` (local LLM).
- **Memory:** SQLite (under `~/.local/share/jupiter`).
- **Safety:** Built-in "Safety Broker" requires confirmation for destructive commands.

## License

MIT License.
