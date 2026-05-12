#!/usr/bin/env python3
import paramiko
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("Testing warmer with DB write...")
    
    cmd = """cd /app && python3 << 'PYEOF'
import sys
import os
import json
os.chdir('/app')
sys.path.insert(0, '/app')

from rsi_engine import build_rsi_heatmap_data
from db import set_setting, get_setting

print("1. Building RSI data for 1w...")
data_1w = build_rsi_heatmap_data('1w', timeout_seconds=15, fast_mode=True) or []
print(f"   Got {len(data_1w)} coins")

print("2. Writing to DB...")
try:
    set_setting('rsi_heatmap_cache_1w', json.dumps(data_1w))
    print("   Write successful")
except Exception as e:
    print(f"   Write error: {e}")

print("3. Reading back from DB...")
try:
    cached = get_setting('rsi_heatmap_cache_1w')
    if cached:
        data = json.loads(cached)
        print(f"   Read {len(data)} coins from cache")
        if data:
            print(f"   Sample: {data[0]['symbol']}")
    else:
        print("   Cache is None")
except Exception as e:
    print(f"   Read error: {e}")
PYEOF
"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore')
    errors = stderr.read().decode('utf-8', errors='ignore')
    
    print("Output:")
    print(output)
    
    if errors:
        print("\nErrors:")
        print(errors[:500])
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
