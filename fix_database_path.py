#!/usr/bin/env python3
import paramiko
import sys
import time

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("Fixing database path configuration...")
    
    # Check current systemd service file
    print("\n1. Checking systemd service file...")
    stdin, stdout, stderr = ssh.exec_command("cat /etc/systemd/system/cryptoscanner.service | grep -A 5 Environment")
    service_env = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"Current environment:\n{service_env}")
    
    # Update service file to set DATABASE_PATH
    print("\n2. Updating systemd service file...")
    cmd = """sudo bash -c 'cat > /tmp/cryptoscanner_env.txt << EOF
[Service]
Environment="PATH=/app/venv/bin"
Environment="FLASK_ENV=production"
Environment="DATABASE_PATH=/app/cryptoscanner.db"
Environment="RUN_BACKGROUND_JOBS=true"
