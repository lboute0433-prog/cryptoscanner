#!/usr/bin/env python3
"""
Check what's actually running on the remote server
"""
import paramiko

hostname = "46.225.234.71"
username = "root"
password = "pXdHtvJrbUKL"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname, username=username, password=password, timeout=10)

# Get the load_admin_alert_settings default value
print("\n[CHECK] Checking load_admin_alert_settings in app.py...")
stdin, stdout, stderr = ssh.exec_command('grep -n "score_min.*:" /app/app.py | head -20')
print(stdout.read().decode())

# Check if the api_smart_signals function has debug logging
print("\n[CHECK] Checking api_smart_signals function...")
stdin, stdout, stderr = ssh.exec_command('grep -A 10 "def api_smart_signals" /app/app.py | head -15')
print(stdout.read().decode())

# Check scanner_engine score_min defaults
print("\n[CHECK] Checking scanner_engine defaults...")
stdin, stdout, stderr = ssh.exec_command('grep -B 2 -A 2 "score_min.*60\|score_min.*85" /app/scanner_engine.py')
print(stdout.read().decode())

ssh.close()
