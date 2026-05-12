#!/usr/bin/env python3
import subprocess
import sys
import time

def deploy():
    """Deploy changes to Hetzner server"""
    
    # Try multiple connection methods
    ssh_commands = [
        # Try with password (using sshpass if available)
        'sshpass -p "pXdHtvJrbUKL" ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@46.225.234.71 "cd /home/ubuntu/cryptoscanner && git pull && sudo systemctl restart cryptoscanner"',
        
        # Try without password (key-based auth)
        'ssh -i ~/.ssh/id_rsa -o ConnectTimeout=5 ubuntu@46.225.234.71 "cd /home/ubuntu/cryptoscanner && git pull && sudo systemctl restart cryptoscanner"',
        
        # Try with default key
        'ssh -o ConnectTimeout=5 ubuntu@46.225.234.71 "cd /home/ubuntu/cryptoscanner && git pull && sudo systemctl restart cryptoscanner"',
    ]
    
    for cmd in ssh_commands:
        print(f"[Deployment] Trying: {cmd[:60]}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print(f"[Deployment] SUCCESS!")
            print(result.stdout)
            return True
        else:
            print(f"[Deployment] Failed: {result.stderr[:100]}")
    
    print("[Deployment] All methods failed. Manual deployment needed.")
    return False

if __name__ == '__main__':
    try:
        deploy()
    except Exception as e:
        print(f"[Deployment] Error: {e}")
        sys.exit(1)
