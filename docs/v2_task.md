# Jupiter V2: Native Shell Task Plan

## Phase 1: Native Shell Core (COMPLETED)
- [x] Create `jupiter/shell/repl.py` using `prompt_toolkit`.
- [x] Implement `cd` tracking (maintain `os.getcwd()` state).
- [x] Implement `subprocess.run` passthrough for raw commands.
- [x] Setup `setup.py` for system-wide `pip install .` (no venv).

## Phase 2: Intelligence Layer (COMPLETED)
- [x] Connect `Ollama` client.
- [x] Implement `handle_natural_input(text)` -> LLM -> Proposed Command.
- [x] Implement user confirmation: `jupiter> sudo nmap ... [Y/n]`.
- [x] Auto-detect missing commands (exit 127) and invoke AI.
- [x] Inject Network Context (`ip`, `hostname`) for accurate scanning.

## Phase 3: Autonomy Loop (COMPLETED)
- [x] Implement `/auto <goal>` loop.
- [x] Implement `/trust` command to bypass confirmation for one session.
- [x] Implement deep context gathering: `ls` output fed back to LLM automatically.

## Phase 4: Full System Integration (Kali) (COMPLETED)
- [x] Install as `/usr/local/bin/jupiter`.
- [x] Verify `sudo` behavior (password prompt works naturally).

## Phase 5: Advanced Capabilities (IN PROGRESS)
- [x] Scaffold `jupiter/exploitation/` module structure.
- [x] Implement basic exploit searching (e.g. `searchsploit` wrapper).
- [x] Implement Metasploit Integration (via persistent `msfconsole` PTY wrapper).
- [x] Auto-suggest exploits based on Nmap service versions (via `network_scan` and prompt strategy).
- [ ] Implement Web Interface Dashboard.
- [ ] Persistent Memory across sessions (vector store).
