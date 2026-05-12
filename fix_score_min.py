#!/usr/bin/env python3
"""
Fix score_min in database from 90 to 60
"""
import paramiko

def fix_score_min():
    hostname = "46.225.234.71"
    username = "root"
    password = "pXdHtvJrbUKL"
    
    print("\n" + "="*60)
    print("FIXING SCORE_MIN IN DATABASE")
    print("="*60)

    try:
        # Create SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password, timeout=10)
        print(f"\n[OK] Connected to {hostname}")

        # Check current value
        print(f"\n[CHECK] Checking current database value...")
        stdin, stdout, stderr = ssh.exec_command(
            "sqlite3 /app/data.db \"SELECT key, value FROM platform_settings WHERE key='score_min'\""
        )
        current = stdout.read().decode().strip()
        print(f"Current value: {current}")

        # Update to 60
        print(f"\n[UPDATE] Updating score_min to 60...")
        stdin, stdout, stderr = ssh.exec_command(
            "sqlite3 /app/data.db \"UPDATE platform_settings SET value='60' WHERE key='score_min'\""
        )
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            print(f"[OK] Database updated")
        else:
            print(f"[WARN] Exit code: {exit_code}")

        # Verify update
        print(f"\n[VERIFY] Verifying update...")
        stdin, stdout, stderr = ssh.exec_command(
            "sqlite3 /app/data.db \"SELECT key, value FROM platform_settings WHERE key='score_min'\""
        )
        updated = stdout.read().decode().strip()
        print(f"Updated value: {updated}")

        # Restart service
        print(f"\n[RESTART] Restarting service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart cryptoscanner")
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            print(f"[OK] Service restarted")
        else:
            print(f"[WARN] Exit code: {exit_code}")

        ssh.close()

        print("\n" + "="*60)
        print("[SUCCESS] SCORE_MIN FIXED IN DATABASE!")
        print("="*60 + "\n")
        return True

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_score_min()
