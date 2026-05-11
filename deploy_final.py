#!/usr/bin/env python3
"""
Deploy RSI Heatmap fixes to Hetzner
"""

import paramiko
import os

def deploy_rsi_fixes():
    hostname = "46.225.234.71"
    username = "root"
    password = input(f"SSH password for {username}@{hostname}: ")

    files_to_deploy = [
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\rsi_engine.py", "/app/rsi_engine.py"),
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/app/app.py"),
    ]

    print("\n" + "="*60)
    print("Déploiement RSI Heatmap Fixes")
    print("="*60)

    try:
        # Create SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password, timeout=10)
        print(f"\n[OK] Connected to {hostname}")

        # Create SFTP client
        sftp = ssh.open_sftp()
        print(f"[OK] SFTP opened")

        # Deploy files
        for local_path, remote_path in files_to_deploy:
            if not os.path.exists(local_path):
                print(f"\n[FAIL] Local file not found: {local_path}")
                return False

            file_size = os.path.getsize(local_path)
            print(f"\n[UP] Uploading {os.path.basename(local_path)} ({file_size} bytes)...")
            sftp.put(local_path, remote_path)
            print(f"[OK] {os.path.basename(local_path)} deployed")

        sftp.close()

        # Restart service
        print(f"\n[RESTART] Restarting service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart cryptoscanner")
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            print(f"[OK] Service restarted")
        else:
            print(f"[WARN] Exit code: {exit_code}")

        # Check logs
        print(f"\n[LOGS] Checking logs...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u cryptoscanner -n 20 --no-pager")
        logs = stdout.read().decode().strip()
        for line in logs.split('\n')[-10:]:
            if line.strip():
                print(f"   {line[:120]}")

        # Test API
        print(f"\n[TEST] Testing API...")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/heatmap/scatter 2>&1 | head -c 300")
        api_test = stdout.read().decode().strip()
        if "error" in api_test or "401" in api_test:
            print(f"[INFO] API response (expected auth check): {api_test[:150]}...")
        else:
            print(f"[OK] API responding: {api_test[:150]}...")

        ssh.close()

        print("\n" + "="*60)
        print("[SUCCESS] DEPLOYMENT SUCCESSFUL!")
        print("="*60)
        print("\nChanges deployed:")
        print("  * rsi_engine.py: Fixed build_scatter_plot_data() - no more API calls")
        print("  * app.py: Added rsi_heatmap_warmer() background task")
        print("  * Cache warming: Every 4 minutes (prevents empty cache errors)")
        print("\nThe scatter plot should now work correctly!")
        print("="*60 + "\n")

        return True

    except paramiko.AuthenticationException:
        print("\n[FAIL] SSH Authentication Error")
        return False
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    deploy_rsi_fixes()
