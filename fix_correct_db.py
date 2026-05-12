#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

script = r"""python3 << 'PY'
import sqlite3

# Fix the CORRECT database
db_files = [
    '/app/scanner.db',
    '/root/cryptoscanner/cryptoscanner.db'
]

for db_path in db_files:
    print(f"\n[CHECK] {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check for platform_settings table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='platform_settings'")
        has_table = cursor.fetchone() is not None
        
        if not has_table:
            print(f"  - No platform_settings table")
            conn.close()
            continue
        
        # Check current value
        cursor.execute("SELECT value FROM platform_settings WHERE key='score_min'")
        row = cursor.fetchone()
        current = row[0] if row else 'NOT_FOUND'
        print(f"  - Current score_min: {current}")
        
        # Update if needed
        if current != '60':
            print(f"  - Updating to 60...")
            cursor.execute(
                "INSERT OR REPLACE INTO platform_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                ('score_min', '60')
            )
            conn.commit()
            print(f"  - Updated!")
        
        conn.close()
    except Exception as e:
        print(f"  - Error: {e}")

PY
"""

stdin, stdout, stderr = ssh.exec_command(script)
output = stdout.read().decode()
print(output)

print("\n[RESTART] Restarting service...")
ssh.exec_command("sudo systemctl restart cryptoscanner")

import time
time.sleep(3)

print("[TEST] Testing API...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals")
resp = stdout.read().decode()
if '"score_min":60' in resp:
    print("[SUCCESS!!!] API now returns score_min: 60!")
    print(resp)
elif '"score_min":90' in resp:
    print("[Still wrong] API returns 90")
else:
    print(f"Response: {resp[:200]}")

ssh.close()
