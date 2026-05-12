#!/usr/bin/env python3
import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("Checking actual database file being used...")
    
    # Get all database files
    stdin, stdout, stderr = ssh.exec_command("find /app /root -name '*cryptoscanner*.db' -type f 2>/dev/null")
    db_files = stdout.read().decode('utf-8', errors='ignore').strip().split('\n')
    
    print("Found database files:")
    for db_file in db_files:
        if db_file.strip():
            print(f"\n  {db_file}")
            
            # Check file size and modification time
            stdin, stdout, stderr = ssh.exec_command(f"ls -lh '{db_file}'")
            info = stdout.read().decode('utf-8', errors='ignore').strip()
            print(f"    {info}")
            
            # Check table count
            stdin, stdout, stderr = ssh.exec_command(f"sqlite3 '{db_file}' '.tables'")
            tables = stdout.read().decode('utf-8', errors='ignore').strip()
            if tables:
                table_count = len(tables.split())
                print(f"    Tables: {table_count} ({tables[:50]}...)")
            else:
                print(f"    Tables: NONE (empty database)")
    
    print("\n\nChecking what config.py reports as DATABASE_PATH...")
    stdin, stdout, stderr = ssh.exec_command(
        "cd /app && python3 -c 'from config import DATABASE_PATH; print(DATABASE_PATH)' 2>&1"
    )
    config_db = stdout.read().decode().strip()
    print(f"  DATABASE_PATH: {config_db}")
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
