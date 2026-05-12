#!/usr/bin/env python3
"""Deploy RSI warmer fix to /app directory where gunicorn is actually running"""
import paramiko
import os
import time
import sys

try:
    print("[DEPLOY] Connecting to Hetzner...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    print("[DEPLOY] Connected!")
    
    files_to_deploy = [
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/app/app.py"),
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\rsi_engine.py", "/app/rsi_engine.py"),
    ]
    
    print("\n[DEPLOY] Uploading fixed files to /app...")
    sftp = ssh.open_sftp()
    for local, remote in files_to_deploy:
        if os.path.exists(local):
            print(f"  Uploading to {remote}...")
            sftp.put(local, remote)
        else:
            print(f"  WARNING: {local} not found")
    sftp.close()
    
    print("\n[DEPLOY] Restarting gunicorn service...")
    ssh.exec_command("systemctl restart cryptoscanner")
    time.sleep(10)
    
    print("\n[VERIFY] Testing endpoint after deployment...")
    stdin, stdout, stderr = ssh.exec_command(
        "timeout 3 curl -s -H 'Cookie: cs_token=test' http://localhost:5000/api/heatmap/scatter?timeframe=1w 2>&1"
    )
    response = stdout.read().decode('utf-8', errors='ignore')[:500]
    
    if response:
        print(f"[VERIFY] Response: {response}")
    else:
        print("[VERIFY] No response yet")
    
    print("\n[SUCCESS] Deployment to /app complete!")
    ssh.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
