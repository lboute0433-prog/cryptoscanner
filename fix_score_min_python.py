#!/usr/bin/env python3
"""
Fix score_min in database using Python
"""
import paramiko
import os

def fix_score_min():
    hostname = "46.225.234.71"
    username = "root"
    password = "pXdHtvJrbUKL"
    
    print("\n" + "="*60)
    print("FIXING SCORE_MIN - Using Python")
    print("="*60)

    try:
        # Create SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password, timeout=10)
        print(f"\n[OK] Connected to {hostname}")

        # Create a Python script on the server
        fix_script = """
import sqlite3
import sys

try:
    # Try different possible database paths
    paths = [
        '/app/data.db',
        '/root/cryptoscanner/data.db',
        '/root/data.db',
        'data.db'
    ]
    
    conn = None
    for path in paths:
        try:
            conn = sqlite3.connect(path)
            print(f'[Connected] {path}')
            break
        except:
            continue
    
    if not conn:
        print('Could not find database')
        sys.exit(1)
    
    # Check if platform_settings table exists
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='platform_settings'")
    if cursor.fetchone():
        print('[OK] platform_settings table exists')
        
        # Check current value
        cursor.execute("SELECT value FROM platform_settings WHERE key='score_min'")
        result = cursor.fetchone()
        if result:
            print(f'[Current] score_min = {result[0]}')
        else:
            print('[Current] score_min not found in database')
        
        # Update value
        cursor.execute("INSERT OR REPLACE INTO platform_settings (key, value) VALUES ('score_min', '60')")
        conn.commit()
        print('[Updated] score_min = 60')
    else:
        print('[INFO] platform_settings table does not exist yet')
        print('[INFO] Will use default value 60')
    
    conn.close()
    print('[Success]')
except Exception as e:
    print(f'[Error] {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"""

        # Upload and run the script
        stdin, stdout, stderr = ssh.exec_command('cat > /tmp/fix_score.py << "PYEOF"\n' + fix_script + '\nPYEOF')
        stdout.channel.recv_exit_status()
        
        print("\n[RUN] Executing fix script...")
        stdin, stdout, stderr = ssh.exec_command('cd /root/cryptoscanner && python3 /tmp/fix_score.py')
        output = stdout.read().decode().strip()
        print(output)
        
        # Restart service
        print(f"\n[RESTART] Restarting service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart cryptoscanner")
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            print(f"[OK] Service restarted successfully")
        else:
            print(f"[WARN] Exit code: {exit_code}")

        # Test the endpoint
        print(f"\n[TEST] Testing smart_signals endpoint...")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/smart_signals | grep score_min")
        test_output = stdout.read().decode().strip()
        print(f"API Response: {test_output}")

        ssh.close()

        print("\n" + "="*60)
        print("[SUCCESS] SCORE_MIN FIXED!")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_score_min()
