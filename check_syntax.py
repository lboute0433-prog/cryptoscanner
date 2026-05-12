#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Check Python syntax
print("[CHECK] Python syntax of app.py...")
stdin, stdout, stderr = ssh.exec_command("python3 -m py_compile /app/app.py")
exit_code = stdout.channel.recv_exit_status()
err_out = stderr.read().decode()

if exit_code != 0:
    print(f"[ERROR] Syntax error: {err_out[:500]}")
else:
    print("[OK] Syntax is valid")

# Try to import
print("\n[CHECK] Attempting to import app module...")
stdin, stdout, stderr = ssh.exec_command("cd /app && python3 -c 'import app' 2>&1 | head -20")
err_out = stderr.read().decode() + stdout.read().decode()
if err_out.strip():
    print(f"[ERROR] {err_out[:300]}")
else:
    print("[OK] Import successful")

# Try to start service manually
print("\n[CHECK] Attempting manual service start...")
stdin, stdout, stderr = ssh.exec_command("sudo systemctl start cryptoscanner; sleep 2; systemctl is-active cryptoscanner")
status = stdout.read().decode().strip()
print(f"Service status after start: {status}")

ssh.close()
