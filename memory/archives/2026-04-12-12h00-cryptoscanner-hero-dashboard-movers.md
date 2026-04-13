---
date: 2026-04-12
heure: "12:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---
/
# Session 2026-04-12 12h00 — CryptoScanner Hero · Dashboard · Top Movers

## Résumé
Session de polish dashboard axée sur ce que les investisseurs voient en premier coup d'œil. Refonte du hero (4 cartes utiles), suppression des doublons dans le bloc Expert, uniformisation des TOP 5 GAINS/PERTES au format STABLECOINS, et ajout d'un strip de prix live BTC/ETH/SOL/BNB en bas du hero.

## Travail effectué

### Hero metric board — 4 nouvelles cartes
- **Supprimé** : SCORE ADN MARCHE + SIGNAUX ACTIFS (peu lisibles au premier regard)
- **Ajouté** : NASDAQ 24H (`dash-hero-nasdaq`) — variation % QQQ en vert/rouge
- **Ajouté** : DXY — DOLLAR (`dash-hero-dxy`) — niveau + variation (rouge si fort = pression crypto)
- **Conservé** : FEAR & GREED + BTC DOMINANCE
- IDs `dash-dna`, `dash-dna-label`, `dash-signals` cachés (hidden spans, JS intact)

### Expert live grid — suppression des doublons
- **Supprimé** : Fear & Greed + BTC Dominance (déjà affichés dans le hero)
- **Ajouté** : ETH/BTC Ratio (`expert-eth-btc`) — calculé depuis les prix du scanner, label altseason dynamique (🟢/🔴/⚪)
- **Ajouté** : Volume 24H Total (`expert-vol-24h`) — somme de tous les volumes allCoins
- **Conservé** : Prochain évènement 🔴 + Market Cap Total

### TOP 5 GAINS + TOP 5 PERTES — uniformisation STABLECOINS
- Redesign avec `min-width` par colonne : SYMBOLE (56px) | ±% (62px centré) | VOLUME (aligné droite)
- Séparateur subtil `rgba` entre chaque ligne
- Ajout du bloc **TOP 5 PERTES** (`dash-top-losses`) — tri croissant, valeurs en rouge

### Hero Market Strip — remplacement SVG décoratif
- SVG décoratif inutile (`hero-scene`) remplacé par un strip de prix live à 5 colonnes
- `₿ BTC` · `Ξ ETH` · `◎ SOL` · `💠 BNB` · `📊 VOL TOTAL 24H`
- Alimenté par `updateHeroStrip()` → appelé à chaque `market_update` socket
- CSS dédié : `.hero-market-strip`, `.hms-item`, `.hms-price`, `.hms-chg`, `.hms-sym`

### Backend — DXY dans le flux macro
- `macro_loop()` : fetch `fetch_all_indices(["DXY"])` → `dxy` inclus dans WebSocket `macro_update`
- `/api/macro/all` : idem, champ `dxy` ajouté à la réponse JSON

### CSS — corrections
- Ajout `.hero-metric.blue` (couleur `#60a5fa`) — carte NASDAQ était blanche faute de cette règle
- Ajout `.hero-metric.red`

## Décisions

- **NASDAQ + DXY dans le hero** : ce sont les 2 indicateurs macro les plus lisibles pour un investisseur crypto (risk-ON/OFF, pression dollar)
- **ETH/BTC ratio en Expert** : indicateur altseason — plus utile que répéter F&G déjà visible dans le hero
- **Strip de prix live** : remplacement du SVG décoratif qui ne transmettait aucune information utile
- **min-width colonnes** : les symboles de longueur variable (ARIA vs SKYAI vs KRU) cassaient la grille sans contrainte de largeur

## État du projet
- Phase actuelle : Développement actif — polish UI + features dashboard
- Validé : Hero redesigné (NASDAQ/DXY), Expert sans doublons (ETH/BTC + Vol24H), TOP 5 GAINS/PERTES uniformisés, Hero Market Strip live
- En cours : Déploiement Railway (git push à faire par user)
- Pending : Fixes audit priorité 1 (technical_indicators.py, /api/perp doublon, market_info double call)

## Prochaines étapes
1. **git push** → déployer Railway, vérifier le rendu du strip et des cartes hero
2. **Fixes audit priorité 1** : `technical_indicators.py` central, supprimer `/api/perp`, merger double call `market_info`
3. **Portfolio Tracker / Wallet Scanner** : décision page Whales enrichie vs nouvelle page ON-CHAIN
4. **Activer PostgreSQL Railway** : plugin → `DATABASE_URL` auto-injectée

## Fichiers modifiés
- `templates/index.html` — modifié (hero cards, expert grid, top movers, hero market strip, CSS, JS updateHeroStrip)
- `app.py` — modifié (DXY dans macro_loop + api_macro_all)

## Assets (URLs)
Aucun.
