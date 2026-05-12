#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

script = r"""python3 << 'PY'
import sqlite3

db_path = '/app/data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("[TABLES]")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n[platform_settings TABLE]")
cursor.execute("SELECT * FROM platform_settings")
rows = cursor.fetchall()
for row in rows:
    print(f"  {row}")

if not rows:
    print("  (empty)")

conn.close()
PY
"""

stdin, stdout, stderr = ssh.exec_command(script)
output = stdout.read().decode()
print(output)

ssh.close()
