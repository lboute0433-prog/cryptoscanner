#!/usr/bin/env python3
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Check if process is running
stdin, stdout, stderr = ssh.exec_command("ps aux | grep gunicorn | grep -v grep | wc -l")
count = stdout.read().decode().strip()
print(f"[Gunicorn processes]: {count}")

if count == "0":
    print("\n[RESTART] Starting service...")
    ssh.exec_command("sudo systemctl start cryptoscanner")
    time.sleep(5)

# Test
print("\n[TEST] Testing API...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals")
resp = stdout.read().decode()
if resp:
    print(f"Response: {resp[:200]}")
else:
    print("No response")

ssh.close()
