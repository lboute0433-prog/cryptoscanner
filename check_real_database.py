#!/usr/bin/env python3
import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    db_file = "/root/cryptoscanner/cryptoscanner.db"
    
    print(f"Checking database at {db_file}...")
    
    stdin, stdout, stderr = ssh.exec_command(f"sqlite3 '{db_file}' '.tables'")
    tables = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"\nTables ({len(tables.split())}):")
    print(f"  {tables}")
    
    print("\nPlatform settings entries...")
    stdin, stdout, stderr = ssh.exec_command(
        f"sqlite3 '{db_file}' \"SELECT COUNT(*) as count FROM platform_settings;\""
    )
    count = stdout.read().decode().strip()
    print(f"  Total entries: {count}")
    
    print("\nRSI cache entries...")
    stdin, stdout, stderr = ssh.exec_command(
        f"sqlite3 '{db_file}' \"SELECT key, substr(value, 1, 100) FROM platform_settings WHERE key LIKE 'rsi_heatmap%';\""
    )
    entries = stdout.read().decode('utf-8', errors='ignore').strip()
    if entries:
        for line in entries.split('\n')[:5]:
            if line.strip():
                print(f"  {line}")
    else:
        print("  (none)")
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
