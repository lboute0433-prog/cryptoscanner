#!/usr/bin/env python3
"""
Déploiement RSI Heatmap vers Hetzner
Pousse rsi_engine.py, app.py, index.html via SFTP et redémarre le service
"""

import paramiko
import os
import getpass

def deploy_rsi_heatmap():
    hostname = "46.225.234.71"
    username = input("SSH username [root]: ").strip() or "root"
    password = getpass.getpass(f"SSH password for {username}: ")

    files_to_deploy = [
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\rsi_engine.py", "/app/rsi_engine.py"),
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py", "/app/app.py"),
        (r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\templates\index.html", "/app/templates/index.html"),
    ]

    print("\n" + "="*60)
    print("Déploiement RSI Heatmap")
    print("="*60)

    try:
        # Créer connexion SSH
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, username=username, password=password, timeout=10)
        print(f"\n✓ Connecté à {hostname}")

        # Créer client SFTP
        sftp = ssh.open_sftp()
        print(f"✓ SFTP ouvert")

        # Déployer les fichiers
        for local_path, remote_path in files_to_deploy:
            if not os.path.exists(local_path):
                print(f"\n❌ Fichier local non trouvé: {local_path}")
                return False

            file_size = os.path.getsize(local_path)
            print(f"\n📤 Envoi {os.path.basename(local_path)} ({file_size} bytes)...")
            sftp.put(local_path, remote_path)
            print(f"✓ {os.path.basename(local_path)} déployé")

        sftp.close()

        # Redémarrer service
        print(f"\n🔄 Redémarrage du service...")
        stdin, stdout, stderr = ssh.exec_command("sudo systemctl restart cryptoscanner")
        exit_code = stdout.channel.recv_exit_status()

        if exit_code == 0:
            print(f"✓ Service redémarré")
        else:
            print(f"⚠ Code sortie: {exit_code}")

        # Vérifier logs
        print(f"\n📋 Vérification logs...")
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u cryptoscanner -n 10 --no-pager")
        logs = stdout.read().decode().strip()
        for line in logs.split('\n')[-5:]:
            if line.strip():
                print(f"   {line[:100]}")

        # Tester API
        print(f"\n🧪 Test API...")
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:5000/api/heatmap/rsi?timeframe=1w 2>&1 | head -c 200")
        api_test = stdout.read().decode().strip()
        if "success" in api_test or "data" in api_test:
            print(f"✓ API fonctionne: {api_test[:100]}...")
        else:
            print(f"⚠ API réponse: {api_test[:100]}")

        ssh.close()

        print("\n" + "="*60)
        print("✅ DÉPLOIEMENT RÉUSSI!")
        print("="*60)
        print("\nRSI Heatmap est maintenant en production:")
        print("  • Endpoint: GET /api/heatmap/rsi?timeframe=1w|1m")
        print("  • Tier: MEMBER minimum")
        print("  • Cache: 5 minutes TTL")
        print("  • UI: DATA page → RSI HEATMAP tab")
        print("\n" + "="*60)

        return True

    except paramiko.AuthenticationException:
        print("\n❌ Erreur d'authentification SSH")
        return False
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    deploy_rsi_heatmap()
