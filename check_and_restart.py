#!/usr/bin/env python3
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Check service status
stdin, stdout, stderr = ssh.exec_command("systemctl status cryptoscanner | head -5")
status_output = stdout.read().decode()
print("[STATUS]")
print(status_output)

# Try to restart if not active
stdin, stdout, stderr = ssh.exec_command("systemctl is-active cryptoscanner")
is_active = stdout.read().decode().strip()

if is_active != "active":
    print("\n[RESTART] Restarting service...")
    ssh.exec_command("sudo systemctl restart cryptoscanner")
    time.sleep(5)

# Test API
print("\n[TEST] Testing API...")
for attempt in range(3):
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals")
    resp = stdout.read().decode()
    if resp:
        if '"score_min":60' in resp:
            print("[SUCCESS] API returns score_min: 60!")
        elif '"score_min":90' in resp:
            print("[FAIL] API still returns 90")
        else:
            print(f"[Response] {resp[:150]}")
        break
    else:
        print(f"[Wait] Attempt {attempt+1}/3 - No response, waiting...")
        time.sleep(2)

ssh.close()
