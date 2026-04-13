# Directive — Rapport Quotidien Telegram

## Objectif

Générer et envoyer le rapport quotidien via Telegram (et optionnellement email).

## Agent responsable

`.claude/agents/reporting/rapport.md`

## Entrées

- Contenu du Morning Brief (généré par `morning_brief.py`)
- Données scanner du jour
- Token Telegram et ID du canal

## Scripts à utiliser

| Ordre | Script | Action |
|-------|--------|--------|
| 1 | `daily_report.py` | Génération et envoi du rapport Telegram |
| 2 | `morning_brief.py` | Source du contenu si non déjà généré |
| 3 | `scanner_engine.py` | Données marché pour enrichir le rapport |

## Variables d'environnement requises

```
TG_TOKEN    ← Token du bot Telegram (obligatoire)
TG_CHAT     ← ID du canal ou chat de destination (obligatoire)
```

Variables optionnelles (email) :
```
SMTP_SERVER, SMTP_PORT
SMTP_LOGIN, SMTP_PASSWORD
SMTP_FROM_EMAIL, ADMIN_NOTIFY_EMAIL
```

## Procédure

1. **Vérifier** que `TG_TOKEN` et `TG_CHAT` sont définis
2. **Vérifier** que le Morning Brief est disponible (générer si absent)
3. **Exécuter** `daily_report.py`
4. **Confirmer** la réception dans le canal Telegram
5. **Tenter** l'envoi email si configuré (SMTP non critique)
6. **Documenter** tout échec dans les notes de l'agent Rapport

## Sorties

- Message Telegram envoyé dans `TG_CHAT`
- Email envoyé à `ADMIN_NOTIFY_EMAIL` (si SMTP configuré)
- Confirmation ou rapport d'erreur

## Cas limites

- **TG_TOKEN manquant** : stopper et demander la configuration
- **Telegram API down** : réessayer après 5 min, max 3 tentatives
- **Message trop long** : `daily_report.py` doit gérer le découpage — vérifier si ce cas est géré
- **SMTP échoue** : noter l'erreur mais ne pas bloquer l'envoi Telegram (email = secondaire)
- **État actuel SMTP** : Gmail peu fiable sur Railway — préférer provider transactionnel (voir README)

## Fréquence recommandée

- Une fois par jour, après génération du Morning Brief
- Peut être déclenché manuellement ou en job automatique
