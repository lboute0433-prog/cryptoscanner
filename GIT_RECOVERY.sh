#!/bin/bash
# Script de récupération git pour les verrous persistants
# Exécuter depuis le répertoire racine du projet

set -e

PROJECT_DIR="$(pwd)"
echo "═══════════════════════════════════════════════════════════════════"
echo "Git Recovery — Nettoyage verrous et commit fix macro"
echo "═══════════════════════════════════════════════════════════════════"
echo "Répertoire: $PROJECT_DIR"
echo ""

# Étape 1 : Vérifier que c'est un repo git
if [ ! -d ".git" ]; then
    echo "❌ Erreur: Pas un repo git. Exécute ce script à la racine du projet."
    exit 1
fi

# Étape 2 : Killer les processus git orphelins
echo "[1/4] Nettoyage des processus..."
pkill -f "git.*cryptoscanner" || true
sleep 2

# Étape 3 : Supprimer tous les verrous git
echo "[2/4] Suppression des verrous git..."
find .git -name "*.lock" -type f -delete 2>/dev/null || true
find .git -path "*/refs/*" -name "*lock*" -delete 2>/dev/null || true
echo "  ✓ Verrous supprimés"

# Étape 4 : Vérifier le statut
echo "[3/4] Vérification du statut..."
git status --short | grep "news_macro" && echo "  ✓ news_macro.py modifié détecté" || echo "  ⚠️ news_macro.py non modifié?"

# Étape 5 : Committer
echo "[4/4] Commit des changements..."
sleep 2
git add news_macro.py

git commit -m "fix(macro): Améliore _fetch_ff_xml avec 5 fallbacks et persist cache BDD

- _fetch_ff_xml(): +5 URLs fallback, timeout 20s, logging détaillé
- Cache persistence en macro_cache (BDD) pour survivre redémarrages
- Fallback BDD (7j) si fetch échoue
- get_calendar(): utilise forecast_val en fallback pour éviter actual=''
- Logging amélioré avec codes HTTP, timeouts, tailles XML"

# Étape 6 : Afficher le résultat
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ Commit réussi!"
echo "═══════════════════════════════════════════════════════════════════"

git log -1 --format="%h — %s"
echo ""
echo "Prochaine étape: git push origin master"
