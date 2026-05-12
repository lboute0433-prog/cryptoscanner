#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

stdin, stdout, stderr = ssh.exec_command(
    "sudo journalctl -u cryptoscanner --since '5 minutes ago' -n 100 --no-pager | grep -i 'debug.*smart_signals\|score_min'"
)
logs = stdout.read().decode()
print(logs if logs else "[No logs found for smart_signals]")

ssh.close()
