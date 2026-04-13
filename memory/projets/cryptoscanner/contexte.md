---
projet: cryptoscanner
phase: en-cours
derniere-session: 2026-04-12
tags: [projet/cryptoscanner]
---

# CryptoScanner Pro — Contexte actif

## État courant
- Phase : Développement actif — polish UI + Telegram FREE opérationnel + signaux avancés
- Dernière session : 2026-04-12 22h00 — verif.md #4 : explication Paramètres Plateforme admin
- En cours : git push Railway + variables TG_CHAT_FREE + SITE_URL à confirmer

## Stack technique
- Backend : Python 3.11, Flask, Flask-SocketIO
- Base de données : SQLite local / PostgreSQL prod (via `db.py` + `DATABASE_URL`)
- Déploiement : Railway (auto-deploy sur git push) — URL : https://web-production-34b51.up.railway.app
- IA : Groq (principal) + Anthropic (fallback) + OpenAI (nouveau) via `ai_provider.py`
- Frontend : HTML/CSS/JS dans `templates/`

## Décisions cumulées
- `db.py` : adapter PostgreSQL transparent — `get_connection()` partout
- Fail-hard si `cryptography` ou `bcrypt` manquants au démarrage
- COT CFTC intégré dans Morning Brief (7 blocs Telegram, badge démo si API indisponible)
- Hero board : Fear&Greed + BTC Dominance + NASDAQ 24H + DXY Dollar
- Hero Market Strip : BTC/ETH/SOL/BNB prix live
- TOP 5 GAINS/PERTES : colonnes min-width, style STABLECOINS
- Expert mode : ETH/BTC Ratio + Volume 24H
- **Telegram multi-niveaux** : `_broadcast_to_members(min_role)` + `get_members_by_role(min_role)`
- **Signal Retrace RSI** : `check_rsi_exit()` + `update_rsi_history()` + `build_retrace_alert()`
- **Disclaimer légal** : uniformisé partout
- **Canal FREE Telegram** : `post_to_free_channel()` + alertes PUMP/DUMP simplifiées + résumé journalier — ID `-1003997628346`
- **Bot /start** : accueil pro, FREE vs PREMIUM, lien inscription
- **Bot /lier** : affiche Chat ID + instructions liaison compte site
- **Logos crypto** : `coinLogoHTML()` + CDN fallback, injectés dans tous les tableaux + popup
- **Historique Smart Signals** : table `signals_history` + route `/api/smart_signals/history` + bloc UI filtrable
- **IA multi-providers** : Groq + Anthropic + OpenAI — dropdown + bouton `?` procédure
- **Matrice permissions** : visitor/member/paid/admin par page (Smart Signals → paid, Whales/Forex/Indices/Mood → member)
- **TradingView popup** : bouton dans chart-modal, href dynamique par symbol
- **Tri colonnes Signaux** : sortSignals() + indicateurs ▼/▲
- **CVD Flow** : header sticky + overflow propre
- **Inscription → redirection** : auto-login + showTab('settings')
- **Bloc Accès Limité** : messages dynamiques selon rôle requis vs rôle actuel
- **Paramètres Plateforme** : 4 settings en table SQLite (pump_pct=5, scan_interval=10, vol_mult=3, exchange=coingecko) via `_get_setting`/`_set_setting`
- Rôles : visitor(0) / member(1) / paid(2) / vip(3) / admin(4)

## Variables Railway à configurer
- `TG_CHAT_FREE` = `-1003997628346`
- `SITE_URL` = `https://web-production-34b51.up.railway.app` (changer quand domaine cryptoscanner.pro actif)

## verif.md — État
- ✅ #1 : Tri colonnes signaux
- ✅ #2a : TradingView popup
- ✅ #2b : Historique Smart Signals
- ✅ #3 : CVD Flow tableau
- ✅ #4 : Paramètres Plateforme admin — expliqué
- ✅ #5 : IA multi-providers
- ✅ #6 : Inscription → redirection Mon Compte
- ✅ #7 : Matrice permissions
- ✅ #8 : Logos crypto
- ✅ #9 : Bloc Accès Limité dynamique
- **#10** : Marchés ouverts week-end — à vérifier (logique ou bug ?)
- **#11** : Arkham Intelligence — grand chantier (lié samedi.md item 5)

## Prochaines étapes
1. **git push** → vérifier déploiement Railway
2. **Variables Railway** : `TG_CHAT_FREE` + `SITE_URL`
3. **verif.md #10** : logique marchés ouverts week-end
4. **verif.md #11** : Arkham — réflexion Portfolio Tracker on-chain
5. **technical_indicators.py** : centraliser RSI/EMA/ATR/Bollinger (4 fichiers)
6. **PayPal webhook** : après serveur dédié
