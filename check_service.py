#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)

print("[CHECK] Service status...")
stdin, stdout, stderr = ssh.exec_command("systemctl is-active cryptoscanner")
status = stdout.read().decode().strip()
print(f"Service status: {status}")

if status != "active":
    print("\n[RESTART] Starting service...")
    ssh.exec_command("sudo systemctl start cryptoscanner")
    import time
    time.sleep(3)

print("\n[TEST] Testing API...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/market | head -c 100")
api_resp = stdout.read().decode()
print(f"Market endpoint: {api_resp[:100]}")

ssh.close()
