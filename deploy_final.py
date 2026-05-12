#!/usr/bin/env python3
import paramiko
import os
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=10)

files = [
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/app/app.py"),
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/root/cryptoscanner/app.py"),
]

print("[DEPLOY] Uploading fixed app.py...")
sftp = ssh.open_sftp()
for local, remote in files:
    if os.path.exists(local):
        print(f"  {remote}...")
        sftp.put(local, remote)
sftp.close()

print("\n[RESTART] Restarting service...")
ssh.exec_command("sudo systemctl stop cryptoscanner")
time.sleep(1)
ssh.exec_command("sudo systemctl start cryptoscanner")
time.sleep(6)

# Test
print("\n[TEST] Testing all critical endpoints...")
tests = [
    ("/api/smart_signals", "score_min"),
    ("/api/heatmap/scatter", "success"),
    ("/api/market", "coins"),
    ("/api/signals", "signals"),
]

for endpoint, check_str in tests:
    stdin, stdout, stderr = ssh.exec_command(f"timeout 2 curl -s http://localhost:5000{endpoint} | head -c 200")
    resp = stdout.read().decode()
    status = "OK" if check_str in resp else "FAIL" if resp else "TIMEOUT"
    print(f"  {endpoint}: {status}")
    if resp:
        print(f"    {resp[:100]}")

ssh.close()
print("\n[DONE] Deployment complete")

