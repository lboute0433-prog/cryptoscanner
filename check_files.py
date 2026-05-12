#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

print("[CHECK] File modification times...")
stdin, stdout, stderr = ssh.exec_command("ls -lh /app/app.py /app/scanner_engine.py /app/templates/index.html")
files = stdout.read().decode()
print(files)

print("\n[CHECK] Checking what load_admin_alert_settings returns in live Python...")
stdin, stdout, stderr = ssh.exec_command(r"""python3 -c "
import sys
sys.path.insert(0, '/app')
from scanner_engine import load_admin_alert_settings
settings = load_admin_alert_settings()
print(f'score_min from load_admin_alert_settings: {settings.get(\"score_min\")}')
print(f'Full settings keys: {list(settings.keys())}')
" """)
output = stdout.read().decode()
print(output)

ssh.close()
