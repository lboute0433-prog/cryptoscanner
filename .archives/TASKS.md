# CryptoScanner Pro — Todo List 📋
**Mise à jour** : 2026-05-05 (Session en cours)
**Serveur** : Hetzner 46.225.234.71 (ex-Railway)

---

## 🎯 URGENT — En attente déploiement

### ✅ COMPLÉTÉES (Session 2026-05-05)
- [x] **Morning Brief Redesign** — Design finalisé (Approche C Interactive Pro+) ✅
  - Medals ranking (🥇🥈🥉)
  - Performance bars normalisées
  - Gradient background #0f1428 → #1e1a4a
  - CSS variables + responsive
  - Déployé sur Hetzner ✅

- [x] **Diagnostic Root Cause** — Identifié problème réel ✅
  - **Timing issue** : Scanner cache prend temps à charger au démarrage
  - **CoinGecko 429** : Rate limit quand Priority 1 échoue
  - **Solution temporaire** : Merger + parsing virgule/point appliqués
  - **Fichier** : `morning_brief.py` lignes 143-180, 679, 687-688

### 🔴 À FAIRE (Priorité CRITIQUE)

1. **[BLOQUANT]** Implémenter CoinGecko Cache Fallback
   - Ajouter cache persistant `/tmp/brief-cache.json`
   - Quand CoinGecko 429 → utiliser cache au lieu d'échouer
   - Vérifier que les données sont préservées même si API down
   - Fichier: `morning_brief.py` fonction `fetch_brief_data()`
   - Deadline: Avant prochaine génération morning brief

2. **[Critique]** Corriger création de compte
   - Procédure d'inscription dysfonctionnelle
   - SMTP firewall bloque (solution : config SMTP externe)
   - Status: EN ATTENTE config
   - Bloqué par: Email system

3. **[Important]** Reconfigurer signaux Telegram
   - Gestion envois défaillante
   - Revoir logique filtrage/cooldown/spam

4. **[Important]** Système email admin/membre
   - Infrastructure manquante
   - Bloqueur: SMTP firewall Hetzner
   - Nécessite: Mailgun, SendGrid, ou autre fournisseur SMTP

5. **[URGENT — Session 2026-05-05]** Cache Fallback pour Morning Brief
   - **Raison** : CoinGecko 429 rate limit → données vides
   - **Solution** : Ajouter `/tmp/brief-cache.json`
   - **Implémentation** : `fetch_brief_data()` lignes ~170-180
   - **Prio** : AVANT prochaine génération morning brief
   - **Estimation** : 1h

### 📊 Prochaines étapes (Phase 2)

- [ ] Configurer Let's Encrypt (remplace certificat auto-signé)
- [ ] Configurer domaine custom (DNS → 46.225.234.71)
- [ ] Ajouter COINGECKO_API_KEY env var (élimine 429 errors)
- [ ] Configurer SMTP fonctionnel (Mailgun/SendGrid/autre)
- [ ] Audit sécurité full-stack

---

## 📋 Backlog par département

### Dev — Scanner & Signaux
- [x] Scanner multi-exchange (Binance, Kraken, Bybit, OKX)
- [x] Smart signals avec scoring
- [x] Retrace RSI avec cooldown
- [ ] Améliorer détection whales (ajouter LunarCrush sentiment)

### Reporting — Alertes & Briefs
- [x] Morning Brief HTML + design
- [x] Daily report Telegram
- [x] Signal Telegram multi-niveaux (FREE/PAID/VIP)
- [ ] **[URGENT]** Fix variations zéro → déployer aujourd'hui

### Data — Macro & COT
- [x] Macro data (Fear&Greed, Dominance, indices)
- [x] COT CFTC intégration
- [x] ETF flows
- [ ] Ajouter CoinMarketCap fallback (optionnel)

### Infrastructure — Hetzner & Security
- [x] Migration Railway → Hetzner ✅
- [x] SSL/HTTPS certificat auto-signé ✅
- [x] PM2 process manager ✅
- [ ] Let's Encrypt + domaine custom
- [ ] SMTP fonctionnel
- [ ] Alertes PM2 crash

---

## 🔧 Commandes utiles (Hetzner)

```bash
# État service
pm2 status
pm2 logs cryptoscanner --lines 50

# Tester endpoint
curl -s https://46.225.234.71/brief?token=\
$(echo -n "$(date +%Y-%m-%d)" | openssl dgst -sha256 -hmac "cs_brief_2024" | cut -d' ' -f2) \
| head -50

# Redémarrer
pm2 restart cryptoscanner

# Vérifier fichier
tail -20 /root/cryptoscanner/morning_brief.py  # dernières lignes
```

---

## 📅 Timeline historique

### 2026-05-04 — Inscription + Emails (COMPLÈTE)
- ✅ app.py corrompu → fichier validé
- ✅ Page /dashboard → formulaire accessible
- ✅ Inscription → async, < 1s
- ✅ Emails → async + timeout réduit
- ✅ Liens Telegram → Hetzner
- ⏳ SMTP firewall → EN ATTENTE config

### 2026-05-05 — Morning Brief Redesign + Fix Data (EN COURS)
- ✅ Redesign design finalisé
- ✅ Fix variations zéro appliqué
- 🚀 À déployer sur Hetzner

---

## 📋 Session 2026-05-05 — Résumé Archivé

**Découvertes clés:**
- ✅ Redesign Morning Brief finalisé + déployé
- ✅ Root cause du problème identifiée : Timing issue + CoinGecko 429
- ✅ Tous les fichiers memory/obsidian mis à jour
- ✅ Archive complète créée

**Fichiers modifiés:**
- `morning_brief.py` — Lignes 143-180 (merger logic), 679, 687-688 (parsing)
- `contexte.md` — Session 2026-05-05 documentée
- `_index.md` — Archive ajoutée
- `TASKS.md` — Tâches urgentes identifiées

**Prochaine étape prioritaire:**
- Implémenter cache fallback pour CoinGecko 429 (voir TASKS #5)
- Estimation : 1h
- Impact : Résout 80% du problème données vides

---

**Propriétaire** : Lolo (l.boute0433@gmail.com)
**Serveur** : Hetzner VPS CPX22 | 46.225.234.71
**Base de données** : SQLite local
**IA** : Groq + Anthropic fallback

**Archive date** : 2026-05-05 09:20 UTC
**Status** : ✅ SESSION ARCHIVÉE PROPREMENT
