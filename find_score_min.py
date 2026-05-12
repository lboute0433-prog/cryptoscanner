#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

# Find where score_min is stored
script = r"""python3 << 'PY'
import sys, sqlite3, os
sys.path.insert(0, '/app')

# Find the database file
db_files = ['/app/data.db', '/root/data.db', '/root/cryptoscanner/data.db']
db_path = None
for f in db_files:
    if os.path.exists(f):
        db_path = f
        print(f"[Found] Database: {db_path}")
        break

if not db_path:
    print("[Not found] No database file")
    sys.exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
print(f"[Tables] {tables}")

# Search each table for score_min
for table in tables:
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
    schema = cursor.fetchone()
    if schema:
        schema_text = schema[0] if schema else ''
        if 'key' in schema_text.lower() or 'setting' in schema_text.lower():
            print(f"\n[Check] Table {table}:")
            cursor.execute(f"SELECT * FROM {table} WHERE LOWER(CAST(* AS TEXT)) LIKE '%score%'")
            rows = cursor.fetchall()
            for row in rows:
                print(f"  {row}")

conn.close()
print("\n[Done]")
PY
"""

stdin, stdout, stderr = ssh.exec_command(script)
output = stdout.read().decode()
print(output)

ssh.close()
