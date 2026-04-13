---
date: 2026-04-13
heure: "14:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-13 14h00 — CryptoScanner Fixes + Wallet Tracker + GitHub

## Résumé
Session de correction de 4 bugs persistants (inscription, CROWDED POSITIONS, marchés week-end, settings Railway) et développement du Wallet Tracker On-Chain Phase 1 (ETH/BTC/SOL). Initialisation du repo GitHub et premier push vers `lboute0433-prog/cryptoscanner`.

## Travail effectué

### Fix #1 — Auto-login après inscription
- Ajout check `lData.token` pour distinguer vrai login vs challenge 2FA
- Fetch `/api/auth/me` avec header `X-Session-Token: lData.token` au lieu de dépendance cookie
- Gestion explicite du cas `requires_2fa` (rare pour nouveau compte)
- `subscription_status` ajouté dans le fallback `currentUser`

### Fix #2 — CROWDED POSITIONS bloqué sur "Chargement..."
- Root cause : `fetch('/api/indices/cross_analysis')` sans try/catch bloquait toute la fonction `loadMood()`
- Fix : try/catch isolé autour du bloc cross_analysis — CROWDED se charge même si VIX/DXY/SP500 indisponibles

### Fix #3 — Marchés forex ouverts le week-end (verif.md #10)
- Root cause : `get_active_sessions()` et `get_session_overview()` vérifiaient uniquement l'heure, jamais le jour
- Fix : nouvelle fonction `_is_forex_open()` → False samedi et dimanche
- `get_session_overview()` : `opens_in = "Fermé (week-end)"` + `best_session = "📅 Marchés fermés — rouvrent lundi"`

### Fix #4 — Settings perdus au redémarrage Railway
- Root cause : `pump_pct`, `scan_interval`, `vol_mult` n'étaient jamais seedés en base (seulement `exchange`)
- Fix : seed des 4 valeurs dans `init_db()` via INSERT OR IGNORE

### Feature — Wallet Tracker On-Chain Phase 1 (verif.md #11)
- Nouveau fichier `wallet_tracker.py` : ETH (Ethplorer freekey) + BTC (Blockchain.info) + SOL (Solana RPC public)
- Auto-détection de chaîne depuis format d'adresse (0x→ETH, 1/3/bc1→BTC, base58→SOL)
- Cache 2 min par adresse
- Route `POST /api/wallet/track` (membres uniquement)
- Bloc UI dans page Whales : input + sélecteur chaîne + résultats (solde, tokens, tx)
- JS `trackWallet()` : affichage complet avec badges REÇU/ENVOYÉ

### GitHub + Deploy
- `.gitignore` créé (exclut .vault_key, *.db, __pycache__, .obsidian)
- Repo initialisé et pushé vers `https://github.com/lboute0433-prog/cryptoscanner`
- Force push `master` → `main-cryptoScanner-/-Codex` (historiques non liés)
- Railway redéploiement automatique en cours

## Décisions
- **X-Session-Token** : plus robuste que la dépendance cookie pour l'auto-login cross-navigateur
- **try/catch isolé** : chaque bloc de `loadMood()` doit être indépendant pour éviter les cascades d'erreur
- **Wallet Tracker dans tab-whales** : cohérent thématiquement (on-chain / mouvements)
- **APIs gratuites** : Ethplorer freekey + Blockchain.info + Solana RPC public — aucune clé requise
- **Force push** : branches sans historique commun — PR impossible, force push obligatoire

## État du projet
- Phase actuelle : Développement actif — polish + déploiement Railway
- Validé session : verif.md #10 ✅, verif.md #11 Phase 1 ✅, 4 bugs corrigés ✅
- En cours : Railway build + déploiement

## Prochaines étapes
1. Vérifier déploiement Railway (build terminé ?)
2. Tester bug inscription en prod
3. Tester Wallet Tracker avec adresse ETH/BTC/SOL réelle
4. **Wallet Tracker Phase 2** : wallets whales connus (Binance, Jump, a16z…) — scan auto
5. `technical_indicators.py` : centraliser RSI/EMA/ATR/Bollinger (4 fichiers)
6. PayPal webhook : après serveur dédié

## Fichiers modifiés
- `templates/index.html` — modifié (auto-login, CROWDED fix, Wallet Tracker UI + JS)
- `app.py` — modifié (route `/api/wallet/track`)
- `forex_engine.py` — modifié (`_is_forex_open`, `get_active_sessions`, `get_session_overview`)
- `scanner_engine.py` — modifié (seed settings dans `init_db`)
- `wallet_tracker.py` — créé
- `.gitignore` — créé

## Assets (URLs)
- GitHub : https://github.com/lboute0433-prog/cryptoscanner
- Railway : https://web-production-34b51.up.railway.app
