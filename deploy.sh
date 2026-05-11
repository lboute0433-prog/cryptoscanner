#!/bin/bash
set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Déploiement : Correctif Paramètres d'Alertes"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Vérifier qu'on est en production
if [ ! -f "/app/app.py" ]; then
    echo "❌ Erreur : /app/app.py non trouvé"
    exit 1
fi

echo ""
echo "[1/5] Récupération du dernier code..."
cd /app
git pull origin master

echo ""
echo "[2/5] Vérification du code..."
python3 -m py_compile app.py db.py
echo "✓ Syntax Python valide"

echo ""
echo "[3/5] Redémarrage du service..."
sudo systemctl restart cryptoscanner
sleep 3

echo ""
echo "[4/5] Vérification de l'initialisation..."
LOGS=$(sudo journalctl -u cryptoscanner -n 30 --no-pager | grep "Alert settings" || echo "NOT_FOUND")

if [ "$LOGS" != "NOT_FOUND" ]; then
    echo "✓ Paramètres d'alertes initialisés :"
    echo "  $LOGS"
else
    echo "⚠ Logs d'initialisation non trouvés (normal au redémarrage)"
fi

echo ""
echo "[5/5] Test de l'API..."
sleep 2
RESPONSE=$(curl -s -k "https://46.225.234.71/api/smart_signals" 2>/dev/null || echo "ERROR")

if [ "$RESPONSE" != "ERROR" ]; then
    SCORE_MIN=$(echo "$RESPONSE" | grep -o '"score_min":[0-9]*' | grep -o '[0-9]*' || echo "ERROR")

    if [ "$SCORE_MIN" = "50" ]; then
        echo "✅ API fonctionne correctement !"
        echo "   score_min = 50 (CORRECT)"
    elif [ "$SCORE_MIN" = "85" ]; then
        echo "⚠ API retourne toujours la valeur par défaut"
        echo "   score_min = 85 (devrait être 50)"
        echo "   Vérifiez les logs : sudo journalctl -u cryptoscanner -f"
    else
        echo "⚠ API a répondu mais valeur inattendue : $SCORE_MIN"
    fi
else
    echo "⚠ Impossible de tester l'API (SSL peut être le problème)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Déploiement terminé !"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Afficher les logs en temps réel
echo ""
echo "Logs serveur (dernières 10 lignes) :"
sudo journalctl -u cryptoscanner -n 10 --no-pager
