---
projet: cryptoscanner
phase: en-cours
derniere-session: 2026-04-14
tags: [projet/cryptoscanner]
---

# CryptoScanner Pro — Contexte actif

## État courant
- Phase : Développement actif — chantiers idées.md (Whale Scanner livré, Portfolio/Watchlist opérationnel)
- Dernière session : 2026-04-14 18h00 — Fix inscription 500 + Whale Scanner + Fix Analyse Investisseur
- En cours : Tests prod Railway après redéploiement

## Stack technique
- Backend : Python 3.11, Flask, Flask-SocketIO
- Base de données : SQLite local / PostgreSQL prod (via `db.py` + `DATABASE_URL`)
- Déploiement : Railway (auto-deploy sur push GitHub) — URL : https://web-production-34b51.up.railway.app
- GitHub : https://github.com/lboute0433-prog/cryptoscanner (branche : `master`)
- IA : Groq (principal) + Anthropic (fallback) + OpenAI via `ai_provider.py`
- Frontend : HTML/CSS/JS dans `templates/`

## Décisions cumulées
- `db.py` : adapter PostgreSQL transparent — `get_connection()` partout, rollback dans les except
- **Auto-login inscription** : token retourné directement par `api_auth_register`, cookie cs_token posé
- **JS cfgRegister()** : si `d.token` → `showTab('settings')` après 600ms (Mon Compte)
- **Whale Scanner sans API payante** : `_detect_volume_whales()` (Binance, seuils par cap) + `_detect_btc_whales()` (mempool.space)
- **CoinGecko** : `_cg_headers()` centralisé + stale cache fallback sur 429 + `COINGECKO_API_KEY` env var supportée
- **Analyse Investisseur** : `loadInvestorPage()` implémentée, `invSearch()` normalisée, 429 affiché avec bouton Réessayer
- COT CFTC intégré dans Morning Brief (7 blocs Telegram, badge démo si API indisponible)
- Hero board : Fear&Greed + BTC Dominance + NASDAQ 24H + DXY Dollar
- **Telegram multi-niveaux** : `_broadcast_to_members(min_role)` + `get_members_by_role(min_role)`
- **Signal Retrace RSI** : `check_rsi_exit()` + `update_rsi_history()` + `build_retrace_alert()`
- **Canal FREE Telegram** : ID `-1003997628346`
- **Signaux anti-spam** : max 3/cycle, cooldown 1h, score min 85, filtre ADR ≥25% range 24h
- **MA20 + ADR** dans messages Telegram signaux
- **Sessions forex** : ZoneInfo("Europe/Paris") — Sydney 00-09, Tokyo 01-10, Londres 09-18, New York 15-23
- **Wallet Tracker Phase 1** : ETH/BTC/SOL via APIs gratuites dans page Whales
- Rôles : visitor(0) / member(1) / paid(2) / vip(3) / admin(4)
- Portfolio / Watchlist : tables + routes + UI déjà opérationnels

## Variables Railway configurées
- `TG_CHAT_FREE` = `-1003997628346`
- `SITE_URL` = `https://web-production-34b51.up.railway.app`
- À ajouter : `COINGECKO_API_KEY` (gratuit sur coingecko.com/api)

## Prochaines étapes
1. Ajouter `COINGECKO_API_KEY` dans Railway (gratuit, supprime les 429)
2. Tester inscription prod → redirection Mon Compte
3. Tester Analyse Investisseur prod → affichage données coin
4. Tester tab Whales → sections BTC on-chain + volume Binance
5. Wallet Tracker Phase 2 : wallets whales connus (Binance, Jump, a16z…)
6. Auto-refresh Whales toutes les 5 minutes
7. `technical_indicators.py` : centraliser RSI/EMA/ATR/Bollinger
