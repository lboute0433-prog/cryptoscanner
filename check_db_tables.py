#!/usr/bin/env python3
import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("Checking database tables...")
    
    stdin, stdout, stderr = ssh.exec_command(
        "sqlite3 /app/cryptoscanner.db '.tables'"
    )
    tables = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"Tables:\n  {tables}")
    
    print("\nChecking platform_settings table...")
    stdin, stdout, stderr = ssh.exec_command(
        "sqlite3 /app/cryptoscanner.db \"SELECT COUNT(*) FROM platform_settings;\""
    )
    count = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"  Rows in platform_settings: {count}")
    
    print("\nLast entries in platform_settings...")
    stdin, stdout, stderr = ssh.exec_command(
        "sqlite3 /app/cryptoscanner.db \"SELECT key, substr(value, 1, 50) FROM platform_settings ORDER BY ROWID DESC LIMIT 5;\""
    )
    entries = stdout.read().decode('utf-8', errors='ignore').strip()
    if entries:
        print(f"  {entries}")
    else:
        print("  (empty)")
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
