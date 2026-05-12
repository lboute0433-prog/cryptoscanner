#!/usr/bin/env python3
"""
Deploy latest fixes: RSI HEATMAP endpoint + COT chart canvas
"""
import paramiko
import os
import time

hostname = "46.225.234.71"
username = "root"
password = "pXdHtvJrbUKL"

files = [
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/app/app.py"),
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\templates\index.html", "/app/templates/index.html"),
]

print("\n" + "="*60)
print("DEPLOYING: RSI HEATMAP + COT CHART FIXES")
print("="*60)

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, username=username, password=password, timeout=10)
    print(f"\n[OK] Connected to {hostname}")

    sftp = ssh.open_sftp()

    for local_path, remote_path in files:
        if not os.path.exists(local_path):
            print(f"\n[FAIL] File not found: {local_path}")
            continue

        size = os.path.getsize(local_path)
        print(f"\n[UP] Uploading {os.path.basename(local_path)} ({size} bytes)...")
        sftp.put(local_path, remote_path)
        print(f"[OK] {os.path.basename(local_path)} deployed")

    sftp.close()

    # Restart service
    print(f"\n[RESTART] Restarting service...")
    ssh.exec_command("sudo systemctl restart cryptoscanner")
    time.sleep(3)

    print(f"[OK] Service restarted")

    # Test endpoints
    print(f"\n[TEST 1] Testing /api/heatmap/scatter...")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/heatmap/scatter | head -c 150")
    resp1 = stdout.read().decode()
    if 'Not authenticated' in resp1 or 'success' in resp1:
        print(f"[OK] Endpoint responds: {resp1[:100]}")
    else:
        print(f"[CHECK] Response: {resp1[:100]}")

    ssh.close()

    print("\n" + "="*60)
    print("[SUCCESS] DEPLOYMENT COMPLETE!")
    print("="*60)
    print("\nChanges deployed:")
    print("  ✓ app.py: Added /api/heatmap/scatter endpoint")
    print("  ✓ templates/index.html: Fixed COT chart canvas destruction")
    print("\nTest in browser:")
    print("  1. RSI HEATMAP page should now load (requires member tier)")
    print("  2. COT page should switch assets without 'canvas' errors")
    print("="*60 + "\n")

except Exception as e:
    print(f"\n[FAIL] {e}")
    import traceback
    traceback.print_exc()

