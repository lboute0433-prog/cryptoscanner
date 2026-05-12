#!/usr/bin/env python3
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

print("[STOP] Stopping cryptoscanner service...")
ssh.exec_command("sudo systemctl stop cryptoscanner")
time.sleep(1)

print("[KILL] Killing any remaining Python processes...")
ssh.exec_command("pkill -9 -f gunicorn")
ssh.exec_command("pkill -9 -f python.*app.py")
time.sleep(1)

print("[CLEAR] Clearing Python cache...")
ssh.exec_command("find /app -name '*.pyc' -delete")
ssh.exec_command("find /app -type d -name '__pycache__' -delete")
time.sleep(1)

print("[START] Starting cryptoscanner service...")
stdin, stdout, stderr = ssh.exec_command("sudo systemctl start cryptoscanner")
time.sleep(3)

print("[CHECK] Checking service status...")
stdin, stdout, stderr = ssh.exec_command("sudo systemctl status cryptoscanner | head -10")
status = stdout.read().decode()
print(status)

print("[TEST] Testing API endpoint...")
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals")
response = stdout.read().decode()
print(response)

ssh.close()
