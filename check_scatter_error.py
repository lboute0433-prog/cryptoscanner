#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Get logs mentioning scatter or /api/heatmap
stdin, stdout, stderr = ssh.exec_command(
    "sudo journalctl -u cryptoscanner --since '2 minutes ago' 2>/dev/null | grep -A 3 -B 1 'scatter\|build_rsi' | tail -30 | cat -v"
)
logs = stdout.read().decode()
print("[Scatter-related logs]")
print(logs if logs else "[No scatter logs found]")

ssh.close()
