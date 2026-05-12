#!/usr/bin/env python3
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=30)

print("[STEP 1] Check current database value...")
stdin, stdout, stderr = ssh.exec_command(
    r"python3 << 'PYTHON_EOF'\nimport sys\nsys.path.insert(0, '/app')\nfrom db import get_setting\nprint(f'Current score_min: {get_setting(\"score_min\")}')\nPYTHON_EOF"
)
stdout.channel.recv_exit_status()
out = stdout.read().decode()
print(out)

print("\n[STEP 2] Update database...")
stdin, stdout, stderr = ssh.exec_command(
    r"python3 << 'PYTHON_EOF'\nimport sys\nsys.path.insert(0, '/app')\nfrom db import set_setting, get_setting\nset_setting('score_min', '60')\nprint(f'After update: {get_setting(\"score_min\")}')\nPYTHON_EOF"
)
stdout.channel.recv_exit_status()
out = stdout.read().decode()
print(out)

print("\n[STEP 3] Verify update in Python...")
stdin, stdout, stderr = ssh.exec_command(
    r"python3 << 'PYTHON_EOF'\nimport sys\nsys.path.insert(0, '/app')\nfrom scanner_engine import load_admin_alert_settings\nsettings = load_admin_alert_settings()\nprint(f'load_admin_alert_settings() returns score_min: {settings.get(\"score_min\")}')\nPYTHON_EOF"
)
stdout.channel.recv_exit_status()
out = stdout.read().decode()
print(out)

print("\n[STEP 4] Restart service...")
ssh.exec_command("sudo systemctl restart cryptoscanner")
time.sleep(3)

print("\n[STEP 5] Test API...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals")
resp = stdout.read().decode()
if '"score_min":60' in resp:
    print("[SUCCESS] API now returns score_min: 60!")
    print(resp)
elif '"score_min":90' in resp:
    print("[FAIL] API still returns score_min: 90")
    print(resp)
else:
    print("[CHECK] Response:", resp[:200])

ssh.close()
