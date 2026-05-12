#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Get logs from last 5 minutes
stdin, stdout, stderr = ssh.exec_command(
    "sudo journalctl -u cryptoscanner --since '5 minutes ago' 2>/dev/null | tail -50 | cat -v"
)
logs = stdout.read().decode()
print("[LOGS - Last 50 lines]")
for line in logs.split('\n')[-30:]:
    if line.strip():
        print(line[:150])

ssh.close()
