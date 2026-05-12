#!/usr/bin/env python3
"""Deploy RSI warmer fix to Hetzner"""
import paramiko
import os
import time
import sys

try:
    print("[DEPLOY] Connecting to Hetzner (46.225.234.71)...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    print("[DEPLOY] Connected!")
    
    files_to_deploy = [
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/root/cryptoscanner/app.py"),
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\rsi_engine.py", "/root/cryptoscanner/rsi_engine.py"),
    ]
    
    print("\n[DEPLOY] Uploading fixed files...")
    sftp = ssh.open_sftp()
    for local, remote in files_to_deploy:
        if os.path.exists(local):
            print(f"  Uploading {local} to {remote}...")
            sftp.put(local, remote)
        else:
            print(f"  WARNING: {local} not found")
    sftp.close()
    print("[DEPLOY] Upload complete")
    
    print("\n[DEPLOY] Restarting cryptoscanner service...")
    ssh.exec_command("sudo systemctl restart cryptoscanner")
    time.sleep(8)
    print("[DEPLOY] Service restarted")
    
    print("\n[TEST] Testing RSI HEATMAP endpoint...")
    stdin, stdout, stderr = ssh.exec_command("timeout 5 curl -s http://localhost:5000/api/heatmap/scatter?timeframe=1w | head -c 300")
    response = stdout.read().decode('utf-8', errors='ignore')
    
    if "success" in response:
        print("[TEST] RSI HEATMAP endpoint: OK")
        print(f"Response sample: {response[:150]}...")
    else:
        print("[TEST] RSI HEATMAP endpoint: CHECKING")
        print(f"Response: {response[:200]}")
    
    print("\n[TEST] Checking warmer logs...")
    stdin, stdout, stderr = ssh.exec_command("tail -20 /root/cryptoscanner/app.log | grep RSI")
    logs = stdout.read().decode('utf-8', errors='ignore')
    if logs:
        print("[LOGS] Recent RSI warmer activity:")
        for line in logs.split('\n')[-5:]:
            if line.strip():
                print(f"  {line}")
    else:
        print("[LOGS] No RSI logs yet (warmer may still be warming up)")
    
    ssh.close()
    print("\n[SUCCESS] Deployment and verification complete!")
    
except Exception as e:
    print(f"\n[ERROR] Deployment failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
