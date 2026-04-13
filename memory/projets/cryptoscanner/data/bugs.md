---
tags: [projet/cryptoscanner, type/bugs]
---

# Bugs connus — CryptoScanner Pro

## Actifs

### Email SMTP — peu fiable sur Railway
- **Symptôme** : Envoi email échoue en production Railway
- **Cause** : Gmail SMTP bloqué ou peu fiable sur l'hébergement
- **Contournement** : Utiliser uniquement Telegram pour les notifications critiques
- **Solution long terme** : Migrer vers un provider transactionnel (Mailgun, Resend, SendGrid) avec domaine vérifié
- **Diagnostic** : Visible dans l'admin (`/admin` → SMTP diagnostics)

## Résolus

<!-- Les bugs résolus seront documentés ici après correction -->

## Patterns récurrents

Voir `directives/debug.md` pour le guide de debug et les patterns d'erreurs fréquents.
