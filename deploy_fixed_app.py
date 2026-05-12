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

print("[UPLOAD] Deploying corrected app.py...")
sftp = ssh.open_sftp()

for local, remote in files:
    if os.path.exists(local):
        print(f"  {remote}...")
        sftp.put(local, remote)

sftp.close()
print("[OK] Files uploaded")

# Restart
print("\n[RESTART] Restarting service...")
ssh.exec_command("sudo systemctl restart cryptoscanner")
time.sleep(5)

# Test
print("\n[TEST] Checking if service is running...")
for i in range(3):
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals | head -c 100")
    resp = stdout.read().decode()
    if resp and 'score_min' in resp:
        print(f"SUCCESS! Response: {resp[:120]}")
        break
    elif i < 2:
        time.sleep(2)
    else:
        print(f"No valid response after retries: {resp[:100]}")

ssh.close()
print("\n[DONE]")

