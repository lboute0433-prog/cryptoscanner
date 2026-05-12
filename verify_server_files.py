#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

files = ["/app/db.py", "/root/cryptoscanner/db.py"]

for f in files:
    print(f"\n[{f}]")
    # Check line count
    stdin, stdout, stderr = ssh.exec_command(f"wc -l {f}")
    lines = stdout.read().decode().strip()
    print(f"Lines: {lines}")
    
    # Check for init_alert_settings
    stdin, stdout, stderr = ssh.exec_command(f"grep 'def init_alert_settings' {f}")
    result = stdout.read().decode().strip()
    if result:
        print(f"Has init_alert_settings: YES")
    else:
        print(f"Has init_alert_settings: NO")
    
    # Check file last modified
    stdin, stdout, stderr = ssh.exec_command(f"ls -l {f}")
    info = stdout.read().decode().strip()
    print(f"Info: {info}")

ssh.close()
