#!/usr/bin/env python3
import paramiko
import time
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("[VERIFY] Waiting for service to settle (5s)...")
    time.sleep(5)
    
    print("[VERIFY] Checking app status...")
    stdin, stdout, stderr = ssh.exec_command("systemctl status cryptoscanner | head -10")
    status = stdout.read().decode('utf-8', errors='ignore')
    if "running" in status.lower() or "active" in status.lower():
        print("[VERIFY] Service: RUNNING")
    else:
        print(f"[VERIFY] Service status uncertain: {status[:100]}")
    
    print("\n[VERIFY] Testing RSI HEATMAP endpoint...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/heatmap/scatter?timeframe=1w")
    response = stdout.read().decode('utf-8', errors='ignore')
    
    if response:
        print(f"[VERIFY] Response length: {len(response)} bytes")
        print(f"[VERIFY] First 300 chars:\n{response[:300]}")
        
        if "success" in response:
            print("\n[SUCCESS] RSI HEATMAP endpoint working!")
        elif "error" in response.lower():
            print("\n[WARNING] Endpoint returned error")
    else:
        print("[ERROR] No response from endpoint")
    
    print("\n[VERIFY] Checking recent app logs...")
    stdin, stdout, stderr = ssh.exec_command("tail -30 /root/cryptoscanner/app.log | grep -E 'RSI|Error|error'")
    logs = stdout.read().decode('utf-8', errors='ignore')
    if logs:
        print("[LOGS] Recent messages:")
        for line in logs.split('\n')[-10:]:
            if line.strip():
                print(f"  {line[:150]}")
    
    ssh.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
