#!/usr/bin/env python3
import paramiko
import time
import sys

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=15)
    
    print("Setting DATABASE_PATH environment variable and restarting...")
    
    # Export DATABASE_PATH and restart the service
    cmd = """
    export DATABASE_PATH=/app/cryptoscanner.db
    systemctl restart cryptoscanner
    """
    
    stdin, stdout, stderr = ssh.exec_command(cmd)
    time.sleep(8)
    
    print("Service restarted, waiting for initialization...")
    time.sleep(3)
    
    # Check if tables are now created
    stdin, stdout, stderr = ssh.exec_command("sqlite3 /app/cryptoscanner.db '.tables'")
    tables = stdout.read().decode('utf-8', errors='ignore').strip()
    
    if tables:
        print(f"✓ Database tables created! ({len(tables.split())} tables)")
        
        # Now test the RSI HEATMAP endpoint with a test session
        print("\nTesting RSI HEATMAP endpoint...")
        
        stdin, stdout, stderr = ssh.exec_command(
            "timeout 5 curl -s -H 'Cookie: cs_token=dummy' http://localhost:5000/api/heatmap/scatter?timeframe=1w 2>/dev/null | head -100"
        )
        response = stdout.read().decode('utf-8', errors='ignore')
        print(f"Response: {response[:150]}")
    else:
        print("✗ Tables still not created")
        print("Checking for errors...")
        
        stdin, stdout, stderr = ssh.exec_command("tail -5 /root/cryptoscanner/app.log 2>/dev/null")
        logs = stdout.read().decode('utf-8', errors='ignore')
        if logs:
            print(f"Logs: {logs[:200]}")
    
    ssh.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
