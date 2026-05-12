#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Create a Python script to fix the database
fix_script = """
import sys
sys.path.insert(0, '/app')
from db import connect_sqlite, set_setting, get_setting

# Check current value
current = get_setting('score_min', 'NOT_FOUND')
print(f'[Current] score_min = {current}')

# Fix it
try:
    set_setting('score_min', '60')
    verified = get_setting('score_min', 'NOT_FOUND')
    print(f'[Updated] score_min = {verified}')
    if verified == '60':
        print('[OK] Fix successful!')
    else:
        print('[WARN] Value did not update correctly')
except Exception as e:
    print(f'[Error] {e}')
"""

print("[FIX] Fixing score_min in database...")
stdin, stdout, stderr = ssh.exec_command('cd /app && python3 -c ' + repr(fix_script))
output = stdout.read().decode()
print(output)

# Restart service
print("\n[RESTART] Restarting service...")
ssh.exec_command("sudo systemctl restart cryptoscanner")

# Test
print("[TEST] Testing API...")
import time
time.sleep(2)
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals")
response = stdout.read().decode()
print(f"Response: {response[:100]}")

ssh.close()
