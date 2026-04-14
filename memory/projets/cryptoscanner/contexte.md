---
projet: cryptoscanner
phase: en-cours
derniere-session: 2026-04-14
tags: [projet/cryptoscanner]
---

# CryptoScanner Pro — Contexte actif

## État courant
- Phase : Développement actif — polish UI + Telegram FREE opérationnel + signaux avancés + Wallet Tracker
- Dernière session : 2026-04-14 14h00 — Fix 4 bugs (inscription, investor, forex, signaux Telegram)
- En cours : Railway redéploiement à vérifier (webhook potentiellement cassé)

## Stack technique
- Backend : Python 3.11, Flask, Flask-SocketIO
- Base de données : SQLite local / PostgreSQL prod (via `db.py` + `DATABASE_URL`)
- Déploiement : Railway (auto-deploy sur push GitHub) — URL : https://web-production-34b51.up.railway.app
- GitHub : https://github.com/lboute0433-prog/cryptoscanner (branche : `master`)
- IA : Groq (principal) + Anthropic (fallback) + OpenAI via `ai_provider.py`
- Frontend : HTML/CSS/JS dans `templates/`

## Décisions cumulées
- `db.py` : adapter PostgreSQL transparent — `get_connection()` partout
- COT CFTC intégré dans Morning Brief (7 blocs Telegram, badge démo si API indisponible)
- Hero board : Fear&Greed + BTC Dominance + NASDAQ 24H + DXY Dollar
- **Telegram multi-niveaux** : `_broadcast_to_members(min_role)` + `get_members_by_role(min_role)`
- **Signal Retrace RSI** : `check_rsi_exit()` + `update_rsi_history()` + `build_retrace_alert()`
- **Canal FREE Telegram** : ID `-1003997628346`
- **Bot /start** + **/lier** : opérationnels
- **Logos crypto** : `coinLogoHTML()` + CDN fallback
- **Historique Smart Signals** : table `signals_history` + route + UI filtrable
- **IA multi-providers** : Groq + Anthropic + OpenAI
- **Matrice permissions** : visitor/member/paid/admin par page
- **Paramètres Plateforme** : 4 settings seedés en DB (pump_pct=5, scan_interval=10, vol_mult=3, exchange=coingecko)
- **Auto-login inscription** : token retourné directement par `api_auth_register`
- **CROWDED POSITIONS** : try/catch isolé pour cross_analysis
- **Sessions forex** : ZoneInfo("Europe/Paris") — Sydney 00-09, Tokyo 01-10, Londres 09-18, New York 15-23
- **Wallet Tracker Phase 1** : ETH/BTC/SOL via APIs gratuites dans page Whales
- **Funding rate fix** : `_fetch_bybit_funding()` guard `fr != ""` + try/except par entrée
- **Signaux anti-spam** : max 3/cycle, cooldown 1h, score min 85, filtre ADR ≥25% range 24h
- **MA20 + ADR** dans messages Telegram signaux
- **Analyse Investisseur** : 🔍 cliquable (`onclick="invSearch()"`)
- Rôles : visitor(0) / member(1) / paid(2) / vip(3) / admin(4)

## Variables Railway configurées
- `TG_CHAT_FREE` = `-1003997628346`
- `SITE_URL` = `https://web-production-34b51.up.railway.app`

## Prochaines étapes
1. Vérifier Railway auto-deploy (reconnecter webhook si nécessaire)
2. Tester Analyse Investisseur en prod (vérifier rate-limit CoinGecko)
3. Ajuster `MAX_PER_CYCLE` et score min signaux selon observation prod
4. **Wallet Tracker Phase 2** : wallets whales connus (Binance, Jump, a16z…)
5. `technical_indicators.py` : centraliser RSI/EMA/ATR/Bollinger
6. Réfléchir au nouveau nom de la plateforme (marchés financiers au sens large)
7. PayPal webhook : après serveur dédié
