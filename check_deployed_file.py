#!/usr/bin/env python3
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL")

print("[CHECK] Checking DEFAULTS dict in deployed scanner_engine.py...")
stdin, stdout, stderr = ssh.exec_command(
    "grep -A 20 'DEFAULTS = {' /app/scanner_engine.py | grep -E 'score_min|# SMART'"
)
defaults = stdout.read().decode()
print(defaults)

print("\n[CHECK] Checking get_setting function calls...")
stdin, stdout, stderr = ssh.exec_command(
    "grep 'get_setting.*score_min' /app/scanner_engine.py"
)
get_setting_calls = stdout.read().decode()
print(get_setting_calls if get_setting_calls else "[No get_setting calls for score_min]")

print("\n[CHECK] Checking what get_setting returns for score_min...")
stdin, stdout, stderr = ssh.exec_command(r"""python3 -c "
import sys
sys.path.insert(0, '/app')
from db import get_setting
result = get_setting('score_min', 'DEFAULT_VALUE_60')
print(f'get_setting(\"score_min\", \"DEFAULT_VALUE_60\") = {result}')
" """)
gs_result = stdout.read().decode()
print(gs_result)

ssh.close()
