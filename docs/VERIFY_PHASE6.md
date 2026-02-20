# Verify Phase 6: Real-time Dashboard

This document outlines the steps to verify the Jupiter Dashboard functionality on a fresh Kali Linux install.

## 1. Installation Check

Ensure the clean installation was successful via `pipx`.

```bash
# Check version / command availability
jupiter --version
# Should output: Jupiter V2 ...
```

## 2. Launch Dashboard

Start the web server.

```bash
jupiter dashboard
```

- Open browser to: `http://127.0.0.1:8000`
- Confirm "Secure Link Established" message in the terminal.

## 3. Verify Terminal Auto-Launch

1. Look at the central terminal window in the dashboard.
2. It should NOT be a plain `bash` prompt.
3. It SHOULD show the Jupiter banner: `[JUPITER] Establishing Neural Link...`
4. The prompt should be `jupiter:~$` (or similar depending on theme/prompt settings).
5. Type `help` to verify you are inside the Jupiter AI shell.

## 4. Verify Activity Feed

1. Keep the dashboard open.
2. In the dashboard terminal, run a command:
   ```bash
   scan localhost
   ```
3. Look at the **Activity Log** panel on the right.
4. A new entry should appear (e.g., `SCAN` or `COMMAND`).
5. If the command fails or succeeds, the border color might change (Green/Red).

## 5. Verify Target Detection

1. Run an actual Nmap scan from the dashboard terminal (or another terminal):
   ```bash
   nmap -p 80 localhost
   ```
   *Note: Using system `nmap` directly.*
2. Wait a few seconds (the dashboard polls every 5s).
3. The **Targets Detected** panel on the left should update to show `localhost` (or `127.0.0.1`).

## 6. Remote Access (Optional)

If running on a headless VM:
```bash
jupiter dashboard --host 0.0.0.0
```
Access via `http://<VM_IP>:8000`.

---
**Status:** Phase 6 functionality is COMPLETE.
