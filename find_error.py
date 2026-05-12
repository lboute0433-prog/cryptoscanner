#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Get traceback
print("[Searching for Traceback/Exception]")
stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u cryptoscanner --since '2 minutes ago' 2>/dev/null | grep -A 5 -B 2 'Traceback\|Exception\|Error:' | head -40 | cat -v")
traceback = stdout.read().decode()
print(traceback if traceback else "[No traceback found]")

ssh.close()
