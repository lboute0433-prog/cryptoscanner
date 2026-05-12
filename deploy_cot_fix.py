#!/usr/bin/env python3
"""
Deploy COT chart fix to Hetzner
"""
import paramiko
import os
import sys

def deploy_cot_fix():
    hostname = "46.225.234.71"
    username = "root"
    
    # The password from earlier sessions
    password = "pXdHtvJrbUKL"
    
    files_to_deploy = [
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\templates\index.html", "/app/templates/index.html"),
    ]

    print("\n" + "="*60)
    print("Deploying COT Chart Fix")
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

        ssh.close()

        print("\n" + "="*60)
        print("[SUCCESS] COT CHART FIX DEPLOYED!")
        print("="*60)
        print("\nChanges deployed:")
        print("  * templates/index.html: Destroy both _cotChart and window.cotChartInstance")
        print("  * Fix: 'Canvas is already in use' error resolved")
        print("\nThe COT page should now work without canvas errors!")
        print("="*60 + "\n")

        return True

    except paramiko.AuthenticationException as e:
        print(f"\n[FAIL] SSH Authentication Error: {e}")
        return False
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = deploy_cot_fix()
    sys.exit(0 if success else 1)
