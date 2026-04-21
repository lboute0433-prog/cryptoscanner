---
date: 2026-04-14
heure: "18:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-14 18h00 — CryptoScanner Whale Scanner + Fix Inscription + Fix Investisseur

## Résumé
Session de correctifs critiques et chantier Whale Scanner. Le bug inscription 500 (NameError `get_connection` + rollback PostgreSQL manquant) a été entièrement résolu. La page Analyse Investisseur a été réparée (loadInvestorPage vide, normalisation invSearch, gestion 429 CoinGecko). Le Whale Scanner produit maintenant des données réelles sans API payante (volume Binance + BTC on-chain via mempool.space).

## Travail effectué
- Ajout de `from db import get_connection` manquant dans `app.py` (NameError → 500 inscription)
- `scanner_engine.py` `create_user()` : ajout `conn.rollback()` avant `conn.close()` dans le except (crash PostgreSQL InFailedSqlTransaction)
- `db.py` : sécurisation setter `row_factory` avec `hasattr` check sur psycopg2.extensions
- `app.py` : blocs `try/except` individuels sur tous les appels DB post-inscription (log_action, save_exchange_keys, create_session) — 500 impossible même si DB plante après insertion
- JS `cfgRegister()` vérifié : gère `d.token` → `showTab('settings')` après 600ms
- `scanner_engine.py` : ajout `_detect_volume_whales()` — anomalies volume Binance (large/mid/small cap avec seuils différenciés)
- `scanner_engine.py` : ajout `_detect_btc_whales()` — gros transferts BTC via mempool.space (sans API key)
- `scanner_engine.py` `fetch_whale_alerts()` : fallback sur les deux méthodes si pas de WHALE_API_KEY
- `templates/index.html` `loadWhales()` : refonte affichage — 2 sections distinctes (BTC On-Chain / Anomalies Volume Binance), badges colorés par cap, direction PUMP/DUMP
- `templates/index.html` `loadInvestorPage()` : implémentée (était vide → rien ne s'affichait au chargement tab)
- `templates/index.html` `invSearch()` : normalisation robuste (normalize NFD, nettoyage regex)
- `templates/index.html` `invLoad()` : code `__rate_limit__:<coinId>` sur 429, message utilisateur + bouton Réessayer
- `app.py` : `_cg_headers()` centralisé avec `COINGECKO_API_KEY` env var + fallback stale cache sur 429

## Décisions
- **Whale Scanner sans API payante** : Binance volume anomaly + mempool.space BTC suffisent pour un MVP utile, pas besoin de Whale Alert ($299/mois)
- **Fallback stale cache CoinGecko** : en cas de 429, servir les données en cache même périmées plutôt qu'une erreur — meilleure UX
- **Agents parallèles** : Debugger et Feature lancés en parallèle pour gain de temps

## État du projet
- Phase actuelle : Développement actif — chantiers idées.md en cours
- Validé : Inscription OK, Whale Scanner opérationnel, Analyse Investisseur réparée, Portfolio/Watchlist déjà opérationnel
- En cours : Tests prod Railway à valider après redéploiement

## Prochaines étapes
1. Ajouter `COINGECKO_API_KEY` (gratuit) dans variables Railway → supprime les 429 définitivement
2. Tester inscription en prod avec nouveau compte → vérifier redirection Mon Compte
3. Tester Analyse Investisseur en prod → vérifier affichage données coin
4. Tester tab Whales → vérifier sections BTC on-chain + volume Binance
5. Wallet Tracker Phase 2 : wallets whales connus (Binance cold wallet, Jump, a16z…)
6. Auto-refresh Whales toutes les 5 minutes (setInterval)
7. `technical_indicators.py` : centraliser RSI/EMA/ATR/Bollinger

## Fichiers modifiés
- `app.py` — modifié (import get_connection, _cg_headers, blocs try/except post-inscription, fallback stale cache)
- `scanner_engine.py` — modifié (_detect_volume_whales, _detect_btc_whales, fetch_whale_alerts fallback, rollback create_user)
- `templates/index.html` — modifié (loadWhales refonte, loadInvestorPage, invSearch normalization, 429 handling)
- `db.py` — modifié (setter row_factory sécurisé)

## Assets (URLs)
- Railway : https://web-production-34b51.up.railway.app
- GitHub : https://github.com/lboute0433-prog/cryptoscanner
