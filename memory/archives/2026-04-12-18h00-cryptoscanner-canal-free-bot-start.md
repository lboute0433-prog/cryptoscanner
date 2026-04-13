---
date: 2026-04-12
heure: "18:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-12 18h00 — CryptoScanner Canal FREE + Bot /start

## Résumé
Session axée sur la mise en place du canal Telegram public FREE et la refonte du bot Telegram. Ajout de `post_to_free_channel()`, réécriture complète de `/start` avec accueil professionnel, nouvelle commande `/lier` pour lier son Telegram à son compte site, et alertes PUMP/DUMP simplifiées postées automatiquement sur le canal FREE.

## Travail effectué

### `config.py` (session précédente, déjà archivé partiellement)
- Ajout `TELEGRAM_CHAT_FREE = os.environ.get("TG_CHAT_FREE", "")` — canal public FREE
- Ajout `SITE_URL = os.environ.get("SITE_URL", "https://cryptoscanner.pro")`

### `daily_report.py`
- Import `TELEGRAM_CHAT_FREE` + `SITE_URL` depuis `config`
- `post_to_free_channel(msg)` — fonction dédiée pour poster sur le canal public FREE
- `_post_daily_summary_to_free(engine)` — résumé de marché simplifié (sentiment, volume, top gains + lien site) posté chaque matin automatiquement après le rapport membre
- `/start` entièrement réécrit : accueil pro, distinction FREE vs PREMIUM, lien inscription, commandes, disclaimer légal
- `/lier` (+ `/link`, `/connect`) — nouvelle commande : affiche le Chat ID Telegram + instructions étape par étape pour lier à son compte site

### `scanner_engine.py`
- Import `TELEGRAM_CHAT_FREE` + `SITE_URL` depuis `config`
- Dans `_send_telegram_alerts` : après chaque alerte PUMP/DUMP (admin), poste une version simplifiée sur le canal FREE (variation + volume + teaser PREMIUM + lien site + disclaimer)

## Décisions

- **Canal FREE = marketing passif** : chaque alerte PUMP/DUMP poste automatiquement une version allégée sur le canal public pour attirer de nouveaux utilisateurs
- **Site = point d'entrée unique** : `/start` oriente vers le site pour créer un compte, le bot n'inscrit pas directement
- **`/lier` = pont Telegram ↔ site** : l'utilisateur inscrit sur le site copie son Chat ID Telegram dans son profil pour activer les alertes PREMIUM
- **Variables Railway** : `TG_CHAT_FREE` (ID numérique `-100...`) + `SITE_URL` à ajouter manuellement

## État du projet
- Phase actuelle : Développement actif — polish + features Telegram
- Validé : Canal FREE, `/start` pro, `/lier`, alertes PUMP/DUMP FREE, résumé journalier FREE
- En cours : Déploiement Railway (git push à faire par user + ajout variables)
- Pending : Créer le canal Telegram FREE sur l'app, récupérer son ID, ajouter les variables Railway

## Prochaines étapes
1. **Créer le canal Telegram FREE** → ajouter le bot comme admin → récupérer l'ID numérique
2. **Ajouter sur Railway** : `TG_CHAT_FREE` + `SITE_URL`
3. **git push** → déployer Railway
4. **Tester** : `/start`, `/lier`, alerte PUMP/DUMP sur canal FREE
5. **PayPal webhook** : `POST /webhooks/paypal` → passage auto paid (après serveur dédié)
6. **samedi.md item 5** : Portfolio Tracker / Wallet Scanner ON-CHAIN
7. **technical_indicators.py** : centraliser RSI/EMA/ATR/Bollinger (4 fichiers)
8. **Supprimer /api/perp doublon** + merger double call `market_info`

## Fichiers modifiés
- `config.py` — modifié (TELEGRAM_CHAT_FREE, SITE_URL)
- `daily_report.py` — modifié (imports, post_to_free_channel, _post_daily_summary_to_free, /start réécrit, /lier ajouté)
- `scanner_engine.py` — modifié (imports, alerte FREE dans _send_telegram_alerts)

## Assets (URLs)
Aucun.
