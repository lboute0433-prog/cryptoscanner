#!/usr/bin/env python3
import paramiko
import time
import json
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("[VERIFY] Getting test session token...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/ 2>&1 | grep -o 'cs_token=[^;]*' | head -1")
    token_line = stdout.read().decode('utf-8', errors='ignore').strip()
    print(f"[VERIFY] Token search result: {token_line[:100] if token_line else 'none'}")
    
    print("\n[VERIFY] Testing RSI HEATMAP endpoint with auth...")
    # Try the endpoint with a GET request and default authentication
    stdin, stdout, stderr = ssh.exec_command(
        "curl -s -H 'Cookie: cs_token=test123' http://localhost:5000/api/heatmap/scatter?timeframe=1w 2>&1 | head -500"
    )
    response = stdout.read().decode('utf-8', errors='ignore')
    
    if response:
        print(f"[VERIFY] Response length: {len(response)} bytes")
        if len(response) > 200:
            print(f"[VERIFY] Response preview:\n{response[:300]}")
        else:
            print(f"[VERIFY] Full response:\n{response}")
        
        try:
            data = json.loads(response)
            if data.get("success"):
                print(f"\n[SUCCESS] Endpoint working! Got {len(data.get('data', []))} items")
            else:
                print(f"\n[INFO] Response OK but not complete: {data}")
        except:
            print("\n[INFO] Response is not JSON, may still be starting up")
    else:
        print("[ERROR] No response from endpoint")
    
    print("\n[VERIFY] Checking warmer progress in logs...")
    stdin, stdout, stderr = ssh.exec_command("tail -50 /root/cryptoscanner/app.log")
    logs = stdout.read().decode('utf-8', errors='ignore')
    
    rsi_lines = [line for line in logs.split('\n') if 'RSI' in line or 'Cache' in line]
    if rsi_lines:
        print("[LOGS] Latest RSI-related messages:")
        for line in rsi_lines[-10:]:
            print(f"  {line[:150]}")
    else:
        print("[LOGS] No RSI messages in recent logs")
    
    ssh.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
