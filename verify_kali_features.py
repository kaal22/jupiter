"""Verification script for Jupiter V2 Exploitation Features (Kali Linux)."""
import sys
import time
import shutil
from jupiter.tools.exploit import search_exploit
from jupiter.agent.msf_session import get_msf
from jupiter.tools.msf import msf_exec

def test_searchsploit():
    print("========================================")
    print("[*] Testing SearchSploit Integration")
    print("========================================")
    
    query = "vsftpd 2.3.4"
    print(f"    Querying: '{query}'...")
    
    res = search_exploit(query)
    
    if res.success:
        print(f"[+] Success! Output Snippet:\n{res.output[:300]}\n...")
    else:
        print(f"[-] Failed: {res.error}")
        if "not found" in (res.error or ""):
            print("    (Ensure 'exploitdb' is installed: sudo apt install exploitdb)")

def test_metasploit():
    print("\n========================================")
    print("[*] Testing Metasploit Integration (PTY)")
    print("========================================")
    
    if not shutil.which("msfconsole"):
        print("[-] 'msfconsole' not found in PATH. Skipping.")
        return

    print("    Initializing persistent msfconsole (may take 10-30s)...")
    
    try:
        # 1. Start Session
        msf = get_msf()
        
        # Wait for valid state
        attempts = 0
        while not msf.buffer and attempts < 20: 
            time.sleep(1)
            attempts += 1
            sys.stdout.write(".")
            sys.stdout.flush()
        print("")

        # 2. Exec Command
        print("    Sending 'version' command...")
        res = msf_exec("version")
        
        if res.success:
            print(f"[+] Success! Output:\n{res.output}")
        else:
            print(f"[-] Failed: {res.error}")
            
        # 3. Exec 'use' (Context check)
        print("    Sending 'use exploit/unix/ftp/vsftpd_234_backdoor'...")
        res = msf_exec("use exploit/unix/ftp/vsftpd_234_backdoor")
        print(f"    Result: {res.output[:100]}...")

        # 4. Close
        print("    Closing session...")
        msf_exec("exit")
        
    except Exception as e:
        print(f"[-] Exception during MSF test: {e}")

if __name__ == "__main__":
    print("Jupiter V2 Verification (Run this on Kali)\n")
    test_searchsploit()
    test_metasploit()
    print("\n[=] Tests Completed.")
