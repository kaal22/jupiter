# Jupiter OS — Local AI Agent & Native Shell

**Jupiter** is a local-first AI companion that lives in your terminal. It acts as an intelligent layer over your shell, helping you execute commands, automate tasks, and manage your system without leaving the command line.

> **Privacy First:** All AI inference and memory stay 100% on your machine (via Ollama). No data leaves your localhost.

## Quick Start (Kali Linux / Debian)

The recommended install for Kali Linux uses system packages for maximum integration.

```bash
# 1. Clone the repo
git clone https://github.com/kaal22/jupiter.git ~/.local/share/jupiter-install
cd ~/.local/share/jupiter-install

# 2. Run the V2 installer
chmod +x install_v2_kali.sh
sudo ./install_v2_kali.sh
```

This will:
- Install system dependencies (`python3-prompt-toolkit`, `nmap`, etc).
- Install **Ollama** and pull the `llama3.2:3b` model.
- Install the `jupiter` command globally.

## Features

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
cd ~/.local/share/jupiter-install
git pull
sudo pip install . --break-system-packages
```

## Architecture

- **Core:** Python 3.10+
- **Shell:** `prompt_toolkit` with custom REPL.
- **AI:** `Ollama` (local LLM).
- **Memory:** SQLite (under `~/.local/share/jupiter`).
- **Safety:** Built-in "Safety Broker" requires confirmation for destructive commands.

## License

MIT License.
