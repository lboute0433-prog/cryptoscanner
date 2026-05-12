#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Get last journal logs (avoid unicode issues)
stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u cryptoscanner -n 30 --no-pager 2>/dev/null | tail -15 | cat -v")
logs = stdout.read().decode()
print("[LOGS]")
for line in logs.split('\n')[-10:]:
    if line.strip():
        print(line[:120])

# Check if gunicorn is running
stdin, stdout, stderr = ssh.exec_command("ps aux | grep gunicorn | grep -v grep | wc -l")
count = stdout.read().decode().strip()
print(f"\n[GUNICORN] Processes running: {count}")

ssh.close()
