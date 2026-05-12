#!/usr/bin/env python3
import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=10)

# Force stop service
print("[STOP] Stopping service...")
ssh.exec_command("sudo systemctl stop cryptoscanner")

# Delete old files
print("[DELETE] Removing old app.py files...")
ssh.exec_command("rm /app/app.py /root/cryptoscanner/app.py")

# Upload fresh copy
print("[UPLOAD] Uploading fresh app.py...")
sftp = ssh.open_sftp()

local = r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py"
for remote in ["/app/app.py", "/root/cryptoscanner/app.py"]:
    sftp.put(local, remote)
    print(f"  Uploaded to {remote}")

sftp.close()

# Verify uploaded file
print("\n[VERIFY] Checking deployed file...")
stdin, stdout, stderr = ssh.exec_command("grep -c '@app.route.*heatmap.*scatter' /app/app.py")
count = stdout.read().decode().strip()
print(f"Scatter routes in /app/app.py: {count}")

print("\n[START] Starting service...")
ssh.exec_command("sudo systemctl start cryptoscanner")

ssh.close()
print("[DONE]")

