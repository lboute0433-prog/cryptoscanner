#!/usr/bin/env python3
"""
Déploiement du menu mobile iOS vers le serveur Hetzner
Pousse index.html via SFTP et redémarre le service
"""

import paramiko
import os
import getpass

def deploy_mobile_menu():
    hostname = "46.225.234.71"
    username = input("SSH username [root]: ").strip() or "root"
    password = getpass.getpass(f"SSH password for {username}: ")

    local_file = r"C:\Users\loyan\Documents\Antigravity\cryptoscanner\templates\index.html"
    remote_file = "/app/templates/index.html"

    print("\n" + "="*60)
    print("Déploiement Menu Mobile iOS")
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

        # Vérifier fichier local
        if not os.path.exists(local_file):
            print(f"\n❌ Fichier local non trouvé: {local_file}")
            return False

        file_size = os.path.getsize(local_file)
        print(f"\n📄 Fichier local: {local_file}")
        print(f"   Taille: {file_size:,} bytes")

        # Pousser fichier
        print(f"\n📤 Envoi vers {remote_file}...")
        sftp.put(local_file, remote_file)
        print(f"✓ Fichier envoyé avec succès")

        # Vérifier fichier distant
        remote_stat = sftp.stat(remote_file)
        print(f"\n✓ Vérification distante:")
        print(f"   Taille distante: {remote_stat.st_size:,} bytes")

        # Vérifier que les media queries iOS sont présentes
        print(f"\n🔍 Vérification des media queries iOS...")
        sftp.get(remote_file, "/tmp/check_index.html")
        with open("/tmp/check_index.html", "r") as f:
            content = f.read()
            if "max-device-width:812px" in content:
                print(f"✓ Media query portrait iOS trouvée")
            else:
                print(f"❌ Media query portrait iOS MANQUANTE!")

            if "max-device-width:1024px" in content:
                print(f"✓ Media query landscape iOS trouvée")
            else:
                print(f"❌ Media query landscape iOS MANQUANTE!")

            if 'class="mobile-nav"' in content:
                print(f"✓ Structure HTML mobile-nav trouvée")
            else:
                print(f"❌ Structure HTML mobile-nav MANQUANTE!")

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
        stdin, stdout, stderr = ssh.exec_command("sudo journalctl -u cryptoscanner -n 3 --no-pager")
        logs = stdout.read().decode().strip()
        for line in logs.split('\n'):
            if line.strip():
                print(f"   {line[:80]}")

        ssh.close()

        print("\n" + "="*60)
        print("✅ DÉPLOIEMENT RÉUSSI!")
        print("="*60)
        print("\nLe menu hamburger devrait maintenant:")
        print("  • Apparaître sur iPhone/iPad en portrait (max 812px)")
        print("  • Apparaître sur iPad en landscape (max 1024px)")
        print("  • Utiliser les media queries @media (max-device-width)")
        print("\nVérifiez sur iOS Firefox avec Ctrl+F5 (effacer cache)")
        print("\n" + "="*60)

        return True

    except paramiko.AuthenticationException:
        print("\n❌ Erreur d'authentification SSH")
        return False
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    deploy_mobile_menu()
