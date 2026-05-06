# 🐛 Bug List — CryptoScanner Pro (2026-05-02)

## 🔴 P1 — CRITIQUES (Frontend + UX)

### 1. Landing Page — Routing Bug
- **Symptôme** : Sans compte, on arrive pas sur landing page
- **Expected** : Visiteur sans authentification → force landing page
- **Actual** : Routage cassé, peut accéder aux pages protégées
- **Fix** : Vérifier `session.user_id` dans routes, redirect `/` si missing
- **File** : `app.py` (routes) + `templates/landing.html`
- **Status** : 🔴 À faire

### 2. Bloc TOTAL 3 — Données Vides
- **Symptôme** : Dashboard `/macro` bloc "TOTAL 3" (Excluding BTC & ETH) vide
- **Cause** : API endpoint ou calcul manquant
- **Options** :
  - ✅ Implémenter calculation (somme des autres cryptos)
  - 🗑️ Supprimer le bloc si pas important
- **File** : `app.py` (endpoint `/api/market_info`) + `templates/dashboard.html`
- **Status** : 🟡 Décision requise (keep ou remove?)

### 3. Bloc OTHERS — Données Vides
- **Symptôme** : Dashboard `/macro` bloc "OTHERS" (Excluding Top 10) vide
- **Cause** : Même que TOTAL 3 — calcul manquant
- **Options** :
  - ✅ Implémenter calculation
  - 🗑️ Supprimer si pas important
- **File** : `app.py` (endpoint `/api/market_info`) + `templates/dashboard.html`
- **Status** : 🟡 Décision requise (keep ou remove?)

### 4. Bloc PROCHAIN ÉVÉNEMENT — Manquant
- **Symptôme** : Bloc "Prochain événement" absent de dashboard
- **Importance** : ⭐⭐⭐ (Very important)
- **À implémenter** :
  - Récupérer calendrier économique (FRED, Trading Economics, etc.)
  - Afficher prochain événement majeur (CPI, FED, earnings, etc.)
  - Format: nom + date/heure + impact (high/med/low)
- **File** : `app.py` (endpoint `/api/next_event`) + `templates/dashboard.html`
- **Status** : 🔴 À faire

---

## 🟡 P2 — IMPORTANTS (Données + Graphiques)

### 5. Graphique COT — Positions Nettes par Catégories
- **Symptôme** : Graphique "POSITIONS NETTES PAR CATÉGORIES" difficile à améliorer
- **Problème actuel** :
  - Stacked bar chart basique
  - Peu d'interactivité
  - Peut être confus (LF Net rouge, AM Net vert)
- **Options d'amélioration** :
  - [ ] Ajouter hover avec valeurs exactes
  - [ ] Ajouter toggle pour chaque catégorie (LF / AM / OI)
  - [ ] Ajouter ligne de tendance
  - [ ] Utiliser Plotly au lieu de chart.js pour plus d'interactivité
  - [ ] Ajouter annotation "Bullish trend" / "Bearish trend"
- **File** : `templates/` (COT page) + backend COT data
- **Status** : 🟡 À améliorer (nice-to-have)

### 6. ETH/BTC Ratio — Bloc Vide?
- **Symptôme** : Bloc "ETH/BTC RATIO" affiche `0.02942` avec "🔴 BTC dominant"
- **Question** : C'est un bug ou c'est correct?
- **À vérifier** : Calcul du ratio (doit être ETH price / BTC price)
- **Status** : 🟡 À vérifier

---

## 🟢 P3 — NICE-TO-HAVE (Optimisations)

### 7. Calendar Macro — Caching + Performance
- **Symptôme** : Calendrier économique peut être lent au chargement
- **À faire** : Ajouter cache SQLite avec TTL (24h)
- **File** : `news_macro.py`
- **Status** : 🟢 Optionnel

### 8. Mobile Responsiveness — Dashboard
- **Symptôme** : Blocs dashboard peuvent être écrasés sur mobile
- **À faire** : Améliorer grid responsive (flex au lieu de grid 2/3 colonnes)
- **File** : `templates/dashboard.html` (CSS)
- **Status** : 🟢 Optionnel

---

## 📋 RÉSUMÉ ACTIONABLE

| # | Bug | Priorité | Fix Time | Status |
|---|-----|----------|----------|--------|
| 1 | Landing page routing | 🔴 P1 | 30 min | À faire |
| 2 | Bloc TOTAL 3 | 🔴 P1 | 20 min | Décision (keep/remove) |
| 3 | Bloc OTHERS | 🔴 P1 | 20 min | Décision (keep/remove) |
| 4 | Prochain événement | 🔴 P1 | 2h | À faire ⭐⭐⭐ |
| 5 | COT graphique | 🟡 P2 | 1h | À améliorer |
| 6 | ETH/BTC ratio | 🟡 P2 | 15 min | À vérifier |
| 7 | Calendar caching | 🟢 P3 | 30 min | Optionnel |
| 8 | Mobile responsive | 🟢 P3 | 1h | Optionnel |

---

## 🎯 ORDRE RECOMMANDÉ

1. **Landing page** (P1 - 30 min) → Sécurité critical
2. **TOTAL 3 / OTHERS** (P1 - 20 min each) → Décider keep/remove
3. **Prochain événement** (P1 - 2h) → Important business value
4. **COT graphique** (P2 - 1h) → UX improvement
5. **ETH/BTC ratio** (P2 - 15 min) → Verification quick
6. **Caching + Mobile** (P3) → Nice-to-have

---

**Session créée** : 2026-05-02 05h35  
**Prochaine action** : Corriger landing page routing
