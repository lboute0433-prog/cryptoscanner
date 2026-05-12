#!/usr/bin/env python3
import paramiko
import time
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("[CHECK] Getting full app.log (last 100 lines)...")
    stdin, stdout, stderr = ssh.exec_command("tail -100 /root/cryptoscanner/app.log")
    logs = stdout.read().decode('utf-8', errors='ignore')
    
    print("[LOGS] Full output:")
    for i, line in enumerate(logs.split('\n')[-50:]):
        print(f"  {line}")
    
    print("\n[CHECK] Looking for warmer startup...")
    if "Heatmap warmer started" in logs or "warmer started" in logs.lower():
        print("[SUCCESS] Warmer appears to have started")
    else:
        print("[WARNING] Warmer startup message not found - may not be running yet")
    
    print("\n[CHECK] Process list - looking for Python processes...")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep python")
    procs = stdout.read().decode('utf-8', errors='ignore')
    for line in procs.split('\n'):
        if 'app.py' in line or 'python' in line:
            print(f"  {line[:150]}")
    
    ssh.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
