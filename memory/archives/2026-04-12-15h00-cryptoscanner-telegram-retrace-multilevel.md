---
date: 2026-04-12
heure: "15:00"
projet: cryptoscanner
phase: en-cours
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-12 15h00 — CryptoScanner Telegram Retrace + Multi-niveaux

## Résumé
Session axée sur l'amélioration du système Telegram : ajout de la détection de retournement RSI (signal retrace/rebond), mise en place d'un système multi-niveaux d'accès aux alertes selon le rôle utilisateur (member/paid/vip), et uniformisation du disclaimer légal sur tout le projet.

## Travail effectué

### Disclaimer légal — uniformisé partout
- Remplacé "Analyse technique — pas un conseil financier" par le texte légal complet :
  "Ceci ne constitue pas un conseil d'achat ou de vente. CryptoScanner Pro fournit uniquement des données techniques à titre informatif."
- Modifié dans : `smart_signals.py` (×2), `morning_brief.py` (×2), `templates/index.html` (×1)

### Signal Retrace RSI — `smart_signals.py`
- Ajout `MIN_VOLUME_SMALL = 500_000` — constante pour les small caps (RAVE-style)
- Ajout `_rsi_history: dict` — cache mémoire rolling des 2 dernières valeurs RSI par symbole
- `update_rsi_history(symbol, rsi)` — mémorise chaque analyse
- `check_rsi_exit(symbol, current_rsi)` — détecte 2 cas :
  - RSI quitte surachat (≥70 → <70) → "bearish" = ⚠️ RETRACE PROBABLE
  - RSI quitte survente (≤30 → >30) → "bullish" = 🔔 REBOND POSSIBLE
- `build_retrace_alert()` — format Telegram distinct, focus sortie/prudence

### Smart Signal Loop — `app.py`
- Importé : `update_rsi_history, check_rsi_exit, build_retrace_alert, calc_rsi`
- `smart_signal_loop()` réécrit avec 2 niveaux de scan :
  - Standard $2M+ → Smart Signals + RSI tracking
  - Small caps $500K–$2M → RSI tracking seulement
- Ajout `_alerted_retraces` set dédup (1 alerte/symbole/direction/heure)
- `_send_retrace_alert()` — envoi Telegram + broadcast paid uniquement

### Multi-niveaux Telegram — matrice d'accès
- `scanner_engine.py` : `_broadcast_to_members(msg, min_role="member")` avec filtre SQL par rôle
  - _TG_ROLE_TIERS : member→tous, paid→paid+vip+admin, vip→vip+admin
- `daily_report.py` : `send_telegram(min_role="member")` + nouvelle fonction `get_members_by_role(min_role)`
- `news_macro.py` : broadcast paid dans `send_macro_alert_telegram()` via `get_members_by_role("paid")`
- `app.py` : Smart Signals + Retrace → `min_role="paid"`, calendrier macro → `min_role="paid"`

### Matrice finale
| Alerte | Destinataires |
|---|---|
| Smart Signals | paid + vip + admin |
| Retrace RSI | paid + vip + admin |
| Macro ForexFactory | paid + vip + admin |
| Calendrier macro (événements) | paid + vip + admin |
| Daily report / news | tous (member+) |

## Décisions

- **Scénario 1 Telegram** : le site est le point d'entrée unique. Le bot = outil de notification, pas d'inscription directe via Telegram
- **Architecture combinée** : canal public FREE (news + basiques, marketing) + DMs directs pour paid/VIP (Smart Signals + Retrace + Macro)
- **PayPal webhook** : reporté à quand le site est sur serveur dédié
- **Rôle = clé d'accès Telegram** : pas l'abonnement. L'admin change le rôle manuellement via `/api/admin/users/<uid>/role` (route déjà existante). Abonnement = tracking paiement séparé
- **Small caps $500K** : suivi RSI pour détecter les retraces (RAVE-style) même sans déclencher un Smart Signal complet

## État du projet
- Phase actuelle : Développement actif — polish + features Telegram
- Validé : Signal retrace RSI, multi-niveaux Telegram, disclaimer légal
- En cours : Déploiement Railway (git push à faire par user)
- Pending : Canal Telegram FREE, message /start bot, webhook PayPal (plus tard)

## Prochaines étapes
1. **git push** → déployer Railway
2. **Canal Telegram FREE** : créer le canal + faire poster le bot les news/alertes basiques automatiquement
3. **Message /start bot** : répondre avec lien vers le site pour lier le compte
4. **PayPal webhook** : `/webhooks/paypal` → passage auto paid quand paiement confirmé (après serveur dédié)
5. **samedi.md item 5** : Portfolio Tracker / Wallet Scanner (grand chantier)
6. **technical_indicators.py** : centraliser RSI/EMA/ATR/Bollinger

## Fichiers modifiés
- `smart_signals.py` — modifié (MIN_VOLUME_SMALL, _rsi_history, RSI exit detection, build_retrace_alert, disclaimer)
- `app.py` — modifié (imports, smart_signal_loop dual-tier, _send_retrace_alert, _alerted_retraces, min_role calls)
- `scanner_engine.py` — modifié (_broadcast_to_members avec min_role + _TG_ROLE_TIERS)
- `daily_report.py` — modifié (send_telegram avec min_role, get_members_by_role, _TG_ROLE_TIERS)
- `news_macro.py` — modifié (send_macro_alert_telegram broadcast paid)
- `morning_brief.py` — modifié (disclaimer ×2)
- `templates/index.html` — modifié (disclaimer ×1)

## Assets (URLs)
Aucun.
