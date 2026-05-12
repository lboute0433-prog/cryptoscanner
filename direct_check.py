#!/usr/bin/env python3
import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Try direct API call from server
print("[API Test from server]")
stdin, stdout, stderr = ssh.exec_command("timeout 3 curl -s http://localhost:5000/api/smart_signals || echo 'TIMEOUT'")
resp = stdout.read().decode().strip()
print(f"Response: {resp[:200] if resp else 'NO RESPONSE'}")

# Check gunicorn process
print("\n[Gunicorn process]")
stdin, stdout, stderr = ssh.exec_command("ps aux | grep gunicorn | grep -v grep | wc -l")
ps_count = stdout.read().decode().strip()
print(f"Gunicorn processes: {ps_count}")

# Check if port 5000 is listening
print("\n[Port 5000 status]")
stdin, stdout, stderr = ssh.exec_command("netstat -tln | grep 5000 || lsof -i :5000 | head -2")
port_check = stdout.read().decode().strip()
print(f"Port info: {port_check if port_check else 'NOT LISTENING'}")

# Restart service one more time
print("\n[Restarting service]")
ssh.exec_command("sudo systemctl restart cryptoscanner")
time.sleep(5)

# Test again
print("\n[Final test]")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/market | head -c 100")
final_resp = stdout.read().decode()
print(f"Market API: {final_resp[:100] if final_resp else 'NO RESPONSE'}")

ssh.close()
