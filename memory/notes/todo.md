# Todo — CryptoScanner Pro

## Session 2026-05-02 — Travail Complété + Prochaines Étapes

### ✅ PRIORITÉ HAUTE — COMPLÉTÉE
- [x] **Fixer /api/market_info** — Page DATA macro remplie ✅ (2026-05-02)
  - Diagnostic systématique : threads jamais lancés (start_runtime_services() manquant)
  - Fix : Ajout appel défensif fin de app.py
  - Vérification : /api/market_info retourne données complètes
  - Documentation : contexte.md + bugs.md + memory mise à jour

### 🔴 PRIORITÉ HAUTE — NOUVEAUX BUGS

1. **Création de compte dysfonctionnelle**
   - Procédure d'inscription ne fonctionne pas correctement
   - À investiguer : formulaire, validation, redirection

2. **Gestion Email Admin/Membre**
   - Mettre en place système email pour notifications admin
   - Configuration email par rôle (admin/membre)
   - À configurer : SMTP + templates

3. **Envoi Signaux Telegram — Gestion**
   - Revoir logique d'envoi messages signaux Telegram
   - À vérifier : filtres, déduplication, cooldown

4. **Morning Brief Dysfonctionnel**
   - Lien pour ouvrir morning brief ne fonctionne pas
   - Mise en page + couleurs à revoir
   - À corriger : routes, UI/UX

5. **API IA pour Membres**
   - Revoir gestion adresses API (Groq, Anthropic, Claude)
   - À vérifier : configuration par membre, fallbacks, rate limits

### 🟡 PRIORITÉ MOYENNE
- [ ] Let's Encrypt + domaine custom (remplace certificat auto-signé)
  - Quand domaine disponible : remplacer certificat auto-signé par Let's Encrypt (gratuit)
  - Ajouter domaine à Nginx config
- [ ] Configurer DNS (pointer 46.225.234.71)
- [ ] Configurer SMTP (Gmail, SendGrid, ou autre)
- [ ] Ajouter `COINGECKO_API_KEY` dans .env (supprime les 429)
- [ ] Passer à venv propre sur Hetzner (au lieu de --break-system-packages)

### 🟢 PRIORITÉ BASSE
- [ ] Configurer alertes PM2 si process crash
- [ ] Audit performance + load testing
- [ ] Ajouter monitoring Sentry/NewRelic

---

## Dernière session
- **Date** : 2026-05-02 (suite — debug systématique)
- **Travail fait** : 
  - ✅ Ticker finalisé + HTTPS configuré + bug _get_session() corrigé (session précédente)
  - ✅ /api/market_info débogué avec processus systématique (Phase 1-4)
  - ✅ Tous fichiers documentation mis à jour (contexte, bugs, todo)
- **Bugs fixés** : /api/market_info → threads lancés au startup, données macro actives
- **Fichiers modifiés** : app.py (ligne 150), contexte.md, bugs.md, todo.md
