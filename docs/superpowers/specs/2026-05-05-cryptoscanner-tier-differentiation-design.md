# CryptoScanner Pro — Tier Differentiation & Feature Strategy

**Date** : 2026-05-05  
**Status** : Design Approved  
**Scope** : Stratégie de monétisation + différenciation 3 niveaux (Free/Membre/VIP)

---

## 📋 Résumé Exécutif

CryptoScanner Pro dispose d'une **base technologique solide** (scanner, Morning Brief, COT, Forex, alertes Telegram). Le challenge : **monétiser** en créant une différenciation claire entre Free, Membre ($15-18/mois), et VIP ($49-79/mois).

**Stratégie** : Transformer les données existantes en **insights actionnables** via 4 features clés qui créent de la valeur réelle.

---

## 🎯 Objectif Business

**Avant (situation actuelle)** : App riche mais confuse. L'utilisateur ne sait pas pourquoi payer.  
**Après (objectif)** : 3 parcours clairs — Free te montre qu'on a raison, Membre te rend opérationnel, VIP te donne l'avantage.

**KPI de succès** :
- Free → Membre conversion : 5-10%
- Retention Membre > 60% (churn < 40%/mois)
- VIP : 1-2% de la base (mais ARPU très élevé)

---

## 🏗️ Architecture : Les 4 Pilliers

### 1️⃣ **INSTITUTIONAL DASHBOARD** (Nouvelle feature)
**Niveau minimum** : Membre  
**Où** : Tab "💼 TRADING" → Nouvelle section "Institutional Flows"

**Components** :
- **Real-time Liquidation Heatmap** — Liquidations long/short par niveau de prix (candlestick-like)
  - Colonne: Prix | Long liquidés | Short liquidés | Net | Sentiment
  - Auto-update toutes les 30 secondes
  - Highlight: Si liquidations > $20M à un niveau = couleur rouge/alerte

- **Whale Monitor** — Agrégation whales + volume anormaux
  - Timeline : dernières 24h, changeable
  - Sort: par taille, par timeframe
  - Free (30 min delay) | Membre (live) | VIP (live + email alert)

- **Funding Rate Animator** — Graphique live des funding rates
  - X-axis: timeframe (7j)
  - Y-axis: rate (%) par perp
  - Si funding rate > 0.15% = couleur orange (unsustainable)
  - Si funding rate > 0.25% = couleur rouge (danger immédiat)

- **Smart Signal Generator** — IA qui dit "SO WHAT?" 
  - Input: liquidations + funding + volume
  - Output: "⚠️ 50M$ liquidations SHORT à 45k + funding rate 0.22% → rebond probable à 46.2k"
  - VIP only: Email notification imédiate

**Data source** : Scanner existant + api_manager + nouvelles données liquidations Binance API

---

### 2️⃣ **CORRÉLATIONS VIVANTES** (Nouvelle feature)
**Niveau minimum** : Membre  
**Où** : Tab "📊 ANALYSE" → Nouvelle section "Corrélations Macros"

**Components** :
- **Multi-Asset Canvas** — Graphique interactif 4-asset
  - Assets: BTC, DXY, SPX, Fear&Greed (ou sélectionnable)
  - Mode: Line chart avec secondes Y-axis (normalisé %)
  - Timeframe: 7j / 30j / 90j (toggle buttons)
  - Interactif: Hover sur point = value + date pour tous les assets

- **Correlation Matrix** — Tableau de corrélation
  - BTC vs DXY: -0.85 (strong inverse)
  - BTC vs SPX: +0.72 (coupling)
  - BTC vs Fear: -0.61 (negative)
  - Couleur: Rouge (negative) → Vert (positive)
  - Mise à jour: 1x/jour (data Groq)

- **Macro Context Badge** — Affichage contexte global
  - Fed stance: "Hawkish (+0.25% rate)" | "Neutral" | "Dovish"
  - DXY trend: "Strengthening 📈" | "Weakening 📉"
  - Fear level: "Extreme (20-25)" | "Neutral (50)" | "Greed (75+)"
  - Impact crypto: "🔴 Headwind" | "🟡 Neutral" | "🟢 Tailwind"

**Data source** : indices_engine existant + news_macro + Fear&Greed API

**Free vs Membre vs VIP** :
- Free: Matrix uniquement (pas de canvas live)
- Membre: Canvas + Matrix + Context badge
- VIP: Tout + Prédictions 24h ("Basé sur corrélations historiques, probabil 72%")

---

### 3️⃣ **MORNING BRIEF AMÉLIORÉ** (Upgrade feature existante)
**Niveau minimum** : Free (basique) / Membre (complet)  
**Où** : Déjà existe, upgrade contenu

**Ce qui change** :
- **Free** : 3 sections top (briefing simplifié)
  1. "🎯 Mouvements clés du jour"
  2. "⚠️ Risque macro identifié"
  3. "🔝 Top signal (1)"

- **Membre** : 8 sections complet (daily_report existant)
  1. Mouvements BTC/ETH
  2. Altcoins top gainers
  3. Liquidations 24h résumé
  4. Funding rates extrêmes
  5. Macro context (Fed/DXY/Sentiments)
  6. Signaux trading détectés
  7. Forex sessions opens
  8. Top risques identifiés

- **VIP** : 10 sections + Géopolitique
  1-8: Comme Membre
  9. "🌍 **Géopolitique Today**" — Événements géopolitiques + impact estimé sur crypto
     - Exemple: "Fed Powell parle à 14h (30min) → attention DXY spike possible → BTC short terme headwind"
  10. "🎯 **Setup du jour (Exclusif)**" — 1 setup validé avec conditions et historique

**Format** : HTML riche + Telegram simplifiée (2-3 blocs pour Telegram)

**Data source** : morning_brief.py existant + news_macro + news géopolitiques (NewsAPI?)

---

### 4️⃣ **VALIDATED TRADING SETUPS** (Nouvelle feature)
**Niveau minimum** : VIP only  
**Où** : Tab "💼 TRADING" → Nouvelle section "Setups Validés"

**Components** :
- **Setup Library** — Catalog de 10-15 setups prédéfinis
  - RSI Retrace (EMA aligned) : 72% WR, 12 trades, 2.1:1 RR
  - Liquidation Bounce : 65% WR, 8 trades, 1.8:1 RR
  - Funding Rate Reversal : 58% WR, 20 trades, 1.5:1 RR
  - COT Divergence : 68% WR, 5 trades, 2.4:1 RR
  - Macro Break (Fed decision) : 71% WR, 7 trades, 2.2:1 RR

- **Setup Details** — Pour chaque setup:
  - Description stratégie (2-3 phrases)
  - Timeframe optimal (1H, 4H, 1D)
  - Conditions entrée (prix, indicateurs, macro)
  - TP / SL (niveaux absolus + %)
  - Win rate historique + trade count
  - Exemple graphique (screenshot dernier setup validé)
  - Risk management (position sizing recommandé)

- **Active Setups** — Temps réel
  - "🟢 RSI Retrace à 43k BTC 1H actif" — TP: 45.2k | SL: 42k
  - Bouton "Start tracking" → notification quand TP ou SL

- **Setup API** (VIP bots) :
  - GET `/api/vip/setups` → JSON avec setup actifs
  - POST `/api/vip/setups/{id}/notify` → Email/Telegram si TP/SL

**Data source** : smart_signals.py + backtest_engine (historique validé)

---

## 💰 Pricing & Différenciation

### Free Tier
- ✅ Landing page + Sign up
- ✅ Morning Brief simplifié (3 sections)
- ✅ Whales (30 min delay)
- ✅ Liquidations (30 min delay)
- ✅ Corrélations matrix (pas live)
- ✅ Indices basiques (Fear, DXY, BTC dom)
- ✅ 1 alerte prix/jour max
- ✅ Accès landing Telegram (canal FREE)

**Conversion tactic** : "Débloquer brief complet + institutional flows live → upgrade Membre"

### Membre ($15-18/mois)
- ✅ Tout du Free +
- ✅ Morning Brief complet (8 sections)
- ✅ Institutional Dashboard live (liquidations, whales, funding)
- ✅ Corrélations visuelles (4-asset canvas)
- ✅ Signaux illimités
- ✅ Alertes prix illimitées
- ✅ Accès Telegram MEMBRE (canal privé, discussions)
- ✅ API public (read-only)

**Conversion tactic** : "C'est là qu'on devient opérationnel. Membership = équivalent 3 abonnements TradingView + Glassnode."

### VIP ($49-79/mois)
- ✅ Tout du Membre +
- ✅ Morning Brief VIP (10 sections + géopolitique)
- ✅ Setups validés + API
- ✅ Prédictions corrélations 24h
- ✅ Priorité email alerts (institutional flows)
- ✅ Groupe Telegram VIP privé (exclusif, toi + membres)
- ✅ Análisis géopolitique intégrée
- ✅ Accès early signaux (2h avant Membre)
- ✅ API avancée (webhooks pour bots)

**Conversion tactic** : "C'est l'insider pack. Accès aux setups + géopolitique + communauté = tu trades comme les pros."

---

## 🔄 Flux de Travail Utilisateur

### Free → Explore
1. Landing page : "Voici ce qu'on fait mieux"
2. Sign up
3. Morning Brief gratuit (3x/jour)
4. Explore indices, whales, correlations basiques
5. **Friction** : "Données live = Membre"

### Membre → Opérationnel
1. Subscribe $15/mois
2. Accès institutional dashboard en live
3. Corrélations + signaux trading
4. Setup Telegram Membre (discussions)
5. **Conversion to VIP** : "Setups + géopolitique = avantage compétitif"

### VIP → Insider
1. Subscribe $49-79/mois
2. Tout le monde + setups validés + géopolitique
3. Groupe Telegram VIP privé
4. Parfois 2h avant les autres
5. **Retention** : Haute valeur = churn très bas

---

## 🏗️ Technical Architecture

### Frontend Changes
- New tabs/sections en index.html:
  - "Institutional Flows" (canvas + heatmap)
  - "Corrélations Macros" (multi-asset chart)
  - "Setups Validés" (VIP library)
- Update Morning Brief HTML (vip, geopolitical sections)
- New modals pour setups détails

### Backend Changes
- **New APIs** :
  - `GET /api/institutional-flows` — liquidations + whales + funding (Membre+)
  - `GET /api/correlations` — multi-asset data (Membre+)
  - `GET /api/morning-brief/vip` — brief VIP avec géopolitique
  - `GET /api/vip/setups` — library setups + actifs
  - `POST /api/vip/setups/{id}/track` — user tracking
  - `WebSocket /ws/institutional` — live updates liquidations

- **Data enrichment** :
  - Liquidations Binance API integration (si pas encore)
  - Corrélations multi-asset (via existing indices_engine)
  - Géopolitique (news API: NewsAPI, GNews, ou manuel)
  - Setup validators (backtest_engine existant)

### Database Updates
- Table `setups` : (id, name, strategy, entry_conditions, tp, sl, wr, trades_count, created_at)
- Table `user_setup_tracking` : (user_id, setup_id, active, created_at)
- Column `user_role` : étendu (free/member/vip + timestamps)

### Permissions
- `is_free()` : Accès gratuit seulement
- `is_member()` : Membre + Free
- `is_vip()` : VIP + Membre + Free
- API checks: 403 si pas bon tier

---

## 📊 Success Metrics

| KPI | Target | Baseline |
|-----|--------|----------|
| Signups Free/semaine | 20+ | TBD |
| Free → Membre conversion | 5-10% | 0% |
| Membre churn rate | < 40%/mois | TBD |
| VIP retention | > 80% | TBD |
| Morning Brief opens | > 60% Membre | TBD |
| Institutional dashboard views | > 80 Membre | 0% |

---

## ⏱️ Phasing (Recommandé)

### Phase 1 : Institutional Dashboard (Week 1-2)
- Liquidations heatmap live
- Whale monitor upgradé
- Funding rate animator
- Smart signal generator basique

### Phase 2 : Corrélations Vivantes (Week 3)
- Multi-asset canvas
- Corrélation matrix
- Macro context badge

### Phase 3 : Morning Brief VIP (Week 4)
- Géopolitique intégrée
- Setup du jour

### Phase 4 : Validated Setups (Week 5-6)
- Setup library
- Tracking active
- API webhooks

---

## 📝 Notes Techniques

1. **Liquidations** : Utiliser `ccxt` Binance API (public, gratuit) ou intégrer webhook Glassnode si budget
2. **Corrélations** : Multi-timeframe possible mais complexe — start 7j/30j/90j seulement
3. **Géopolitique** : NewsAPI tier gratuit (1000 req/day) suffit si setup limité
4. **Setups** : Valider via backtest_engine existant avant d'afficher (pas de trades inventés)
5. **Telegram** : Déjà setup (2 canaux) — juste ajouter sauf Macro context

---

## ✅ Checklist de Validation

- [ ] Spec approuvée par product (toi)
- [ ] Mockups/wireframes crées si nécessaire
- [ ] Backend APIs répertoriées complètement
- [ ] Data sources identifiées (APIs, DBs)
- [ ] Permissions/tiers clairement modélisées
- [ ] Tests strategy définie
- [ ] Déploiement plan clairement

---

**Spec écrite par** : Claude Code (brainstorming skill)  
**Date approuvée** : 2026-05-05  
**Status final** : ✅ Ready for implementation planning
