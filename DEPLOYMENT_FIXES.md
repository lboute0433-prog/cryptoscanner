# Déploiement Hetzner — Guide de Correction

## 🔴 BUGS DÉTECTÉS & CORRECTIONS

### BUG #1: Threads non lancés sur Gunicorn (CORRIGÉ)

**Problème:**
- `start_runtime_services()` était appelée dans le `if __name__` block (ligne 2211)
- Sur Hetzner/Gunicorn, ce bloc n'est jamais exécuté
- Résultat: macro_loop() ne s'exécutait jamais → pas de socketio.emit("macro_update")

**Correction appliquée:**
```python
# app.py ligne ~179
# Lancer les threads de fond AU DÉMARRAGE (Gunicorn-safe)
start_runtime_services()
```

### BUG #2: Variables d'environnement admin manquantes

**Problème:**
- `ADMIN_BOOTSTRAP_USER` et `ADMIN_BOOTSTRAP_PASSWORD` ne sont pas définies
- Aucun admin créé à l'initialisation
- Impossible de se connecter au panel admin

**Variables requises dans `.env`:**
```bash
MAKE_ADMIN=ton_username
ADMIN_PASSWORD=ton_mot_de_passe_super_secure
```

### BUG #3: Configuration Telegram manquante

**Problème:**
- `TG_TOKEN` et `TG_CHAT` (ou `TG_CHAT_FREE`) ne sont pas configurés
- Les alertes Telegram ne peuvent pas être envoyées

**Variables requises dans `.env`:**
```bash
TG_TOKEN=123456:ABCDEFG...  # Token du bot (depuis BotFather)
TG_CHAT=-1001234567890      # ID du canal admin
TG_CHAT_FREE=-1003997628346 # ID du canal public FREE
```

---

## 📋 CHECKLIST DÉPLOIEMENT HETZNER

### Étape 1: SSH vers Hetzner
```bash
ssh root@46.225.234.71
cd /root/cryptoscanner
```

### Étape 2: Créer/Mettre à jour le fichier `.env`
```bash
cat > .env << 'EOF'
# Admin
MAKE_ADMIN=admin
ADMIN_PASSWORD=votremotdepasssecurise

# Telegram
TG_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij
TG_CHAT=-1001234567890
TG_CHAT_FREE=-1003997628346

# Database
DATABASE_PATH=/root/cryptoscanner/cryptoscanner.db

# Background jobs (DOIT être TRUE sur Hetzner)
RUN_BACKGROUND_JOBS=true

# Secret (généré aléatoirement si absent)
SECRET_KEY=votre_clé_secrète_très_longue_et_aléatoire

# Site URL
SITE_URL=https://46.225.234.71

# SMTP (optionnel pour alertes email)
SMTP_EMAIL=votremail@gmail.com
SMTP_PASSWORD=votremotdepasse_app_gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EOF
```

### Étape 3: Vérifier les fichiers modifiés
```bash
# Vérifier que app.py a la ligne 179 (start_runtime_services)
grep -n "start_runtime_services()" app.py

# Doit montrer:
# 179: start_runtime_services()  ← Au démarrage Flask
# 2215: start_runtime_services() ← Dans le if __name__ block (redondant mais inoffensif)
```

### Étape 4: Redémarrer le service
```bash
pm2 stop cryptoscanner
pm2 start app.py --name cryptoscanner

# Vérifier les logs
pm2 logs cryptoscanner --lines 50
```

### Étape 5: Vérifier que les threads sont lancés
```bash
# Attendre ~5 secondes puis vérifier les logs
sleep 5
pm2 logs cryptoscanner | grep -E "Background services|scan_loop|macro_loop|smart_signal"

# Doit afficher:
# [Init] Background services lancés ✓
# [Startup] Hetzner - lancement des taches de fond (ou Local si pas Gunicorn)
```

### Étape 6: Tester les endpoints API

#### Test 1: Ticker
```bash
curl http://46.225.234.71/api/ticker
# Doit retourner: {"items": [...]}
```

#### Test 2: Données macro
```bash
curl http://46.225.234.71/api/market_info
# Doit retourner: {"fear_greed": {...}, "dominance": {...}, ...}
```

#### Test 3: Connexion admin
```bash
curl -X POST http://46.225.234.71/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"votremotdepasssecurise"}'
# Doit retourner: {"ok": true, "token": "...", "role": "admin"}
```

---

## 🔧 DIAGNOSTIC EN CAS DE PROBLÈME

### Les données macro n'arrivent toujours pas ?
```bash
pm2 logs cryptoscanner | grep -i "macro"
# Chercher: [Macro] ou [MacroAlert] messages

# Si erreur: [Macro] ... problème de réseau/API
# → Vérifier fetch_all_indices(), fetch_inflation(), etc.
```

### Les alertes Telegram ne s'envoient pas ?
```bash
pm2 logs cryptoscanner | grep -E "smart_signal|telegram|Telegram"
# Chercher: messages de génération/envoi

# Si absent: smart_signal_loop() ne s'exécute pas
# → Vérifier que RUN_BACKGROUND_JOBS=true
# → Redémarrer: pm2 restart cryptoscanner
```

### Impossible de se connecter en admin ?
```bash
# Vérifier que l'admin existe dans la BD
sqlite3 /root/cryptoscanner/cryptoscanner.db
> SELECT id, username, role FROM users WHERE role='admin';
# Doit afficher le compte admin

# Si absent:
# → Vérifier que MAKE_ADMIN et ADMIN_PASSWORD sont dans .env
# → Relancer app.py: pm2 restart cryptoscanner
# → Vérifier les logs: pm2 logs cryptoscanner | grep -i admin
```

---

## 📝 FICHIERS MODIFIÉS (Session 2026-05-04)

| Fichier | Modification | Ligne(s) |
|---------|-------------|---------|
| `app.py` | Ajout start_runtime_services() au démarrage Flask | 179 |

---

## ✅ TESTS À EFFECTUER

1. **Dashboard** — Les données du ticker et macro s'affichent ✓
2. **Authentification** — Admin peut se connecter ✓
3. **Alertes** — Messages Telegram arrivent dans les canaux ✓
4. **WebSocket** — Les mises à jour SocketIO arrivent en temps réel ✓

---

**Dernière mise à jour:** 2026-05-04
**Status:** Prêt pour déploiement Hetzner
