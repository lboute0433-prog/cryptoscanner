#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

print("[SCATTER ENDPOINT ERROR]")
stdin, stdout, stderr = ssh.exec_command(
    "sudo journalctl -u cryptoscanner --since '1 minute ago' 2>/dev/null | grep -A 5 'heatmap/scatter' | tail -20 | cat -v"
)
logs = stdout.read().decode()
for line in logs.split('\n'):
    if line.strip():
        print(line[:180])

ssh.close()
