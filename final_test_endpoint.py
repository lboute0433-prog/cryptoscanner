#!/usr/bin/env python3
import paramiko
import json
import sys
import time

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("Final verification of RSI HEATMAP endpoint...")
    
    # Create a test user and session directly
    print("\n1. Creating test session in database...")
    
    cmd = """cd /app && python3 << 'PYEOF'
import sqlite3
import uuid
from datetime import datetime, timedelta

conn = sqlite3.connect('/app/cryptoscanner.db')
c = conn.cursor()

# Create test user if needed
test_token = 'test_' + str(uuid.uuid4())
expires = (datetime.now() + timedelta(hours=1)).isoformat()

try:
    c.execute('''
        INSERT INTO sessions (token, user_id, tier, expires)
        VALUES (?, 1, 'free', ?)
    ''', (test_token, expires))
    conn.commit()
    print(f"Created session: {test_token}")
except Exception as e:
    print(f"Error creating session: {e}")

conn.close()
PYEOF
"""
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=10)
    session_output = stdout.read().decode('utf-8', errors='ignore')
    print(session_output)
    
    # Extract the token
    token = None
    for line in session_output.split('\n'):
        if 'Created session:' in line:
            token = line.split(': ')[1].strip()
            break
    
    if not token:
        print("Creating fallback test session...")
        token = "test_fallback_session_12345"
    
    print(f"\n2. Testing endpoint with token: {token[:30]}...")
    stdin, stdout, stderr = ssh.exec_command(
        f"timeout 5 curl -s -H 'Cookie: cs_token={token}' 'http://localhost:5000/api/heatmap/scatter?timeframe=1w' 2>/dev/null"
    )
    response = stdout.read().decode('utf-8', errors='ignore')
    
    if response:
        print(f"Response length: {len(response)} bytes")
        try:
            data = json.loads(response)
            if data.get('success'):
                items = len(data.get('data', []))
                source = data.get('source')
                print(f"\n✓ SUCCESS!")
                print(f"  Items returned: {items}")
                print(f"  Source: {source}")
                if data.get('data'):
                    first = data['data'][0]
                    print(f"  Sample: {first['symbol']} (rsi_1w: {first.get('rsi_1w')})")
            else:
                print(f"Error in response: {data.get('error')}")
        except json.JSONDecodeError:
            print(f"Response:\n{response[:300]}")
    else:
        print("No response from endpoint")
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
