#!/usr/bin/env python3
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

print("[PULL] Pulling latest from GitHub...")
stdin, stdout, stderr = ssh.exec_command("cd /root/cryptoscanner && git pull 2>&1")
pull_out = stdout.read().decode()
print(pull_out[:300])

print("\n[COPY] Syncing to /app...")
ssh.exec_command("cp /root/cryptoscanner/*.py /app/ 2>/dev/null")
ssh.exec_command("cp -r /root/cryptoscanner/templates/* /app/templates/ 2>/dev/null")
time.sleep(1)

print("\n[RESTART] Restarting service...")
stdin, stdout, stderr = ssh.exec_command("sudo systemctl stop cryptoscanner")
time.sleep(1)
stdin, stdout, stderr = ssh.exec_command("sudo systemctl start cryptoscanner")
time.sleep(5)

# Test
print("\n[TEST] Testing API...")
stdin, stdout, stderr = ssh.exec_command("timeout 3 curl -s http://localhost:5000/api/smart_signals | head -c 100 || echo 'NO RESPONSE'")
test_resp = stdout.read().decode()
print(test_resp[:100])

ssh.close()
