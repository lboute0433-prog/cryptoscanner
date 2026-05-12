#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

print("[LOGS] Last 30 service logs...")
stdin, stdout, stderr = ssh.exec_command("systemctl status cryptoscanner | head -20")
status = stdout.read().decode()
lines = status.split('\n')
for line in lines:
    if line.strip():
        print(line)

print("\n[JOURNAL] Recent errors...")
stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u cryptoscanner -n 20 --no-pager 2>/dev/null | tail -10")
logs = stdout.read().decode()
if logs:
    for line in logs.split('\n')[-5:]:
        if line.strip():
            print(line[:100])
else:
    print("No logs available")

ssh.close()
