---
tags: [projet/cryptoscanner, type/bugs]
---

# Bugs connus — CryptoScanner Pro

## Actifs

### Création de Compte — Dysfonctionnelle — CRITIQUE
- **Symptôme** : Procédure d'inscription ne fonctionne pas correctement
- **Impact** : Utilisateurs ne peuvent pas créer de compte
- **À investiguer** :
  - Validation du formulaire
  - Envoi données à base de données
  - Redirection après inscription
  - Messages d'erreur/validation
- **Priorité** : 🔴 HAUTE

### Gestion Email Admin/Membre — À Mettre en Place
- **Symptôme** : Système d'email par rôle absent
- **À faire** :
  - Configuration email par rôle (admin notifications vs membre)
  - SMTP configuration (SendGrid/Mailgun recommandé)
  - Templates emails (inscription, alerte, notifications)
  - Authentification membre pour accès API IA
- **Priorité** : 🔴 HAUTE

### Envoi Signaux Telegram — Gestion Défaillante
- **Symptôme** : Signaux Telegram envoyés de manière incohérente
- **À revoir** :
  - Logique filtrage signaux (score, ADR, volume)
  - Déduplication messages
  - Cooldown entre signaux (1h)
  - Formatage messages (MA20, ADR)
- **Priorité** : 🔴 HAUTE

### Morning Brief — Lien Cassé + UI Dégradée
- **Symptôme** :
  - Lien pour ouvrir morning brief ne fonctionne pas
  - Mise en page + couleurs à revoir
- **À corriger** :
  - Routes `/morning-brief` vérifier
  - Génération contenu (COT, macro, signaux)
  - UI/UX (layouts Telegram, colors, readability)
- **Priorité** : 🔴 HAUTE

### API IA pour Membres — Configuration Incohérente
- **Symptôme** : Gestion adresses API (Groq, Anthropic, Claude) confuse
- **À revoir** :
  - Stockage clés API par membre (encrypted?)
  - Fallback chain (Groq → Anthropic → Claude)
  - Rate limits par provider
  - Configuration UI/settings pour membres
- **Priorité** : 🔴 HAUTE

### Email SMTP — Peu Fiable sur Railway
- **Symptôme** : Envoi email échoue en production Railway
- **Cause** : Gmail SMTP bloqué ou peu fiable sur l'hébergement
- **Contournement** : Utiliser uniquement Telegram pour les notifications critiques
- **Solution long terme** : Migrer vers un provider transactionnel (Mailgun, Resend, SendGrid) avec domaine vérifié
- **Diagnostic** : Visible dans l'admin (`/admin` → SMTP diagnostics)
- **Priorité** : 🟡 MOYENNE

## Résolus

### /api/market_info Retourne Données — RÉSOLU ✅
- **Symptôme** : Page DATA macro n'affichait aucune donnée (blocs vides)
- **Root cause** : `start_runtime_services()` jamais appelé au startup app.py
- **Diagnostic** : Traçage appels → fonction définie mais JAMAIS INVOQUÉE dans app.py (seulement dans wsgi.py)
- **Cause profonde** : Hetzner n'utilisait pas wsgi.py, threads de fond jamais lancés, `_market_info = {}` restait vide
- **Fix** : Ajout appel `start_runtime_services()` à la fin du fichier app.py (après toutes les définitions)
- **Vérification** : `/api/market_info` retourne `{fear_greed, dominance, ...}` ✅
- **Session fix** : 2026-05-02
- **Fichiers modifiés** : `app.py` (fin du fichier)

### Session Authentication Error — RÉSOLU ✅
- **Symptôme** : Erreur 500 `NameError: name '_get_session' is not defined` à ligne 640
- **Root cause** : Appels à `_get_session()` au lieu de `get_session()`
- **Fix** : `sed -i 's/_get_session()/get_session()/g' /root/cryptoscanner/app.py`
- **Vérification** : Session authentication fonctionne, pages chargent correctement ✅
- **Session fix** : 2026-05-02
- **Fichiers modifiés** : `app.py` (multiples lignes)

## Patterns récurrents

Voir `directives/debug.md` pour le guide de debug et les patterns d'erreurs fréquents.
