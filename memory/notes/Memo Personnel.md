
Commande 

mot de passe pXdHtvJrbUKL

serveur 46.225.234.71
ssh root@46.225.234.71

# 1. REDÉMARRER L'APP (après modif Python)
pm2 restart cryptoscanner

# 2. VOIR LES LOGS (pour debug)
pm2 logs cryptoscanner --lines 50

# 3. VÉRIFIER L'ÉTAT
pm2 status

# 4. ARRÊTER L'APP
pm2 stop cryptoscanner

# 5. RELANCER L'APP
pm2 start cryptoscanner

# 6. ENTRER DANS LE DOSSIER (si besoin)
cd /root/cryptoscanner

# 7. VOIR LES FICHIERS
ls -la /root/cryptoscanner/

# 8. NETTOYER LES NULL BYTES (si erreur SyntaxError)
find /root/cryptoscanner -name "*.py" -exec sh -c 'tr -d "\0" < "$1" > "$1.tmp" && mv "$1.tmp" "$1"' _ {} \;

# 1. CONNECTER AU SERVEUR (depuis PowerShell)
ssh root@46.225.234.71

# Une fois connecté au serveur, tape ces commandes:

# 2. VOIR LES LOGS (100 dernières lignes)
pm2 logs cryptoscanner --lines 100

# 3. VOIR TOUS LES LOGS EN DIRECT (pour suivre en temps réel)
pm2 logs cryptoscanner

# 4. VÉRIFIER L'ÉTAT DE L'APP
pm2 status

# 5. REDÉMARRER L'APP (si besoin)
pm2 restart cryptoscanner

# 6. ALLER DANS LE DOSSIER (si besoin)
cd /root/cryptoscanner && ls -la


knowlege 


# 1. Activer l'environnement virtuel (à faire en premier)
.venv\Scripts\Activate.ps1

# 2. Compiler les dailies logs en articles de knowledge base
python scripts/compile.py --all

# 3. Compiler un log spécifique
python scripts/compile.py --file daily/2026-04-23.md

# 4. Voir ce qui serait compilé (sans créer de fichiers)
python scripts/compile.py --dry-run

# 5. Nettoyer et valider la knowledge base
python scripts/lint.py

# 6. Chercher dans la knowledge base
python scripts/query.py "ta recherche"

# 7. Archiver et compacter la knowledge base
python scripts/flush.py


Compilation complete. Total cost: $0.22
Knowledge base: 5 articles
(llm-personal-kb) PS C:\Users\loyan\Documents\Antigravity\cryptoscanner> python scripts/compile.py --file daily/test-setup.md
Files to compile (1):
  - test-setup.md

# 1. Compiler TOUS les dailies non compilés
python scripts/compile.py --all

# 2. Chercher une connaissance
python scripts/query.py "ta recherche"

# 3. Voir la knowledge base
cat knowledge/index.md