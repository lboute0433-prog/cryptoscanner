# CryptoScanner Pro V11 — Documentation Complète

**Dernière mise à jour :** 28 Mars 2026  
**Version :** V11  
**URL Railway :** https://web-production-34b51.up.railway.app  
**GitHub :** dépôt privé connecté à Railway

---

## 🏗️ Architecture

### Stack technique
- **Backend :** Python 3.11 + Flask + Flask-SocketIO (eventlet sur Railway)
- **Frontend :** HTML/CSS/JS — dark cyber theme (Orbitron)
- **Base de données :** SQLite (`cryptoscanner.db`)
- **Déploiement :** Railway.app (auto-redéploiement via GitHub push)
- **Local :** `lancer.bat` → `python app.py`

### Fichiers clés
```
app.py                  # Flask principal + routes API (1377 lignes)
scanner_engine.py       # Moteur scan CoinGecko/Binance/Kraken
news_macro.py           # News RSS FR + calendrier macro économique
cot_engine.py           # COT CFTC + ETF flows + CoinGlass + liquidations
daily_report.py         # Rapport Telegram + bot + abonnés
smart_signals.py        # Signaux multi-critères RSI/MACD/Volume
backtest_engine.py      # Backtesting 5 stratégies
forex_engine.py         # Forex 26 paires + sessions + corrélations DXY
indices_engine.py       # SP500/VIX/CAC40/Bybit/OKX + Market Mood Score
security.py             # bcrypt + Fernet AES-256 + TOTP Google Auth
lexique.py              # Glossaire trading 25+ termes
debloquer_admin.py      # Script utilitaire déblocage admin
wsgi.py                 # Entry point gunicorn Railway
templates/index.html    # Interface frontend (6200+ lignes)
templates/admin.html    # Page administration
```

---

## 🌐 Déploiement Railway

### Variables d'environnement (Railway → Variables)
```
TG_TOKEN=ton_token_telegram
TG_CHAT=ton_chat_id
REPORT_HOUR=8
RUN_BACKGROUND_JOBS=true
SECRET_KEY=une_cle_flask_stable
```

### Commande de démarrage (Procfile)
```
web: gunicorn --worker-class eventlet -w 1 --timeout 120 --bind 0.0.0.0:$PORT wsgi:application
```

### Healthcheck
- Route : `/health` → liveness HTTP tolérant pour Railway
- Route : `/ready` → vérifie la base et l'état métier minimal
- Timeout : 300 secondes
- `railway.json` configuré avec `healthcheckPath: "/health"`

### Workflow de mise à jour
```
1. Télécharger le ZIP depuis Claude
2. Uploader les fichiers sur GitHub (remplacer les anciens)
3. Railway redéploie automatiquement en 2-3 minutes
```

---

## 📦 Sources de données

### Sources principales
| Source | Usage | Limite gratuite |
|--------|-------|-----------------|
| **CoinGecko** | Scan principal (top 250 coins) | ~30 req/min → scan toutes les 90s |
| **Binance Futures** | Perp, Funding rates, Open Interest | Illimité (public) |
| **Kraken** | Alternative exchange spot | Illimité (public) |
| **CFTC** | Données COT officielles (hebdo, vendredi) | Illimité (public) |
| **CoinGlass** | Long/Short ratio, liquidations, OI multi-ex | Limité sans clé |
| **Yahoo Finance** | Indices SP500/VIX/CAC40/Or/Pétrole/DXY | Limité (2 tentatives) |
| **Alternative.me** | Fear & Greed Index | Illimité |
| **Frankfurter** | Forex 26 paires | Illimité |
| **RSS FR** | News crypto françaises | Illimité |

### Sources RSS News (FR uniquement)
1. CoinTelegraph FR — `https://fr.cointelegraph.com/rss`
2. Cryptoast — `https://cryptoast.fr/feed/`
3. Journal du Coin — `https://journalducoin.com/feed/`
4. Coinactu — `https://coinactu.com/feed/`
5. The Coin Tribune — `https://thecointribune.com/feed/`

---

## 🤖 Bot Telegram

### Commandes disponibles
| Commande | Description |
|----------|-------------|
| `/rapport` | Rapport journalier complet (Or, Forex, Indices, Crypto) |
| `/etf` | Flux ETF Bitcoin du jour |
| `/news` | Dernières news FR |
| `/backtest BTC rsi 1h` | Backtest rapide avec résultats |
| `/subscribe` | S'abonner aux alertes automatiques |
| `/aide` | Liste toutes les commandes |

### Commandes admin
| Commande | Description |
|----------|-------------|
| `/subscribers` | Liste des abonnés |
| `/approve [chat_id]` | Approuver un abonné |
| `/reject [chat_id]` | Refuser un abonné |
| `/broadcast [msg]` | Message à tous les abonnés |

### Alertes automatiques (broadcast à tous les abonnés)
- 🚀 Pump/Dump (score signal ≥ 80)
- 📊 Rapport COT hebdomadaire (vendredi)
- 📅 Événements macro importants (FOMC, CPI, NFP)
- 🔔 Alertes prix personnalisées

---

## 🗺️ Navigation de l'application

### Menu principal
- **DASHBOARD** — Vue globale + Market Mood + News critiques + Calendrier + Top gains
- **ANALYSE** → COT, Marché, Signaux, Heatmap, Smart Signals
- **DATA** → Macro, News FR, Whales, Watchlist
- **MARCHÉS** → Forex, Indices, Multi-Exchange (Bybit/OKX), Market Mood
- **TRADING** → Portfolio, Journal, Alertes prix, Backtest
- **OUTILS** → Calculateur TP/SL, Config, Lexique, IA Analyste, Exchange

### Navigation mobile
- Bottom bar fixe avec 5 boutons + sous-menus
- Responsive CSS complet (768px breakpoint)

---

## 📊 Fonctionnalités détaillées

### COT (Commitment of Traders)
- **Source :** API CFTC publique (gratuite, sans clé)
- **Fréquence :** Rapport publié chaque **vendredi soir** (données du mardi)
- **Codes CFTC :** BTC=133741, ETH=146021, SP500=13874, Or=088691
- **Analyse automatique :** Signal HAUSSIER/BAISSIER/NEUTRE basé sur :
  - Asset Managers (suivre leur direction)
  - Leveraged Funds (signal contrarien — hedge funds ont souvent tort aux extrêmes)
  - Open Interest (nouveaux capitaux entrant ou sortant)
- **Affichage :** RÉEL vs DÉMO clairement indiqué
- **Fallback :** Données démo si API CFTC indisponible

### CoinGlass (données gratuites récupérées)
- Long/Short ratio (Binance Futures public)
- Liquidations 24h multi-coins (BTC, ETH, SOL, BNB, XRP)
- Open Interest multi-exchange (Binance, Bybit, OKX, Deribit)
- Routes : `/api/longshort/<symbol>`, `/api/liquidations/heatmap`, `/api/oi/multiexchange`

### Market Mood Score (0-100)
Combinaison de : VIX + Fear&Greed + DXY + SP500 + Funding rates
- **0-35** 🔴 Risk-OFF — Réduire l'exposition
- **35-65** 🟡 Prudence — Neutre
- **65-100** 🟢 Risk-ON — Favorable aux cryptos
Affiché directement sur le **Dashboard** (widget compact) + page dédiée

### Backtest Engine (5 stratégies)
| ID | Stratégie | Description |
|----|-----------|-------------|
| `rsi_reversal` | RSI Reversal | Achat RSI < 30, Vente RSI > 70 |
| `ema_crossover` | EMA Crossover | Croisement EMA 9/21 |
| `bollinger` | Bollinger Bands | Rebond sur bandes (20/2.0) |
| `macd` | MACD Signal | Croisement MACD/Signal (12/26/9) |
| `smart` | Smart Signal | Multi-critères RSI+BB+EMA+Volume |

Métriques : PnL%, Win Rate, Sharpe Ratio, Max Drawdown, Profit Factor
Données : Binance Klines (jusqu'à 1000 bougies)

### Alertes Prix
1. TRADING → ALERTES → Ajouter symbole + condition + prix cible
2. Scan vérifie à chaque cycle (90 sec avec CoinGecko)
3. Si atteint → Telegram envoyé + alerte désactivée
4. Token Telegram rechargé dynamiquement depuis `os.environ`

---

## 🔐 Sécurité

### Authentification
- bcrypt pour hashing des mots de passe
- Sessions avec tokens sécurisés (24h d'expiration)
- **2FA TOTP** (Google Authenticator / Authy)
- **2FA Telegram** (alternative)
- Déconnexion automatique après **30 min d'inactivité**
- Rate limiting (5 tentatives de connexion max)

### TOTP Google Authenticator
1. CONFIG → Double Authentification → Activer Google Authenticator
2. Scanner le QR Code avec Google Authenticator ou Authy
3. Entrer le code à 6 chiffres pour confirmer
4. 10 codes de secours générés (usage unique)

### Inscription
- Prénom, Nom, Email (optionnel), Username, Mot de passe
- Indicateur de force du mot de passe (5 niveaux)
- Validation format email
- Stockage local uniquement (pas de serveur tiers)

---

## 🐛 Bugs résolus (historique)

| Date | Bug | Solution |
|------|-----|---------|
| Mar 2026 | `engine is not defined` JS | `engine` est Python — remplacé par `window._lastMarket` |
| Mar 2026 | `showTab not defined` au chargement | Stub function ajoutée avant le header |
| Mar 2026 | Accolade manquante `loadNews()` | `}` ajouté après `.join('')` |
| Mar 2026 | `/api/cot_sp500` 404 | Routes alias ajoutées dans app.py |
| Mar 2026 | Heatmap vide | CoinGecko rate limit → scan toutes les 90s |
| Mar 2026 | Fear&Greed vide dashboard | `updateMacroUI` met à jour `dash-fg` ET `fg-val` |
| Mar 2026 | Alertes Telegram pas reçues | Token rechargé dynamiquement depuis `os.environ` |
| Mar 2026 | Healthcheck failure Railway | Route `/health` + démarrage des boucles différé de 1s |
| Mar 2026 | Threading incompatible Railway | `socketio.start_background_task()` sur Railway, `threading` en local |
| Mar 2026 | "fermant -->" visible | Texte parasite supprimé du HTML |
| Mar 2026 | `protect_all` bloquait tout | Protection HTTP Basic supprimée de app.py |

---

## ⚠️ Limitations connues

- **Railway gratuit :** 500h/mois (~20 jours) → passer Hobby 5$/mois pour 24h/24
- **CoinGecko gratuit :** Rate limit → scan toutes les 90 sec (pas temps réel)
- **COT CFTC :** Données avec 4-5 jours de retard (rapport vendredi, données du mardi)
- **COT BTC/ETH :** Uniquement les futures CME (institutionnels US), pas Binance
- **CoinGlass sans clé :** Certains endpoints peuvent être bloqués → fallback Binance
- **Yahoo Finance :** Parfois indisponible → données DEMO affichées pour les indices
- **SQLite :** Remis à zéro à chaque redéploiement Railway (base de données éphémère)

---

## 🚀 Prochaines améliorations planifiées

- [ ] Persistance SQLite sur Railway (volume ou PostgreSQL)
- [ ] Alertes prix avec répétition configurable
- [ ] Intégration TradingView webhooks
- [ ] Dashboard personnalisable (widgets déplaçables)
- [ ] Historique des prix dans le portfolio (courbe PnL)
- [ ] Notifications push navigateur (PWA)
- [ ] Amélioration Smart Signals avec ML

---

## 📱 Accès

| Plateforme             | URL                                         |
| ---------------------- | ------------------------------------------- |
| **En ligne (Railway)** | https://web-production-34b51.up.railway.app |
| **Local PC**           | http://localhost:5000                       |
| **Mobile même réseau** | http://[IP-PC]:5000                         |
| **Admin**              | /admin                                      |

**Credentials par défaut (local) :**  
Username: `admin` | Password: `cryptoscanner`  
*(Changer dans CONFIG → Créer un compte)*
