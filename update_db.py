#!/usr/bin/env python3
import paramiko
import base64

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Upload and run a Python script
script = """import sys; sys.path.insert(0, '/app'); from db import set_setting, get_setting; set_setting('score_min', '60'); print(f'Updated: {get_setting("score_min")}')"""

print("[RUN] Updating database...")
stdin, stdout, stderr = ssh.exec_command(f'python3 -c {repr(script)}')
result = stdout.read().decode().strip()
print(result)

print("\n[RESTART] Restarting service...")
ssh.exec_command("sudo systemctl restart cryptoscanner")

import time
time.sleep(3)

print("\n[TEST] Testing API...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals 2>&1")
resp_raw = stdout.read()
try:
    resp = resp_raw.decode()
    if '90' in resp:
        print(f"Response still shows 90: {resp}")
    elif '60' in resp:
        print(f"SUCCESS! Response shows 60: {resp}")
    else:
        print(f"Response: {resp[:200]}")
except:
    print("Could not decode response")

ssh.close()
