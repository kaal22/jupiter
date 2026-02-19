# Phase 5 Verification Guide

## Prerequisites (Kali Linux)
Ensure you have the following tools installed:
```bash
sudo apt update
sudo apt install exploitdb metasploit-framework
sudo apt install python3-pip python3-venv
```

## Running Verification Script
We have provided a script `verify_kali_features.py` to automate testing of the new modules.

1.  **Pull latest changes**:
    ```bash
    git pull origin main
    ```

2.  **Install dependencies**:
    ```bash
    pip install . --break-system-packages
    # Or simple: pip install -r requirements.txt
    ```

3.  **Run the script**:
    ```bash
    python3 verify_kali_features.py
    ```

## Expected Output
-   `[*] Testing SearchSploit Integration`: Should find "vsftpd 2.3.4 Backdoor".
-   `[*] Testing Metasploit Integration`: Should launch `msfconsole`, wait for prompt, and print version info.

## Manual Testing via Shell
Start Jupiter:
```bash
jupiter shell
```

Try these commands:
1.  `/auto Scan for exploits related to vsftpd 2.3.4`
    -   Should trigger `exploit_search`.
2.  `/auto Launch Metasploit and use exploit/unix/ftp/vsftpd_234_backdoor`
    -   Should trigger `msf_exec`.

3.  `/auto Scan 127.0.0.1 and find runnable exploits`
    -   Should trigger `network_scan`.
    -   Should use `msf_exec("search ...")` to find available Metasploit modules.
    -   Should attempt exploit if safe/mocked.

