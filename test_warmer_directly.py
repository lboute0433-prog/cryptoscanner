#!/usr/bin/env python3
import paramiko
import time
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("Testing warmer function directly on server...")
    
    # Try running just the build_rsi_heatmap_data function
    cmd = """cd /app && python3 << 'PYEOF'
import sys
import time
import os
os.chdir('/app')
sys.path.insert(0, '/app')

from rsi_engine import build_rsi_heatmap_data

print("Starting RSI build test (timeout 20s)...")
start = time.time()

try:
    data = build_rsi_heatmap_data('1w', timeout_seconds=15, fast_mode=True)
    elapsed = time.time() - start
    print(f"Got {len(data)} coins in {elapsed:.1f}s")
    if data:
        print(f"Sample: {data[0]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
PYEOF
"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=30)
    output = stdout.read().decode('utf-8', errors='ignore')
    errors = stderr.read().decode('utf-8', errors='ignore')
    
    print("Output:")
    print(output)
    
    if errors:
        print("\nErrors:")
        print(errors)
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
