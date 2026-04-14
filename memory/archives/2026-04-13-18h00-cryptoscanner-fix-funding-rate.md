---
date: 2026-04-13
heure: "18:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-13 18h00 — CryptoScanner Fix Funding Rate CROWDED POSITIONS

## Résumé
Session courte de correction du bug funding rate dans CROWDED POSITIONS : tous les contrats affichaient +0.0000%. Root cause identifiée et corrigée dans `indices_engine.py`, commit pushé sur GitHub, Railway redéploie automatiquement.

## Travail effectué

### Fix — Funding Rate 0.0000% CROWDED POSITIONS
- Root cause : `_fetch_bybit_funding()` faisait `float(fr) * 100` sans guard sur `fr == ""` — Bybit retourne parfois une chaîne vide pour `fundingRate`
- `float("")` lève une `ValueError` silencieuse dans le `try/except` global → `funding_map` entièrement vide → 0.0000% partout
- Fix : ajout guard `fr != ""` + try/except individuel par entrée pour ne pas vider tout le map sur une seule valeur invalide
- Commit pushé : `1d5010d` sur `main-cryptoScanner-/-Codex`

## Décisions
- **Guard individuel par entrée** : un `float("")` ne doit pas invalider tout le `funding_map` — chaque entrée a son propre try/except
- **Push force** : branche sans historique commun, force push obligatoire vers `main-cryptoScanner-/-Codex`

## État du projet
- Phase actuelle : Développement actif — polish + déploiement Railway
- Validé : Fix funding rate ✅ — commit `1d5010d` pushé
- En cours : Railway build en cours après push

## Prochaines étapes
1. Vérifier CROWDED POSITIONS en prod après build Railway (funding rates non nuls)
2. Page Marchés : rien n'a changé visuellement — vérifier si le bug persiste côté frontend (données bien transmises ?)
3. Page Whales : idem — tester Wallet Tracker en prod
4. **Wallet Tracker Phase 2** : wallets whales connus (Binance, Jump, a16z…) — scan auto
5. `technical_indicators.py` : centraliser RSI/EMA/ATR/Bollinger (4 fichiers)
6. Trouver de meilleures illustrations pour le hero/UI
7. Réfléchir au nouveau nom de la plateforme (couvrir marchés financiers au sens large)

## Fichiers modifiés
- `indices_engine.py` — modifié (`_fetch_bybit_funding()` : guard `fr != ""` + try/except par entrée)

## Assets (URLs)
- GitHub : https://github.com/lboute0433-prog/cryptoscanner
- Railway : https://web-production-34b51.up.railway.app
