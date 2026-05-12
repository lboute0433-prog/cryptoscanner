#!/usr/bin/env python3
import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("[CHECK] Looking for app.py location...")
    stdin, stdout, stderr = ssh.exec_command("find /app /root -name app.py -type f 2>/dev/null")
    locations = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
    for loc in locations:
        if loc:
            print(f"  Found: {loc}")
    
    print("\n[CHECK] Checking /app directory structure...")
    stdin, stdout, stderr = ssh.exec_command("ls -la /app/ 2>/dev/null | head -20")
    app_files = stdout.read().decode('utf-8', errors='ignore')
    print(app_files[:500])
    
    print("\n[CHECK] Looking for recent log files...")
    stdin, stdout, stderr = ssh.exec_command("find /app -name '*.log' -type f 2>/dev/null | head -10")
    logs = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
    for log in logs:
        if log:
            print(f"  {log}")
    
    print("\n[CHECK] Current app.py in /app/app.py...")
    stdin, stdout, stderr = ssh.exec_command("head -5 /app/app.py 2>/dev/null")
    head = stdout.read().decode('utf-8', errors='ignore')
    if head:
        print(f"  OK - file exists")
        print(f"  {head[:100]}")
    else:
        print("  ERROR - file not found or empty")
    
    ssh.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
