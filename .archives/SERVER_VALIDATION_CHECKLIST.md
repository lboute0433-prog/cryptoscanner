# ✅ Checklist Validation — Déploiement Production

**Date:** 2026-05-10  
**Serveur:** Hetzner (46.225.234.71)  
**URL:** https://46.225.234.71

---

## 🔐 Sécurité & Infrastructure

- [ ] HTTPS activé (certificat auto-signé)
- [ ] Redirection HTTP → HTTPS fonctionne
- [ ] Certificat n'affiche pas d'erreur (accepté une fois)
- [ ] Headers de sécurité présents (F12 → Network)
- [ ] Pas d'alerte sur les mots de passe (securité)

## 📱 Page Accueil (Dashboard)

- [ ] Page charge sans erreur 404
- [ ] Header avec logo et statut visible
- [ ] 20 cryptos affichées avec prix
- [ ] Ticker défile en bas (ou section prix dynamique)
- [ ] Peut se connecter avec `loloPrim` / `loloPrim0409@@`

## 📊 Onglets du Dashboard

### SCANNER
- [ ] Données chargent (pas de 404)
- [ ] 20 cryptos avec prix BTC/USD
- [ ] Volumes affichés
- [ ] Signaux RSI visibles
- [ ] Boutons Action (ANALYSE, GRAPH) fonctionnent

### SIGNAUX
- [ ] Section visible
- [ ] Signaux smart chargent
- [ ] Affiche symbole, timeframe, direction

### COT
- [ ] Message "Données vendredi" OK (normal)
- [ ] Pas d'erreur 500
- [ ] Le vendredi: Données s'affichent

### WHALES
- [ ] Baleine chargent (mouvements récents)
- [ ] Affiche adresse, montant, direction
- [ ] Pas de timeout

### LIQUIDATIONS
- [ ] Heatmap affiche
- [ ] Code couleur rouge/vert visible
- [ ] Données Binance live

### FUNDING RATES
- [ ] Taux de financement affichent
- [ ] Positif/négatif clear

### MORNING BRIEF
- [ ] Texte IA charge
- [ ] Pas de timeout
- [ ] Format lisible

## 🔧 Page ADMIN

- [ ] Login fonctionne
- [ ] Redirection après login
- [ ] Onglet ALERTES visible
- [ ] 4 blocs d'alertes visibles:
  - [ ] SMART SIGNALS
  - [ ] RETRACE RSI
  - [ ] MACRO EVENTS
  - [ ] PLATEFORME

### Modification Alertes
- [ ] Peut modifier Score minimum
- [ ] Peut modifier Max alertes/cycle
- [ ] Peut modifier Cooldown
- [ ] Bouton Sauvegarder répond (pas 404)
- [ ] Message "Sauvegardé" s'affiche
- [ ] F12 → Network: Pas d'erreur 404 ou 500

## 📲 Intégration Telegram

- [ ] Bot ajouté au canal TG_CHAT
- [ ] Bot ajouté au canal TG_CHAT_FREE
- [ ] Bot a Admin rights
- [ ] Peut envoyer `/start` au bot
- [ ] Bot répond avec menu

### Test Alerte Manuelle
- [ ] Déclencher une alerte (baisser score minimum, attendre)
- [ ] Message Telegram reçu dans le canal
- [ ] Format correct du message
- [ ] Lien clickable vers le dashboard

## 🗂️ Fichiers Serveur

### Templates
- [ ] `/app/templates/index.html` — 736 KB
- [ ] `/app/templates/admin.html` — 53 KB
- [ ] `/app/templates/landing.html` — 44 KB

### Statiques
- [ ] `/app/static/ticker.js` — 2.0 KB

### Python
- [ ] `/app/app.py` — 131 KB (routes principales)
- [ ] `/app/db.py` — 27 KB (base de données)
- [ ] `/app/security.py` — 36 KB (auth)
- [ ] `/app/scanner_engine.py` — 79 KB (scanner crypto)
- [ ] Tous les engines présents

### Config
- [ ] `/app/.env` — Variables production
- [ ] `/app/requirements.txt` — Dépendances
- [ ] `/app/wsgi.py` — Entry point

## 🔄 Services Système

- [ ] `cryptoscanner` service: **active**
- [ ] `nginx` service: **active**
- [ ] Port 5000 répond (Flask)
- [ ] Port 80 redirige vers 443 (HTTPS)
- [ ] Port 443 répond (nginx + SSL)

### Auto-restart
- [ ] Tuez le process gunicorn: `pkill -f gunicorn`
- [ ] Service redémarre automatiquement en < 10s
- [ ] Dashboard accessible à nouveau

## 📊 API Endpoints

### GET Endpoints
- [ ] `GET /api/scanner/prices` → Retourne JSON
- [ ] `GET /api/smart_signals` → Retourne signaux
- [ ] `GET /api/admin/alerts/config` → Config alertes
- [ ] `GET /api/health` → Status

### POST Endpoints
- [ ] `POST /api/admin/alerts/config/<type>` → Sauvegarde config
- [ ] `POST /api/auth/login` → Authentification
- [ ] Pas d'erreur 404

## 📈 Performance

- [ ] Dashboard charge en < 3s
- [ ] Pas de timeout sur les endpoints
- [ ] CPU usage < 50%
- [ ] Memory usage < 200MB
- [ ] Pas d'erreur "504 Gateway Timeout"

## 🐛 Console Navigateur (F12)

- [ ] Pas d'erreur rouge
- [ ] Avertissements acceptables:
  - ✅ Eventlet deprecation (normal)
  - ✅ Certificat auto-signé (normal)
- [ ] Pas de 404 sur fichiers statiques

## 🔔 Notifications

### Telegram
- [ ] Peut tester: Modifiez score min à 50
- [ ] Attendez 2-3 signaux
- [ ] Reçus dans le canal Telegram

### Email (si configuré)
- [ ] SMTP credentials dans .env
- [ ] Pas d'erreur "530 Authentication required"

## 📝 Documentation

- [ ] Fichier TELEGRAM_ALERTS_GUIDE.md créé
- [ ] DEPLOYMENT.md mis à jour
- [ ] README.md accessible

---

## 🎯 Résultat Final

**Total Checks:** ___/60

**Status:**
- [ ] ✅ Tous passants → **Production Ready**
- [ ] ⚠️ 1-2 mineurs → **Ready (fix later)**
- [ ] ❌ > 2 critiques → **Fix required**

---

## 📞 Si quelque chose ne marche pas

1. **Ouvrez F12 → Console** et cherchez les erreurs rouges
2. **Notez l'endpoint** qui affiche 404/500
3. **Vérifiez les logs serveur:**
   ```bash
   sudo journalctl -u cryptoscanner -n 50 --no-pager
   ```
4. **Signalez avec:**
   - Erreur exacte
   - Endpoint concerné
   - Actions pour reproduire

---

**Checklist Version:** 1.0  
**Mise à jour:** 2026-05-10  
**Responsable:** DevOps Team
