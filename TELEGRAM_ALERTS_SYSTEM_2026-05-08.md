# 📡 SYSTÈME D'ALERTES TELEGRAM — Documentation Complète

**Date:** 2026-05-08  
**Objectif:** Clarifier la correspondance entre les pages ANALYSE, ADMIN et les alertes Telegram  
**Status:** Complet et vérifié  

---

## 🎯 VUE D'ENSEMBLE

### Structure Générale

```
PAGE ADMIN (Alertes)
    ├─ SMART SIGNALS ← Bloc 1 (Config paramètres)
    ├─ RETRACE RSI ← Bloc 2 (Config paramètres)
    └─ MACRO EVENTS ← Bloc 3 (Config paramètres)
           ↓
    PAGE ADMIN (Parametres)
    └─ PARAMETRES PLATEFORME (Config globale)
           ↓
    TELEGRAM CHANNELS (2 canaux)
    ├─ Canal PUBLIC (messages FREE)
    └─ Canal VIP/PAID (messages PAID)
```

---

## 📊 LES 3 BLOCS D'ALERTES EXPLIQUÉS

### Bloc 1: SMART SIGNALS 🧠 (Bleu)

**Correspondance:**
- **Page ANALYSE** → Onglet **SMART SIGNALS** (💎 PAID)
- Détecte les signaux d'achat/vente basés sur critères multi-factor
- Envoie alertes sur **2 canaux Telegram** (FREE + PAID)

**Paramètres du bloc SMART SIGNALS:**

| Paramètre | Valeur Actuelle | Signification |
|-----------|-----------------|---------------|
| **Score minimum** | 85 | Le signal doit avoir un score ≥85/100 pour être envoyé |
| **Variation PUMP (%)** | 4 | Alerte si prix monte > 4% en temps court |
| **Variation DUMP (%)** | -4 | Alerte si prix baisse > -4% en temps court |
| **Multiplicateur volume min** | 5 | Volume doit être 5x le volume moyen |
| **Critères minimum** | 3 | Au minimum 3 critères doivent être valides |
| **ADR % minimum** | 25 | Average Daily Range doit être > 25% |
| **Cooldown (heures)** | 1 | Attendre 1h avant de renvoyer alerte pour même coin |
| **Max par cycle** | 3 | Max 3 alertes SMART SIGNALS par cycle de scan |

**Comment ça fonctionne:**
```
Scanner détecte signal (RSI, MACD, Volume, etc.)
    ↓
Score = 85+ ? OUI
    ↓
Message Telegram envoyé:
- "🟢 BTC SIGNAL ACHAT — Score 92/100"
- Version FREE sur canal public
- Version PAID sur canal VIP (si abonné)
```

**Quand ça s'active:**
- Toutes les **5 secondes** (INTERVALLE SCAN = 5s)
- Scan tous les coins du marché
- Envoie alertes immédiatement si conditions remplies

---

### Bloc 2: RETRACE RSI 📈 (Vert)

**Correspondance:**
- **Page ANALYSE** → Onglet **SIGNAUX** (section "Distribution RSI")
- Détecte les extrêmes RSI (Overbought/Oversold)
- Basé sur la stratégie de "retrace" (rebond après extrême)

**Paramètres du bloc RETRACE RSI:**

| Paramètre | Valeur Actuelle | Signification |
|-----------|-----------------|---------------|
| **RSI surachat (limite)** | 85 | Alerte si RSI > 85 (overbought = vente probable) |
| **RSI survente (limite)** | 25 | Alerte si RSI < 25 (oversold = achat probable) |
| **Cooldown (heures)** | 1 | Attendre 1h avant alerte suivante même coin |

**Comment ça fonctionne:**
```
Scanner calcule RSI (14-period)
    ↓
RSI > 85 OU RSI < 25 ?
    ↓ OUI
Message Telegram envoyé:
- "🔴 BTC RSI 88 SURACHAT — Retrace probable"
- "🟢 BTC RSI 22 SURVENTE — Rebond probable"
- Version FREE sur canal public
- Version PAID sur canal VIP
```

**Stratégie derrière:**
- **RSI > 85** = Marché en surextension (↗️ trop fort) → Correction/Dump probable
- **RSI < 25** = Marché survendu (↘️ trop faible) → Rebond/Pump probable
- **Cooldown 1h** = Évite spam, attend 1h pour nouvelle alerte

---

### Bloc 3: MACRO EVENTS 📰 (Rouge)

**Correspondance:**
- **Page ANALYSE** → Onglet **COT** (nouvelles macro économiques)
- Événements économiques mondiaux affectant les cryptos
- Inflation, FOMC, NFP, etc.

**Paramètres du bloc MACRO EVENTS:**

| Paramètre | Valeur Actuelle | Signification |
|-----------|-----------------|---------------|
| **Filtre impact** | "High seulement" | Envoie SEULEMENT événements à **haut impact** |
| **Fenêtre début (UTC)** | 8 | Événements à partir de 8h UTC |
| **Fenêtre fin (UTC)** | 22 | Événements jusqu'à 22h UTC |

**Comment ça fonctionne:**
```
Event macro calendrier économique
    ↓
Impact = "HIGH" ? OUI
    ↓
Heure événement entre 8-22 UTC ? OUI
    ↓
Message Telegram envoyé:
- "📊 FOMC Decision 14:00 UTC — HAUT IMPACT"
- "Prévision: X% · Prédiction: Y%"
- Version PAID sur canal VIP (alertes macro = premium)
```

**Exemples d'événements macro:**
- 🏦 FOMC Decision (Federal Reserve)
- 📈 NFP (Non-Farm Payroll - emploi USA)
- 💹 Inflation CPI (Indice des prix)
- 💶 BCE Decision (Banque Centrale Européenne)
- 🇬🇧 BOE Decision (Banque Angleterre)

---

## ⚙️ PARAMETRES PLATEFORME (Global Settings)

**Ces paramètres affectent TOUS les blocs d'alertes:**

| Paramètre | Valeur | Impact sur Alertes |
|-----------|--------|-------------------|
| **SEUIL PUMP/DUMP (%)** | 1 | Variation minimale pour détecter pump/dump |
| **INTERVALLE SCAN (sec)** | 5 | Scan tous les 5 secondes |
| **MULTIPLICATEUR VOLUME SPIKE** | 1 | Volume doit être 1x le volume normal |
| **VOLUME MINIMUM 24H ($M)** | 2 | Coins avec < $2M volume/jour ignorés |
| **SCORE SIGNAL MINIMUM (0-100)** | 90 | Score ≥ 90 pour envoyer (SMART SIGNALS) |
| **MAX FEAR & GREED (Sécurité)** | -15 | Ne pas alerte si Fear&Greed < -15 (marché panique) |
| **EXCHANGE PAR DÉFAUT** | Binance | Données utilisées par défaut |
| **ADX MINIMUM (Tendance)** | 8 | Tendance forte minimale requise |
| **ADR MINIMUM (% Range)** | 1.9 | Average Daily Range minimum |
| **FILTRE EMA 200** | Activé | Prix > EMA200 requis (tendance haussière) |

---

## 📱 LES 2 CANAUX TELEGRAM EXPLIQUÉS

### Canal 1: PUBLIC (FREE)

**Objectif:** Messages gratuits pour tous les utilisateurs

**Contient:**
- ✅ SMART SIGNALS (version simplifiée)
- ✅ RETRACE RSI (signaux simples)
- ❌ MACRO EVENTS (non inclus)

**Format message FREE:**
```
🟢 BTC SIGNAL ACHAT
Score: 92/100
RSI: 35 (Survente)
Volume: 5.2x (Normal)
Entrée recommandée: $43,500
---
Telegram Public: t.me/cryptoscanner_public
```

**Qui reçoit:** Tous les utilisateurs avec `/subscribe`

---

### Canal 2: VIP/PAID (💎 PREMIUM)

**Objectif:** Alertes détaillées et exclusives pour abonnés

**Contient:**
- ✅ SMART SIGNALS (version complète + details)
- ✅ RETRACE RSI (stratégies détaillées)
- ✅ MACRO EVENTS (calendrier économique)
- ✅ Analyses techniques avancées
- ✅ Liquidations massives détectées
- ✅ Whale alerts (Balena tracking)

**Format message PAID:**
```
🟢 BTC SMART SIGNAL — DÉTECTION INTELLIGENTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Score: 92/100 (TRÈS FORT)
├─ RSI: 35 (Survente extrême)
├─ MACD: Croisement Bullish
├─ Volume: 5.2x (Accumulation)
├─ ADX: 32 (Tendance forte)
└─ EMA 200: Prix > EMA (Haussier)

💰 Entrée: $43,500
🎯 Target 1: $44,200 (+1.6%)
🎯 Target 2: $45,000 (+3.4%)
⛔ Stop Loss: $42,800 (-1.6%)

⏰ Cooldown: 1h (attendre avant alerte BTC)
---
Telegram Premium: t.me/cryptoscanner_vip
```

**Qui reçoit:** Utilisateurs PAID + VIP tiers

---

## 🔄 FLUX DE TRAVAIL COMPLET

### Scénario: BTC fait un SMART SIGNAL

```
1. SCAN (Toutes les 5 secondes)
   └─ App fetch BTC OHLCV depuis Binance

2. CALCUL INDICATEURS
   └─ RSI, MACD, ADX, Volume, EMA, ATR calculés

3. VÉRIFICATION CONDITIONS SMART SIGNALS
   ├─ Score ≥ 85? ✓
   ├─ Volume ≥ 5x? ✓
   ├─ RSI favorable? ✓
   ├─ ADX > 8? ✓
   └─ EMA200 filter? ✓

4. GÉNÉRATION MESSAGE
   ├─ Version FREE (basic)
   └─ Version PAID (détaillé)

5. ENVOI TELEGRAM (Multi-canal)
   ├─ POST Canal PUBLIC (FREE)
   └─ POST Canal VIP (PAID)

6. COOLDOWN
   └─ Attendre 1h avant nouvel alerte BTC

7. LOG HISTORIQUE
   └─ Enregistrement dans DB pour historique
```

---

## 📍 CORRESPONDANCE ADMIN ↔ ANALYSE

### Page ANALYSE: Onglet SMART SIGNALS

```
UI Affiche:
├─ Liste coins avec signaux actifs
├─ Score de chaque signal (0-100)
├─ Statut (Achat/Vente/Neutre)
├─ Critères validés (RSI, MACD, Volume, etc.)
└─ Sparklines pour historique

ADMIN Configure:
├─ Score minimum (85)
├─ Variation Pump/Dump (4% / -4%)
├─ Multiplicateur volume (5x)
├─ Critères minimum (3)
├─ ADR minimum (25%)
└─ Cooldown (1h)
```

### Page ANALYSE: Onglet SIGNAUX

```
UI Affiche:
├─ Tous les signaux détectés (RSI, MACD, Volume)
├─ Distribution RSI (histogramme)
├─ Signaux par catégorie
└─ Tendance générale marché

ADMIN Configure:
├─ RETRACE RSI bloc
│  ├─ RSI Overbought (85)
│  ├─ RSI Oversold (25)
│  └─ Cooldown (1h)
└─ PARAMETRES PLATEFORME
   ├─ Score minimum (90)
   ├─ ADX minimum (8)
   ├─ EMA 200 filter
   └─ Fear & Greed limit
```

### Page ANALYSE: Onglet COT

```
UI Affiche:
├─ Calendrier événements macro
├─ Impact (High/Medium/Low)
├─ Prédictions vs Résultats
└─ Impact sur marché

ADMIN Configure:
├─ MACRO EVENTS bloc
│  ├─ Filtre impact (High only)
│  ├─ Fenêtre UTC (8-22)
│  └─ Alertes Telegram
└─ Qui reçoit (PAID only)
```

---

## 🧪 TEST: Comment Vérifier que tout Marche

### Test 1: Déclencher SMART SIGNAL
```
1. Aller ADMIN → ALERTES → SMART SIGNALS
2. Baisser "Score minimum" de 85 → 50
3. Attendre 5-10 secondes
4. Devrait recevoir alerte Telegram dans 10 secondes
5. Remonter à 85 pour éviter spam
```

### Test 2: Vérifier RSI Retrace
```
1. Allez ANALYSE → SIGNAUX
2. Chercher coin avec RSI < 25 ou > 85
3. Vérifier que RETRACE RSI alerte reçue (si Telegram lié)
4. Vérifier cooldown 1h (pas 2 alertes d'affilée)
```

### Test 3: Macro Events
```
1. ADMIN → ALERTES → MACRO EVENTS
2. Mettre fenêtre début/fin dans l'heure actuelle
3. Attendre événement macro ou tester avec date futures
4. Devrait recevoir alerte PAID seulement
```

---

## 📋 CHECKLIST: Configuration Correcte

- [ ] **SMART SIGNALS** bloc présent et configurable
- [ ] **RETRACE RSI** bloc présent et configurable
- [ ] **MACRO EVENTS** bloc présent et configurable
- [ ] **Telegram lié** dans AUTH (Chat ID présent)
- [ ] **Alertes Telegram** activées dans PREFS
- [ ] **2 canaux** reçoivent messages (Public + VIP)
- [ ] **Score minimum** adapté (85 est good)
- [ ] **Cooldown** fonctionne (1h = pas de spam)
- [ ] **Messages FREE** sur canal public
- [ ] **Messages PAID** sur canal VIP seulement

---

## 🔒 SÉCURITÉ & PERMISSIONS

### Par Tier:

**FREE Users:**
- ✅ Reçoivent SMART SIGNALS (version simple)
- ✅ Reçoivent RETRACE RSI (base)
- ❌ N'ont pas accès MACRO EVENTS
- ❌ N'ont pas accès onglet SMART SIGNALS (💎 PAID)

**PAID/VIP Users:**
- ✅ Reçoivent SMART SIGNALS (détaillé)
- ✅ Reçoivent RETRACE RSI (avancé)
- ✅ Reçoivent MACRO EVENTS
- ✅ Accès onglet SMART SIGNALS
- ✅ Signaux plus précis et rapides

---

## 📞 TROUBLESHOOTING

### Pas de Telegram?
```
1. ADMIN → PARAMETRES → Scroll down
2. Vérifier "Telegram lié" = YES
3. Si NON → AUTH → PROFIL → Link Telegram Chat ID
4. Envoyer /start au bot Telegram
5. Copier Chat ID et passer dans AUTH
```

### Alertes trop fréquentes?
```
1. ADMIN → ALERTES → SMART SIGNALS
2. Augmenter "Score minimum" (85 → 90)
3. Augmenter "Cooldown" (1h → 2h)
4. Baisser "Variation PUMP/DUMP" (moins sensible)
```

### Alertes pas assez fréquentes?
```
1. ADMIN → ALERTES → SMART SIGNALS
2. Baisser "Score minimum" (85 → 70)
3. Baisser "Cooldown" (1h → 30min)
4. Baisser "Critères minimum" (3 → 2)
```

---

## 📊 RESUME FINAL

| Bloc | Canal | Fréquence | Trigger |
|------|-------|-----------|---------|
| **SMART SIGNALS** | PUBLIC + VIP | Toutes les 5s | Score ≥85 + Conditions |
| **RETRACE RSI** | PUBLIC + VIP | Toutes les 5s | RSI > 85 ou < 25 |
| **MACRO EVENTS** | VIP ONLY | Événement | Impact HIGH + Fenêtre UTC |

---

**Document:** Telegram Alerts System Documentation  
**Validé:** 2026-05-08  
**Prêt:** Pour clarifier auprès des utilisateurs  

