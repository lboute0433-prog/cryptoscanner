#!/usr/bin/env python3
import paramiko
import os
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("46.225.234.71", username="root", password="pXdHtvJrbUKL", timeout=10)

files_to_sync = [
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/app/app.py"),
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/root/cryptoscanner/app.py"),
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\templates\index.html", "/app/templates/index.html"),
    (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\templates\index.html", "/root/cryptoscanner/templates/index.html"),
]

print("[DEPLOY] Uploading app.py and index.html...")
sftp = ssh.open_sftp()

for local, remote in files_to_sync:
    if os.path.exists(local):
        try:
            print(f"  -> {remote}")
            sftp.put(local, remote)
        except Exception as e:
            print(f"  [SKIP] {e}")

sftp.close()

print("\n[RESTART] Restarting service...")
ssh.exec_command("sudo systemctl restart cryptoscanner")
time.sleep(4)

# Verify fixes
print("\n[VERIFY] Checking endpoints...")
tests = [
    ("/api/smart_signals", "score_min"),
    ("/api/heatmap/scatter", "success"),
    ("/api/market", "coins"),
]

for endpoint, check in tests:
    stdin, stdout, stderr = ssh.exec_command(f"curl -s http://localhost:5000{endpoint} | head -c 200")
    resp = stdout.read().decode()
    status = "OK" if check in resp else "FAIL"
    print(f"  {endpoint}: {status} - {resp[:80]}")

ssh.close()
print("\n[DONE] Deployment complete")

