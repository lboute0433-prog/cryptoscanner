#!/usr/bin/env python3
import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("Checking critical environment variables...")
    
    # Check gunicorn environment
    stdin, stdout, stderr = ssh.exec_command(
        "ps aux | grep gunicorn | grep -v grep | head -1"
    )
    proc = stdout.read().decode().strip()
    if proc:
        print(f"Gunicorn process:\n  {proc[:150]}")
    
    # Check systemd environment
    stdin, stdout, stderr = ssh.exec_command(
        "systemctl show cryptoscanner -p Environment 2>/dev/null"
    )
    env_output = stdout.read().decode().strip()
    print(f"\nSystemd Environment:\n  {env_output}")
    
    # Check PORT environment variable
    stdin, stdout, stderr = ssh.exec_command(
        "echo PORT=$PORT"
    )
    port = stdout.read().decode().strip()
    print(f"\nPORT variable: {port}")
    
    # Check RAILWAY_ENVIRONMENT
    stdin, stdout, stderr = ssh.exec_command(
        "echo RAILWAY_ENVIRONMENT=$RAILWAY_ENVIRONMENT"
    )
    railway = stdout.read().decode().strip()
    print(f"RAILWAY_ENVIRONMENT: {railway}")
    
    # Check actual config by importing
    print("\nChecking what config.py reports...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /app && python3 -c 'from config import IS_RAILWAY, RUN_BACKGROUND_JOBS; print(f\"IS_RAILWAY={IS_RAILWAY}\"); print(f\"RUN_BACKGROUND_JOBS={RUN_BACKGROUND_JOBS}\")' 2>&1"
    )
    config_out = stdout.read().decode().strip()
    config_err = stderr.read().decode().strip()
    
    if config_out:
        print(f"Config output:\n  {config_out}")
    if config_err:
        print(f"Config error:\n  {config_err}")
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
