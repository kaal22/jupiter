# Jupiter V2: Native Shell Integration Architecture

## Goal
Rebuild Jupiter as a **Shell-First AI Agent** that integrates deeply with the user's terminal session, bypassing the limitations of the current "chatbot + tool sandbox" model. Support full `sudo` access and seamless command execution on Kali Linux without virtual environment friction.

## Core Philosophy
1.  **I am the Shell**: Jupiter behaves like a shell wrapper (e.g., `zsh` plugin or standalone REPL).
2.  **State is King**: You are always in a directory, with environment variables. `cd /tmp` changes your state instantly.
3.  **Trust but Verify**: Sudo commands are proposed and executed seamlessly. Authorization is handled naturally (e.g., one-time session trust).
4.  **System Native**: Installation via system Python (`/usr/bin/python3`) or `pipx`, avoiding fragile venv activation dance.

## Architecture

### 1. The Engine: `JupiterShell`
A Python-based REPL (Read-Eval-Print Loop) using `python-prompt-toolkit`.
- **Input Handling**:
    - **Raw Commands**: `ls -la`, `cd ..`, `git status` -> Executed immediately via `subprocess.run` (inheriting stdin/stdout/stderr).
    - **Natural Language**: "Scan the network for open ports" -> Intercepted by LLM.
    - **AI Commands**: `/auto`, `/plan`, `/config`.

### 2. Execution Model
- **Interactive Mode**: Commands run in foreground. Output streams directly to terminal (no buffering issues).
- **Sudo Support**: Since we inherit stdin/stdout, `sudo` prompts for password *directly* in the terminal. No need for complex PTY wrappers or "INTERACTIVE_PROMPT_NEEDED" workaround. The user just types their password.
- **Output Capture**: For AI analysis, we use `script` or transparent PTY tapping *only* when AI needs to see output.

### 3. Installation Strategy (No Venv)
- **Target**: System-wide via `sudo pip3 install .` (as requested) or user-space `pip3 install --user .`.
- **Binary**: `jupiter` available globally on PATH.

## Implementation Steps

### Phase 1: The Shell Wrapper (MVP) (COMPLETED)
- [x] Create `jupiter/shell/repl.py` using `prompt_toolkit`.
- [x] Implement command passthrough (system commands run raw).
- [x] Implement `cd` tracking (maintain `os.getcwd()` sync).

### Phase 2: The Brain (COMPLETED)
- [x] Connect `Ollama` / LLM to handling non-system commands.
- [x] Prompt: "Translate this request to a command."
- [x] UX: User types "scan network" -> Jupiter prints `> sudo nmap -sn 192.168.1.0/24`. User hits Enter to confirm.

### Phase 3: Autonomous Agents (IN PROGRESS)
- [x] `/auto <goal>`: Spawns the agent loop.
- [ ] **Trust Mode**: `/trust` command to auto-approve all commands (sudo included) for the current session.

## Comparison to V1
| Feature | V1 (Current) | V2 (Native) |
| :--- | :--- | :--- |
| **Execution** | Tool Sandbox (subprocess) | Direct System Execution |
| **Sudo** | Fails / Needs complex handling | Native (User types password) |
| **State** | Fragile (simulated state) | Robust (Real PWD/ENV) |
| **UX** | Chat-based | Shell-based |
| **Safety** | Rigid Confirmation Loop | Natural Shell Confirmation |

## User Action Required
Approve this architecture to begin the rebuild.
