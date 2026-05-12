#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

script = r"""python3 << 'PY'
import sys, sqlite3, os
sys.path.insert(0, '/app')

db_path = '/app/data.db'
print(f"[DB] Connecting to {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='platform_settings'")
table_exists = cursor.fetchone() is not None
print(f"[TABLE] platform_settings exists: {table_exists}")

if not table_exists:
    print("[CREATE] Creating platform_settings table...")
    cursor.execute('''CREATE TABLE platform_settings (
        id INTEGER PRIMARY KEY,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()

# Check current value
cursor.execute("SELECT value FROM platform_settings WHERE key='score_min'")
row = cursor.fetchone()
current = row[0] if row else "NOT_FOUND"
print(f"[Current] score_min = {current}")

# Update/insert
print("[UPDATE] Setting score_min to 60...")
cursor.execute(
    "INSERT OR REPLACE INTO platform_settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
    ('score_min', '60')
)
conn.commit()

# Verify
cursor.execute("SELECT value FROM platform_settings WHERE key='score_min'")
row = cursor.fetchone()
updated = row[0] if row else "FAILED"
print(f"[Result] score_min = {updated}")

conn.close()
PY
"""

stdin, stdout, stderr = ssh.exec_command(script)
output = stdout.read().decode()
print(output)

print("\n[RESTART] Restarting service...")
ssh.exec_command("sudo systemctl restart cryptoscanner")

import time
time.sleep(3)

print("\n[TEST] Testing API...")
stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals | grep score_min")
resp = stdout.read().decode()
print(f"Response: {resp}")

ssh.close()
