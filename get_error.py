#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Get error messages
stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u cryptoscanner -n 40 --no-pager 2>/dev/null | grep -E 'Error|error|Traceback|Exception' | tail -10 | head -c 1000")
errors = stdout.read().decode()
print("[ERRORS]")
print(errors if errors else "[No errors found in logs]")

# Check process
stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'gunicorn|python.*app' | grep -v grep | wc -l")
proc = stdout.read().decode().strip()
print(f"\n[PROCESSES] Running: {proc}")

ssh.close()
