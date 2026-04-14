---
date: 2026-04-14
heure: "14:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-14 14h00 — CryptoScanner Fix 4 bugs (inscription, investor, forex, signaux)

## Résumé
Session de correction des 4 bugs listés dans `memory/agents/debugger/notes.md`.
Tous les fixes ont été commités et pushés sur `master` → Railway redéploiement en attente (webhook à vérifier).

## Travail effectué
- **Bug #1** : Création de compte ne redirige pas vers Mon Compte — `api_auth_register` retourne maintenant un token de session directement, suppression du second appel login fragile
- **Bug #2** : Page Analyse Investisseur — icône 🔍 non cliquable → ajout `onclick="invSearch()"` + `cursor:pointer`
- **Bug #3** : Horaires marchés Paris/New York incorrects — `datetime.now()` (UTC) remplacé par `datetime.now(ZoneInfo("Europe/Paris"))`, heures corrigées (Londres 09-18, New York 15-23)
- **Bug #4** : Telegram signaux spam — max 3 alertes/cycle, cooldown 1h, score min 85, filtre ADR (≥25% du range 24h), MA20 + ADR ajoutés dans le message

## Décisions
- **Token direct depuis register** : évite la double requête et les race conditions
- **ADR threshold** : `max(PUMP_PRICE_PCT, adr_pct * 0.25)` — s'adapte à la volatilité du coin
- **MAX_PER_CYCLE = 3** : anti-burst conservative, peut être ajusté dans `app.py`
- **Score min 85** : réduit les faux positifs, garder 90 en option si encore trop de bruit
- **Overlap London/NY** recalé à 17h-18h Paris (était 14h-17h UTC)

## État du projet
- Phase actuelle : Développement actif
- Validé : 4 bugs corrigés + pushés (commits `97728af`, `684ce1f`, `5ba6ffd`)
- En cours : Railway redéploiement à vérifier (webhook potentiellement cassé)

## Prochaines étapes
1. Vérifier Railway auto-deploy (reconnecter webhook si nécessaire)
2. Tester Bug #2 en prod : recherche Analyse Investisseur (vérifier rate-limit CoinGecko aussi)
3. Ajuster `MAX_PER_CYCLE` et score min selon observation en prod
4. **Wallet Tracker Phase 2** : wallets whales connus (Binance, Jump, a16z…)
5. `technical_indicators.py` : centraliser RSI/EMA/ATR/Bollinger
6. Réfléchir au nouveau nom de la plateforme (marchés financiers au sens large)

## Fichiers modifiés
- `app.py` — `api_auth_register` retourne token+cookie ; `_send_smart_alerts` anti-spam
- `templates/index.html` — `cfgRegister()` utilise token direct ; 🔍 `onclick="invSearch()"`
- `forex_engine.py` — import ZoneInfo, `_PARIS`, `datetime.now(_PARIS)`, heures sessions corrigées
- `smart_signals.py` — ADR filter, MA20 (calc_ema), enrichissement message Telegram

## Assets (URLs)
- Prod : https://web-production-34b51.up.railway.app
- GitHub : https://github.com/lboute0433-prog/cryptoscanner (branche `master`)
