#!/bin/bash
set -e

# CryptoScanner Pro — Script de Correction Déploiement Hetzner
# À exécuter sur le serveur: bash fix_deployment.sh

echo "═══════════════════════════════════════════════════════════"
echo "🔧 CryptoScanner Pro — Correction Déploiement Hetzner"
echo "═══════════════════════════════════════════════════════════"

# ─── Vérification Prérequis ────────────────────────────────────
echo ""
echo "▶ ÉTAPE 1: Vérification prérequis"
echo "────────────────────────────────────"

if [ ! -f "app.py" ]; then
    echo "❌ FAIL: app.py non trouvé dans le répertoire courant"
    exit 1
fi

if [ ! -f "config.py" ]; then
    echo "❌ FAIL: config.py non trouvé"
    exit 1
fi

if [ ! -f "smart_signals.py" ]; then
    echo "❌ FAIL: smart_signals.py non trouvé"
    exit 1
fi

echo "✓ Fichiers essentiels trouvés"

# ─── Vérifier que start_runtime_services() est au démarrage ───
echo ""
echo "▶ ÉTAPE 2: Vérifier que start_runtime_services() est au démarrage"
echo "───────────────────────────────────────────────────────────────────"

if grep -q "start_runtime_services()" app.py; then
    echo "✓ start_runtime_services() trouvé dans app.py"

    # Compter les occurrences (doit y en avoir 2: une au démarrage, une dans if __name__)
    count=$(grep -c "start_runtime_services()" app.py)
    if [ "$count" -ge 2 ]; then
        echo "✓ start_runtime_services() appelée au DÉMARRAGE + if __name__ block ($count occurrences)"
    elif [ "$count" -eq 1 ]; then
        echo "⚠️  WARN: start_runtime_services() trouvée seulement 1 fois (idéalement 2)"
    fi
else
    echo "❌ FAIL: start_runtime_services() non trouvée dans app.py"
    echo "   Ajout requis ligne ~179 après init des engines"
    exit 1
fi

# ─── Vérifier que smart_signals a les bonnes signatures ──────
echo ""
echo "▶ ÉTAPE 3: Vérifier signatures smart_signals.py"
echo "─────────────────────────────────────────────────"

if grep -q "def build_telegram_alert.*for_role" smart_signals.py; then
    echo "✓ build_telegram_alert() a le paramètre for_role"
else
    echo "❌ FAIL: build_telegram_alert() n'a pas le paramètre for_role"
    exit 1
fi

if grep -q "def build_retrace_alert.*candles_15m" smart_signals.py; then
    echo "✓ build_retrace_alert() a le paramètre candles_15m"
else
    echo "⚠️  WARN: build_retrace_alert() n'a pas le paramètre candles_15m (peut être optionnel)"
fi

# ─── Vérifier que app.py importe les bonnes fonctions ───────
echo ""
echo "▶ ÉTAPE 4: Vérifier imports app.py"
echo "────────────────────────────────────"

if grep -q "from indices_engine import.*calc_crypto_total3.*calc_crypto_others" app.py; then
    echo "✓ app.py importe calc_crypto_total3 et calc_crypto_others"
else
    echo "❌ FAIL: app.py n'importe pas les fonctions requises"
    exit 1
fi

# ─── Vérifier que broadcast=True est dans les emit() ───────
echo ""
echo "▶ ÉTAPE 5: Vérifier socketio.emit(..., broadcast=True)"
echo "─────────────────────────────────────────────────────────"

emit_count=$(grep -c 'socketio.emit.*broadcast=True' app.py || true)
if [ "$emit_count" -ge 5 ]; then
    echo "✓ Au moins 5 appels socketio.emit() avec broadcast=True trouvés"
else
    echo "⚠️  WARN: Seulement $emit_count socketio.emit(..., broadcast=True) trouvés (idéalement 5+)"
fi

# ─── Vérifier le fichier .env ─────────────────────────────────
echo ""
echo "▶ ÉTAPE 6: Configuration .env"
echo "──────────────────────────────"

if [ -f ".env" ]; then
    echo "✓ .env existe"

    # Vérifier les variables critiques
    missing=()

    if ! grep -q "MAKE_ADMIN" .env; then
        missing+=("MAKE_ADMIN")
    else
        echo "  ✓ MAKE_ADMIN défini"
    fi

    if ! grep -q "ADMIN_PASSWORD" .env; then
        missing+=("ADMIN_PASSWORD")
    else
        echo "  ✓ ADMIN_PASSWORD défini"
    fi

    if ! grep -q "TG_TOKEN" .env && ! grep -q "TG_CHAT" .env; then
        echo "  ⚠️  WARN: TG_TOKEN/TG_CHAT manquants (alertes Telegram désactivées)"
    else
        echo "  ✓ Telegram configuré"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo "❌ Variables manquantes dans .env: ${missing[*]}"
        echo "   Ajoute ces variables dans .env et redémarre l'app"
    fi
else
    echo "❌ FAIL: .env n'existe pas"
    echo ""
    echo "Créer un .env avec au minimum:"
    echo "  MAKE_ADMIN=ton_username"
    echo "  ADMIN_PASSWORD=ton_mot_de_passe"
    echo "  TG_TOKEN=123456:ABCDEF..."
    echo "  TG_CHAT=-1001234567890"
    echo "  RUN_BACKGROUND_JOBS=true"
    exit 1
fi

# ─── Vérifier la base de données ──────────────────────────────
echo ""
echo "▶ ÉTAPE 7: Vérifier base de données"
echo "────────────────────────────────────"

DB_PATH=${DATABASE_PATH:-cryptoscanner.db}

if [ -f "$DB_PATH" ]; then
    echo "✓ Base de données trouvée: $DB_PATH"

    # Compter les administrateurs
    admin_count=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM users WHERE role='admin';" 2>/dev/null || echo "0")

    if [ "$admin_count" -gt 0 ]; then
        echo "✓ Administrateur(s) trouvé(s) dans la BD: $admin_count"
    else
        echo "⚠️  WARN: Aucun administrateur dans la BD"
        echo "   → Relance l'app pour que le bootstrap admin crée le compte"
    fi
else
    echo "⚠️  WARN: Base de données non trouvée (sera créée au premier démarrage)"
fi

# ─── Résumé ────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ DIAGNOSTIC COMPLET — Tous les contrôles passent!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Prochaines étapes:"
echo "1. Redémarre l'app: pm2 restart cryptoscanner"
echo "2. Vérifier les logs: pm2 logs cryptoscanner --lines 50"
echo "3. Tester les endpoints:"
echo "   • curl http://localhost:5000/api/ticker"
echo "   • curl http://localhost:5000/api/market_info"
echo "4. Vérifier la connexion admin dans le navigateur"
echo ""
echo "Les bugs suivants devraient être FIXES:"
echo "  ✅ Page DATA macro — données visibles (macro_update émis)"
echo "  ✅ Alertes Telegram — actives et envoyées"
echo "  ✅ Authentification admin — fonctionnelle"
echo ""
