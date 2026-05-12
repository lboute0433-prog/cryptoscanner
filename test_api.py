#!/usr/bin/env python3
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Check service status
print("[CHECK] Service status...")
stdin, stdout, stderr = ssh.exec_command("systemctl is-active cryptoscanner")
status = stdout.read().decode().strip()
print(f"Status: {status}")

if status != "active":
    print("\n[RESTART] Restarting service...")
    ssh.exec_command("sudo systemctl restart cryptoscanner")
    time.sleep(4)

# Test API
print("\n[TEST 1] /api/heatmap/scatter...")
stdin, stdout, stderr = ssh.exec_command("curl -s -w '\nSTATUS:%{http_code}' http://localhost:5000/api/heatmap/scatter | tail -5")
resp = stdout.read().decode()
print(resp)

print("\n[TEST 2] /api/market...")
stdin, stdout, stderr = ssh.exec_command("curl -s -w '\nSTATUS:%{http_code}' http://localhost:5000/api/market | head -c 100 && echo")
resp = stdout.read().decode()
print(resp)

ssh.close()
