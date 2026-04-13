---
date: 2026-04-11
heure: "20:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-11 20h00 — CryptoScanner UI Fixes · Audit · Alertes Macro

## Résumé
Session de polish UI, correction de bugs frontend et implémentation de nouvelles features issues de la todo list `memory/notes/samedi.md`. 8 items traités couvrant des bugs (crowded positions, CVD), des améliorations UX (modals pédagogiques, Expert mode dynamique, Sources de données), un audit d'architecture complet, et des alertes Telegram macro automatiques.

## Travail effectué

### COT — Graphique tendance (finalisé depuis session précédente)
- HTML + CSS + JS `renderCOTChart()` injecté dans `templates/index.html`
- Dual Y-axis Chart.js, 8 semaines, onglets Tout/LF Net/AM Net/OI
- Appelé dans `loadCOT()` et `refreshCOT()` → mise à jour automatique

### Boutons info pédagogiques (?)
- **COT chart** : bouton `?` + modal overlay expliquant LF Net (contrarien), AM Net (directionnel), OI, lecture combinée
- **CVD page** : bouton `?` + modal overlay expliquant divergence haussière/baissière, source Bybit perpétuels

### Expert Mode — Blocs statiques supprimés, données live
- Supprimé `desk-ribbon` et `insight-grid` (contenu marketing statique inutile)
- Remplacé par `expert-live-grid` : 4 cartes dynamiques (Fear&Greed + label emoji, BTC Dominance, Prochain event 🔴 + countdown, Market Cap Total)
- Alimentées automatiquement depuis `updateMacroUI()` et `loadDashCalendar()`

### Calendrier macro — Corrections majeures
- **Bug matching FR/EN** : `_merge_forexfactory_actuals()` échouait car "Inscriptions chômage" ≠ "Initial Jobless Claims"
  → Ajout `FF_TITLE_KEYWORDS` (12 paires FR/EN) + `_titles_match_ff()` avec matching sémantique
- **Cache actuals** : `ECON_ACTUAL_CACHE` persiste maintenant les résultats en session
- **Lookback étendu** : `_recent_releases` passe de 3 → 7 jours
- **Dashboard "Dernières Stats"** : rendu unifié (withActual → upcoming → pastNoActual), plus jamais de div vide
- **Calendrier pleine page** : colonne "Actuel" différencie valeur publiée / ⏳ En cours / N/D ⓘ (avec tooltip explication RSS limité semaine courante)
- **Source ForexFactory** : affichée en vert dans le sous-titre de l'événement

### Bug Crowded Positions (item 7)
- **Bug** : Python stockait `"symbol": "BTC"` (sans USDT) mais JS filtrait `['BTCUSDT','ETHUSDT','SOLUSDT']` → 0 match → div vide
- **Fix** : filtre JS corrigé sur symboles courts `['BTC','ETH','SOL','BNB','XRP','DOGE','ADA']`, top 5 par funding rate

### CVD — 12 cryptos (item 8)
- Dropdown étendu de 3 à 12 cryptos : BTC ETH SOL BNB XRP DOGE ADA AVAX DOT LINK LTC MATIC
- Modal explicatif CVD ajouté

### Sources de données (item 6)
- Ancien bloc : 4 boutons qui semblaient interactifs mais `setExchange()` retournait immédiatement (fake UI)
- Nouveau bloc : tableau de statut honnête avec 5 sources (CoinGecko/Binance/Bybit/ForexFactory+CFTC/Kraken), rôle précis, badge statut (● ACTIF / ◑ HEBDO / ○ INACTIF)

### Alertes Telegram macro auto (item 2)
- Nouvelle fonction `send_macro_alert_telegram(event)` dans `news_macro.py`
- Route `POST /api/macro/calendar/check-results` dans `app.py`
- Intégration dans `macro_loop()` : check automatique toutes les 5 min entre 7h-22h UTC
- Déduplication via `_sent_macro_alerts` set (reset au-delà de 200 entrées)
- Bouton manuel "📡 Alertes macro" sur la page Calendrier + feedback JS

### Audit doublons architecture (item 3)
- RSI calculé **4 fois** identique (scanner, smart_signals, backtest, forex)
- EMA/Bollinger/ATR dupliqués 2-3× chacun
- `/api/perp` = `/api/bybit/perp` (routes jumelles)
- `/api/market_info` appelé 2× au démarrage
- Bybit/OKX spot+perp+multi_exchange tous appelés ensemble
- Funding rate Binance + Bybit en doublon
- **Recommandation validée** : créer `technical_indicators.py`, supprimer `/api/perp`, merger fetch market_info

## Décisions

- **Matching FR/EN** via mots-clés plutôt que préfixe titre : les titres internes sont en français, ForexFactory en anglais — le matching par préfixe était structurellement voué à l'échec
- **Expert mode live** : contenu statique = perte de confiance utilisateur → remplacement par vraies données
- **Buttons Sources de données honnêtes** : afficher le statut réel, pas une fausse interactivité
- **Alertes macro automatiques** dans `macro_loop` : évite la dépendance à un clic utilisateur, s'auto-nettoie
- **Audit architecture** délégué à un agent Explore : rapport précis avec numéros de lignes

## État du projet
- Phase actuelle : Développement actif — polish UI + features reporting
- Validé : Bugs crowded + CVD + calendrier corrigés, modals pédagogiques, alertes Telegram auto
- En cours : Déploiement Railway (git push effectué par user en fin de session)
- Pending : Fixes audit priorité 1 (technical_indicators.py, /api/perp doublon, market_info double call)

## Prochaines étapes
1. **Vérifier le déploiement Railway** : crowded positions, CVD, dashboard stats, alertes Telegram
2. **Fixes audit priorité 1** : `technical_indicators.py` central + supprimer `/api/perp` + merger market_info
3. **Portfolio Tracker / Wallet Scanner** (item 5) : décision page Whales enrichie ou nouvelle page ON-CHAIN
4. **Activer PostgreSQL Railway** : plugin Railway → `DATABASE_URL` auto-injectée
5. **Smart Signals small caps** : `MIN_VOLUME_USD = 500_000` si user veut voir RAVE-style

## Fichiers modifiés
- `templates/index.html` — modifié (COT chart, modals COT+CVD, Expert mode live, crowded fix, CVD 12 cryptos, sources données, calendar rendering, dashboard stats, Telegram button)
- `news_macro.py` — modifié (FF_TITLE_KEYWORDS, _titles_match_ff, _merge_forexfactory_actuals, _recent_releases lookback 7j, ECON_ACTUAL_CACHE persistance, send_macro_alert_telegram)
- `app.py` — modifié (_sent_macro_alerts, route check-results, macro_loop auto-check)
- `memory/notes/samedi.md` — lu (todo list source)

## Assets (URLs)
Aucun.
