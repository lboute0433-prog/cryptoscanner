# Bugs Détectés — Session 2026-05-02

**Date** : 2026-05-02  
**Status** : Documenté pour prochaine session  
**Priorité** : 🔴 CRITIQUE (5 bugs bloquants)

---

## 1️⃣ Création de Compte — Dysfonctionnelle

**Symptôme** : Utilisateurs ne peuvent pas s'inscrire correctement

**À investiguer** :
- Formulaire validation (côté client + serveur)
- Envoi données POST vers `/api/auth/register`
- Vérification email unique dans base données
- Hachage mot de passe (bcrypt V11)
- Création session après inscription
- Redirection vers dashboard/settings

**Points clés** :
- Auto-login après inscription (token retourné directement?)
- Affichage messages d'erreur/validation
- Vérification SMTP n'est pas requis pour inscription

**Fichiers concernés** : `app.py` (routes auth), `scanner_engine.py` (create_user)

---

## 2️⃣ Gestion Email Admin/Membre — À Mettre en Place

**Symptôme** : Système d'email par rôle absent

**À faire** :
1. **Configuration SMTP** (SendGrid/Mailgun recommandé)
   - Remplacer Gmail (peu fiable sur Hetzner)
   - Templates emails transactionnel
   - Domain verification

2. **Notifications Admin**
   - Contact form submissions
   - User registrations
   - Error alerts

3. **Notifications Membre**
   - Inscription confirmation
   - Password reset
   - Subscription updates
   - API key alerts

4. **API IA Gestion**
   - Affichage clés API membres (encryptées)
   - Configuration par membre (Groq/Anthropic/Claude)
   - Rate limit monitoring

**Fichiers concernés** : `app.py` (email routes), `security.py` (encryption)

---

## 3️⃣ Envoi Signaux Telegram — Gestion Défaillante

**Symptôme** : Signaux envoyés de manière incohérente/excessifs

**À revoir** :
1. **Filtrage Signaux**
   - Score minimum (85?)
   - ADR minimum (25% range 24h?)
   - Volume seuil

2. **Déduplication**
   - Éviter envoyer même signal 2x
   - Historique signaux dernière heure

3. **Cooldown**
   - 1h entre signaux même paire
   - Ou 3 max signaux par cycle?

4. **Formatage Messages**
   - Include MA20 + ADR dans message
   - Badge "DEMO" si API indisponible
   - Emoji + couleurs cohérentes

5. **Distribution**
   - Multichannel par rôle (`get_members_by_role(min_role)`)
   - Filtre canal FREE vs Premium

**Fichiers concernés** : `smart_signals.py`, `daily_report.py`, `app.py` (telegram routes)

---

## 4️⃣ Morning Brief — Lien Cassé + UI Dégradée

**Symptôme 1** : Lien pour ouvrir morning brief ne fonctionne pas
- Route `/morning-brief` inaccessible?
- Widget "Ouvrir brief" clique sur rien?

**Symptôme 2** : Mise en page + couleurs dégradées
- Blocs misalignés
- Couleurs de texte mauvaises
- Contraste insuffisant

**À corriger** :
1. **Routes Backend**
   - Vérifier `/api/morning-brief` retourne données
   - GET `/morning-brief` retourne HTML/template
   - Session authentication OK

2. **Contenu Morning Brief**
   - COT CFTC (7 blocs Telegram)
   - Macro data (Fear&Greed, Dominance)
   - Signaux rsi
   - Formatage + parsing OK

3. **UI/UX Frontend**
   - Layouts Telegram (responsive)
   - Colors palette cohérente
   - Typography readability
   - Hover/focus states

**Fichiers concernés** : `templates/index.html`, `app.py` (routes), `morning_brief.py`

---

## 5️⃣ API IA pour Membres — Configuration Incohérente

**Symptôme** : Gestion adresses API (Groq, Anthropic, Claude) confuse

**À revoir** :
1. **Stockage Clés API**
   - Où stored? (users table, séparé?)
   - Encryption Fernet OK?
   - Display masqué (show last 4 chars?)

2. **Fallback Chain**
   - Groq (principal) → Anthropic → Claude
   - Ordre logique?
   - Retry logic OK?

3. **UI Settings**
   - Page `/settings` pour gérer clés
   - Input validation (length, format)
   - Affichage statut API (connected/error)

4. **Rate Limiting**
   - Per-member rate limits?
   - Quota tracking?
   - Cost monitoring?

5. **Error Handling**
   - Afficher errors lisibles
   - Suggestions fallback
   - Logging pour debug

**Fichiers concernés** : `security.py` (key storage), `ai_provider.py` (fallback logic), `app.py` (settings routes)

---

## Prochaines Étapes

**Pour prochaine session** :
1. Choisir bug #1 (création compte) — le plus bloquant
2. Debugger systématiquement (Phase 1-4)
3. Fixer + tester
4. Documenter dans bugs.md (Résolus)
5. Continuer autres bugs

**Ordre recommandé** :
1. Création compte (bloque new users)
2. Morning brief link (user experience)
3. Signaux Telegram (feature critical)
4. Email setup (notifications)
5. API IA config (advanced feature)

---

**Mis à jour** : 2026-05-02  
**Statut** : Ready for next session debugging
