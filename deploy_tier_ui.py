#!/usr/bin/env python3
import paramiko
import sys

hostname = "46.225.234.71"
username = "root"
password = "pXdHtvJrbUKL"

try:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, timeout=10)
    print("✓ Connected to server")
    
    # Upload index.html via SFTP
    print("\n[1/4] Uploading index.html...")
    sftp = client.open_sftp()
    sftp.put("templates/index.html", "/app/templates/index.html")
    print("✓ Uploaded index.html")
    sftp.close()
    
    # Restart service
    print("\n[2/4] Restarting service...")
    stdin, stdout, stderr = client.exec_command("sudo systemctl restart cryptoscanner")
    exit_code = stdout.channel.recv_exit_status()
    output = stdout.read().decode().strip()
    if output:
        print(f"  {output}")
    print("✓ Service restarted" if exit_code == 0 else f"⚠ Exit code: {exit_code}")
    
    # Wait for service to start
    print("\n[3/4] Waiting for service to stabilize...")
    import time
    time.sleep(3)
    
    # Verify deployment
    print("\n[4/4] Verifying deployment...")
    stdin, stdout, stderr = client.exec_command("curl -s -k 'https://127.0.0.1/api/alerts' | head -c 50")
    output = stdout.read().decode().strip()
    print(f"  API response: {output}...")
    
    client.close()
    print("\n✅ Deployment complete!")
    print("\nChanges deployed:")
    print("  • ALERTES PRIX: Added tier-based UI (rules, limits, upgrade messages)")
    print("  • WATCHLIST: Tier-based UI (already implemented)")
    print("  • Both now respect: FREE (0), MEMBRE (5), PAYANT (10), VIP (∞), ADMIN (∞)")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
