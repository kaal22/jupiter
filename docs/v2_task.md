# Jupiter V2: Native Shell Task Plan

## Phase 1: Native Shell Core (Immediate)
- [ ] Create `jupiter/shell/repl.py` using `prompt_toolkit`.
- [ ] Implement `cd` tracking (maintain `os.getcwd()` state).
- [ ] Implement `subprocess.run` passthrough for raw commands.
- [ ] Setup `setup.py` for system-wide `pip install .` (no venv).

## Phase 2: Intelligence Layer
- [ ] Connect `Ollama` client.
- [ ] Implement `handle_natural_input(text)` -> LLM -> Proposed Command.
- [ ] Implement user confirmation: `jupiter> sudo nmap ... [Y/n]`.

## Phase 3: Autonomy Loop
- [ ] Implement `/auto <goal>` loop.
- [ ] Implement `/trust` command to bypass confirmation for one session.
- [ ] Implement context gathering: `ls` output fed back to LLM automatically.

## Phase 4: Full System Integration (Kali)
- [ ] Install as `/usr/local/bin/jupiter`.
- [ ] Verify `sudo` behavior (password prompt works naturally).
