#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

script = r"""python3 << 'PY'
import sys, os
sys.path.insert(0, '/app')

from config import DATABASE_PATH, BASE_DIR
from db import DB_PATH

print(f"BASE_DIR: {BASE_DIR}")
print(f"DATABASE_PATH: {DATABASE_PATH}")
print(f"DB_PATH (from db.py): {DB_PATH}")

# Check which files exist
files_to_check = [
    "/app/data.db",
    "/app/cryptoscanner.db",
    "/root/cryptoscanner/data.db",
    "/root/cryptoscanner/cryptoscanner.db",
    str(BASE_DIR / "cryptoscanner.db"),
    str(DATABASE_PATH)
]

print("\n[FILES CHECK]")
for f in files_to_check:
    exists = os.path.exists(f)
    size = os.path.getsize(f) if exists else "N/A"
    print(f"  {f}: {'EXISTS' if exists else 'NOT FOUND'} ({size} bytes)")

PY
"""

stdin, stdout, stderr = ssh.exec_command(script)
output = stdout.read().decode()
print(output)

ssh.close()
