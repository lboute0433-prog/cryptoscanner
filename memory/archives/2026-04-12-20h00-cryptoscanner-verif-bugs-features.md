---
date: 2026-04-12
heure: "20:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-12 20h00 — CryptoScanner Verif.md — Bugs + Features

## Résumé
Session de traitement complet du fichier verif.md : correction de 3 bugs bloquants, ajout de 5 features majeures. Toutes les modifications portent sur `templates/index.html`, `app.py`, `scanner_engine.py` et `ai_provider.py`.

## Travail effectué

### Bug #6 — Création de compte : pas de redirection
- Auto-login immédiat après inscription réussie via `cfgRegister()`
- Login avec les credentials saisis → `cfgUpdateProfile()` + `showTab('settings')`
- Fallback : bascule onglet Login avec username pré-rempli si auto-login échoue

### Bug #1 — Tri colonnes page Signaux cassé
- Ajout `onclick="sortSignals('...')"` sur SYMBOLE, PRIX $, VAR 24H, VOLUME $, SCORE
- Nouvelle variable `signalSortKey / signalSortDir` + fonction `sortSignals(key)` + tri dans `renderSignals()`
- Indicateur visuel ▼/▲ sur la colonne active

### Bug #3 — CVD Flow : tableau défilant buggé
- Header `position:sticky;top:0` → reste visible au scroll
- Container `overflow-y:auto` sans padding parasite
- Hauteur portée à 260px

### Feature #9 — Bloc "Accès limité" dynamique selon le rôle
- Badge dynamique : 🔒 MEMBRES UNIQUEMENT / 💎 PREMIUM REQUIS / ⭐ VIP REQUIS / 🔐 ADMIN UNIQUEMENT
- Message contextuel selon rôle actuel + rôle requis (invitation inscription, upgrade, contacter admin)
- Bouton "Voir les offres" masqué pour `admin`

### Feature #2b — Historique Smart Signals
- Table `signals_history` dans SQLite (symbol, direction, score, price, change_pct, volume_usdt, tags, criteria, ts)
- Sauvegarde auto dans `smart_signal_loop` (signaux score ≥ 50)
- Route `GET /api/smart_signals/history?limit&direction&symbol`
- Bloc HTML dans page Smart Signals : tableau scrollable 320px, header sticky, 7 colonnes
- Filtre direction (select) + filtre symbole (input + debounce 300ms)
- Clic ligne → `openChart(symbol)` popup graphique
- Rafraîchissement auto à chaque `smart_signals_update` WebSocket

### Feature #2a — Lien TradingView dans popup graphique
- Bouton "📺 Ouvrir sur TradingView" dans le header du `chart-modal`
- `href` mis à jour dynamiquement dans `openChart(sym)` → `BINANCE:{SYM}USDT`
- Fonctionne depuis tous les points d'entrée (heatmap, spot, perp, signaux, watchlist, historique)

### Feature #8 — Logos crypto devant les symboles
- `coinLogos {}` map global symbol → URL, alimenté via `_buildLogoMap(coins)` à chaque market update
- `coinLogoHTML(symbol, size)` : `<img>` avec fallback CDN cryptocurrency-icons, `onerror` silencieux
- Logos injectés : Marché Spot, Signaux, Heatmap, Smart Signals cards, Historique Signaux, Perp, CoinGecko, Watchlist, popup graphique titre

### Feature #5 — IA Personnelle multi-providers
- `ai_provider.py` : support OpenAI ajouté (`gpt-4o-mini`), `_pick_provider` étendu (groq → anthropic → openai)
- Route `POST /api/auth/api_keys` : accepte `openai` comme provider valide
- Route `GET /api/auth/api_keys` : retourne statut Groq + Anthropic + OpenAI séparément
- Frontend : 3 boutons provider ⚡ Groq / 🧠 Anthropic / 🤖 OpenAI + badges ✓ si configuré
- Bouton `?` : modal étape par étape avec liens directs consoles + navigation inter-providers
- Auto-détection provider par préfixe clé (`gsk_` → Groq, `sk-ant-` → Anthropic, `sk-` → OpenAI)

### Feature #7 — Matrice des permissions par page
- Nouvelles règles : `smart` → paid, `whales`/`forex`/`indices`/`mood` → member
- Badges visuels 💎 PAID et 🔒 MEMBRE sur les boutons de navigation
- Matrice complète documentée dans `TAB_ACCESS_RULES`

## Décisions

- **Smart Signals → paid** : le teaser gratuit reste dans la page Signaux (basique), les Smart Signals (multi-critères, score, patterns) sont réservés paid
- **Whales → member** : données de valeur, pas public
- **Forex/Indices/Mood → member** : cohérent avec la valeur ajoutée
- **Logos CDN** : `cdn.jsdelivr.net/gh/ErikThiart/cryptocurrency-icons` (repo GitHub ~1000 logos), `onerror` silencieux si absent
- **Historique signaux** : seuil score ≥ 50 pour éviter le bruit

## État du projet
- Phase actuelle : Développement actif — polish + features Telegram + signaux avancés
- Validé : 3 bugs corrigés + 5 features majeures (verif.md items 1, 2a, 2b, 3, 5, 6, 7, 9)
- Restant verif.md : #4 (explication admin paramètres), #10 (marchés dimanche — vérif logique), #11 (Arkham — grand chantier)
- En cours : Déploiement Railway (git push à faire)

## Prochaines étapes
1. **git push** → déployer Railway
2. **Créer canal Telegram FREE** → `TG_CHAT_FREE` + `SITE_URL` dans Railway
3. **verif.md #4** : lire bloc paramètres admin + expliquer fonctionnement
4. **verif.md #10** : vérifier logique marchés ouverts week-end
5. **verif.md #11** : Arkham — réflexion Portfolio Tracker on-chain (samedi.md item 5)
6. **technical_indicators.py** : centraliser RSI/EMA/ATR/Bollinger (4 fichiers)
7. **PayPal webhook** : après serveur dédié

## Fichiers modifiés
- `templates/index.html` — modifié (bugs, features, permissions, logos, historique, IA, TradingView)
- `app.py` — modifié (route history, sauvegarde signals_history, api_keys OpenAI)
- `scanner_engine.py` — modifié (table signals_history dans init DB)
- `ai_provider.py` — modifié (support OpenAI, _pick_provider étendu)

## Assets (URLs)
Aucun.
