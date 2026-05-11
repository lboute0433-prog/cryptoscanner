#!/usr/bin/env python3
"""
Script de déploiement distant pour CryptoScanner Pro
Exécute le déploiement sur le serveur Hetzner via SSH
"""

import paramiko
import sys
import getpass
import time

def deploy(hostname, username, password):
    """Déploie les changements sur le serveur."""

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("Déploiement : Correctif Paramètres d'Alertes")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    try:
        # Connexion SSH
        print("\n[SSH] Connexion au serveur...")
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password, timeout=10)
        print("✓ Connecté")

        commands = [
            ("Récupération du code", "cd /app && git pull origin master 2>&1"),
            ("Vérification syntax", "python3 -m py_compile app.py db.py"),
            ("Redémarrage service", "sudo systemctl restart cryptoscanner"),
            ("Attente redémarrage", "sleep 3"),
            ("Vérif initialisation", "sudo journalctl -u cryptoscanner -n 30 --no-pager | grep 'Alert settings' || echo 'En cours d\\'initialisation...'"),
        ]

        for step_name, cmd in commands:
            print(f"\n[{step_name}]")
            print(f"  Commande: {cmd}")

            stdin, stdout, stderr = client.exec_command(cmd)
            exit_code = stdout.channel.recv_exit_status()

            output = stdout.read().decode().strip()
            errors = stderr.read().decode().strip()

            if output:
                for line in output.split('\n')[:5]:  # Afficher max 5 lignes
                    print(f"  {line}")

            if exit_code != 0 and errors:
                print(f"  ⚠ Erreur: {errors[:200]}")
            else:
                print(f"  ✓ OK")

        # Test API
        print("\n[Test API]")
        print("  Attente de stabilisation...")
        time.sleep(2)

        stdin, stdout, stderr = client.exec_command(
            "curl -s -k 'https://127.0.0.1/api/smart_signals' 2>/dev/null | python3 -c \"import sys, json; data = json.load(sys.stdin); print(f'score_min = {data.get(\\\"score_min\\\", \\\"ERROR\\\")}')\" || echo 'Curl failed'"
        )
        output = stdout.read().decode().strip()
        print(f"  Réponse: {output}")

        if "50" in output:
            print("  ✓ SUCCÈS ! score_min = 50")
        elif "85" in output:
            print("  ⚠ Toujours 85 (par défaut)")
        else:
            print("  ⚠ Valeur inattendue")

        # Logs finaux
        print("\n[Logs finaux]")
        stdin, stdout, stderr = client.exec_command("sudo journalctl -u cryptoscanner -n 5 --no-pager")
        output = stdout.read().decode().strip()
        for line in output.split('\n'):
            if line.strip():
                print(f"  {line[:100]}")

        client.close()

        print("\n" + "━" * 50)
        print("Déploiement TERMINÉ !")
        print("━" * 50)

    except paramiko.AuthenticationException:
        print("\n❌ Erreur d'authentification SSH")
        print("   Vérifiez votre mot de passe")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    hostname = "46.225.234.71"
    username = input("Nom d'utilisateur SSH [root]: ").strip() or "root"
    password = getpass.getpass(f"Mot de passe SSH pour {username}: ")

    deploy(hostname, username, password)
