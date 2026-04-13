---
date: 2026-04-12
heure: "22:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-12 22h00 — CryptoScanner verif.md #4 — Paramètres Plateforme Admin

## Résumé
Session courte de continuation après compaction de contexte. Traitement de verif.md #4 : lecture et explication complète du bloc "Paramètres Plateforme" de la page admin. Aucune modification de code — session 100% explicative/documentaire.

## Travail effectué

### verif.md #4 — Bloc Paramètres Plateforme (admin → ⚙️ PARAMÈTRES)

- Lecture de `templates/admin.html` (lignes 363–397) : formulaire 4 champs
- Lecture de `app.py` route `GET/POST /api/admin/settings` (lignes 1098–1119)
- Lecture de `scanner_engine.py` : `_get_setting()` / `_set_setting()` → table `settings` SQLite

**4 paramètres expliqués :**

| Paramètre | Défaut | Impact |
|-----------|--------|--------|
| `pump_pct` | `5` | Seuil % var 1h pour déclencher alerte PUMP/DUMP |
| `scan_interval` | `10` | Intervalle en secondes entre chaque cycle scanner |
| `vol_mult` | `3` | Multiplicateur × volume moyen pour détecter spike |
| `exchange` | `coingecko` | Source de données principale (Binance/Kraken/CoinGecko) |

**Fonctionnement technique :**
1. Lecture au démarrage : `_get_setting(key, default)` → table `settings` SQLite
2. Modification : formulaire → POST `/api/admin/settings` → `_set_setting(key, value)`
3. Application dynamique sans redémarrage serveur
4. Audit log : `ADMIN_SETTINGS / settings_updated` à chaque sauvegarde

**Limite identifiée :** settings en SQLite local → reviennent aux défauts si Railway redémarre. Fix long terme : variables Railway ou PostgreSQL.

## Contexte session précédente (compacté)

Session 2026-04-12 18h00–20h00 — travail déjà archivé :
- **Canal FREE Telegram** créé : `@CryptoScannerPro_Free`, ID `-1003997628346`
- **SITE_URL** Railway : `https://web-production-34b51.up.railway.app`
- **verif.md #1** ✅ Tri colonnes signaux (sortSignals + ▼/▲)
- **verif.md #2a** ✅ TradingView popup (bouton chart-modal, href dynamique)
- **verif.md #2b** ✅ Historique Smart Signals (table signals_history + route + UI filtrable)
- **verif.md #3** ✅ CVD Flow tableau sticky header
- **verif.md #5** ✅ IA multi-providers (Groq + Anthropic + OpenAI, dropdown + bouton ?)
- **verif.md #6** ✅ Auto-login après inscription + redirect Mon Compte
- **verif.md #7** ✅ Matrice permissions (TAB_ACCESS_RULES complète + badges nav)
- **verif.md #8** ✅ Logos crypto (coinLogoHTML + CDN fallback)
- **verif.md #9** ✅ Bloc Accès Limité dynamique selon rôle
- **Canal FREE** : post_to_free_channel() + alertes PUMP/DUMP simplifiées + résumé journalier
- **Bot /start** : accueil pro FREE vs PREMIUM + lien inscription
- **Bot /lier** : affiche Chat ID + instructions liaison compte site

## Décisions

- **#4 → pas de modification de code** : le bloc fonctionne tel quel, juste besoin d'explication
- **Settings Railway** : `TG_CHAT_FREE=-1003997628346`, `SITE_URL=https://web-production-34b51.up.railway.app` — à configurer si pas encore fait

## État du projet
- Phase actuelle : Développement actif — polish + Telegram FREE opérationnel
- Validé session : verif.md #4 expliqué
- Restant verif.md : **#10** (marchés ouverts week-end), **#11** (Arkham Intelligence — grand chantier)

## Prochaines étapes
1. **git push** → déployer Railway (si pas encore fait)
2. **Variables Railway** : `TG_CHAT_FREE` + `SITE_URL` (si pas encore fait)
3. **verif.md #10** : vérifier logique marchés ouverts week-end (actions NASDAQ/SP500)
4. **verif.md #11** : Arkham Intelligence — réflexion Portfolio Tracker on-chain (lié samedi.md item 5)
5. **technical_indicators.py** : centraliser RSI/EMA/ATR/Bollinger (4 fichiers)
6. **PayPal webhook** : après serveur dédié

## Fichiers modifiés
Aucun. Session purement explicative.

## Assets (URLs)
- Canal Telegram FREE : https://t.me/CryptoScannerPro_Free (ou nom choisi)
- Site Railway : https://web-production-34b51.up.railway.app
- Transcription complète session : `C:\Users\loyan\.claude\projects\C--Users-loyan-Documents-CryptoScanner-Codex-Projet-cryptoscanner-main-cryptoScanner-Codex\fc7d5b1a-4b72-4e93-9a94-11dd6b8a3480.jsonl`
