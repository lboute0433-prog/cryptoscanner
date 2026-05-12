#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

script = r"""python3 << 'PY'
import sys
sys.path.insert(0, '/app')

# Direct DB test
import sqlite3
conn = sqlite3.connect('/app/data.db')
cursor = conn.cursor()
cursor.execute("SELECT value FROM platform_settings WHERE key='score_min'")
row = cursor.fetchone()
db_value = row[0] if row else 'NOT_FOUND'
print(f'1. Direct DB query: score_min = {db_value}')
conn.close()

# Test get_setting()
from db import get_setting
gs_value = get_setting('score_min', 'FALLBACK_60')
print(f'2. get_setting("score_min") = {gs_value}')

# Test load_admin_alert_settings()
from scanner_engine import load_admin_alert_settings
settings = load_admin_alert_settings()
las_value = settings.get('score_min', 'NOT_IN_DICT')
print(f'3. load_admin_alert_settings()["score_min"] = {las_value}')

# Print full DEFAULTS from scanner_engine to see what it was created with
import scanner_engine
print(f'\n4. Checking DEFAULTS source in scanner_engine...')
import inspect
source = inspect.getsource(scanner_engine.load_admin_alert_settings)
# Print just the DEFAULTS line
for line in source.split('\n'):
    if 'score_min' in line.lower() and ('85' in line or '60' in line):
        print(f'   {line.strip()}')

PY
"""

stdin, stdout, stderr = ssh.exec_command(script)
output = stdout.read().decode()
print(output)

stderr_output = stderr.read().decode()
if stderr_output:
    print("\n[STDERR]:")
    print(stderr_output[:500])

ssh.close()
