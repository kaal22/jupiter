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

## Phase 3: Autonomy Loop (IN PROGRESS)
- [x] Implement `/auto <goal>` loop.
- [ ] Implement `/trust` command to bypass confirmation for one session.
- [ ] Implement deep context gathering: `ls` output fed back to LLM automatically.

## Phase 4: Full System Integration (Kali) (COMPLETED)
- [x] Install as `/usr/local/bin/jupiter`.
- [x] Verify `sudo` behavior (password prompt works naturally).

## Phase 5: Advanced Capabilities (NEXT)
- [ ] Implement Exploitation Module (Metasploit integration?)
- [ ] Implement Web Interface Dashboard.
- [ ] Persistent Memory across sessions (vector store).
