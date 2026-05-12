#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Get latest error
print("[Latest logs]")
stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u cryptoscanner -n 50 --no-pager 2>/dev/null | tail -20 | cat -v")
logs = stdout.read().decode()
for line in logs.split('\n')[-10:]:
    if line.strip():
        print(line[:120])

ssh.close()
