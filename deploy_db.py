#!/usr/bin/env python3
import paramiko
import os
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=10)

files = [
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\db.py", "/app/db.py"),
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\db.py", "/root/cryptoscanner/db.py"),
]

print("[UPLOAD] Deploying current db.py...")
sftp = ssh.open_sftp()

for local, remote in files:
    if os.path.exists(local):
        size = os.path.getsize(local)
        print(f"  {remote} ({size} bytes)...")
        sftp.put(local, remote)

sftp.close()
print("[OK] Files uploaded")

print("\n[RESTART] Restarting service...")
ssh.exec_command("sudo systemctl stop cryptoscanner")
time.sleep(1)
ssh.exec_command("sudo systemctl start cryptoscanner")
time.sleep(5)

print("\n[TEST] Testing API...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals | head -c 150")
resp = stdout.read().decode()
if resp:
    print(f"Response: {resp}")
else:
    print("No response yet")

ssh.close()
