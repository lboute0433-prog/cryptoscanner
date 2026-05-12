#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Check if function exists in /app/db.py
stdin, stdout, stderr = ssh.exec_command("grep -n 'def init_alert_settings' /app/db.py")
app_result = stdout.read().decode()
print(f"[/app/db.py] {app_result if app_result else 'NOT FOUND'}")

# Check if function exists in /root/cryptoscanner/db.py
stdin, stdout, stderr = ssh.exec_command("grep -n 'def init_alert_settings' /root/cryptoscanner/db.py")
root_result = stdout.read().decode()
print(f"[/root/cryptoscanner/db.py] {root_result if root_result else 'NOT FOUND'}")

# Check file sizes
stdin, stdout, stderr = ssh.exec_command("ls -lh /app/db.py /root/cryptoscanner/db.py")
sizes = stdout.read().decode()
print(f"\n[SIZES]\n{sizes}")

ssh.close()
