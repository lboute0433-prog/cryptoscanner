#!/usr/bin/env python3
"""
Deploy scanner_engine.py fix to Hetzner
"""
import paramiko
import os

def deploy():
    hostname = "46.225.234.71"
    username = "root"
    password = "pXdHtvJrbUKL"
    
    files = [
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\scanner_engine.py", "/app/scanner_engine.py"),
    ]

    print("\n" + "="*60)
    print("Deploying scanner_engine.py (score_min fix)")
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
                return False

            size = os.path.getsize(local_path)
            print(f"\n[UP] Uploading {os.path.basename(local_path)} ({size} bytes)...")
            sftp.put(local_path, remote_path)
            print(f"[OK] Uploaded")

        sftp.close()

        # Restart service
        print(f"\n[RESTART] Restarting service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart cryptoscanner")
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            print(f"[OK] Service restarted")

        # Verify fix
        print(f"\n[VERIFY] Verifying fix...")
        stdin, stdout, stderr = ssh.exec_command('grep "score_min.*:" /app/scanner_engine.py | head -5')
        verification = stdout.read().decode()
        if "60" in verification:
            print("[OK] ✅ scanner_engine.py has score_min: 60")
        else:
            print("[WARN] Could not confirm fix")
            print(verification)

        # Test API
        print(f"\n[TEST] Testing smart_signals endpoint...")
        stdin, stdout, stderr = ssh.exec_command("sleep 2 && curl -s http://localhost:5000/api/smart_signals | grep score_min")
        test = stdout.read().decode().strip()
        print(f"Response: {test}")

        ssh.close()

        print("\n" + "="*60)
        print("[SUCCESS] SCANNER_ENGINE DEPLOYED!")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    deploy()
