# 📱 Guide Complet — Alertes Telegram CryptoScanner Pro

## 🎯 Vue d'ensemble

CryptoScanner Pro envoie **3 types d'alertes Telegram**:
1. **SMART SIGNALS** — Signaux de trading avancés (multi-critères)
2. **RETRACE RSI** — Rebonds RSI sur support/résistance
3. **MACRO EVENTS** — Événements macroéconomiques

Chaque alerte est **configurée et filtrée via le panneau ADMIN**.

---

## 📲 Configuration des Canaux Telegram

### Configuration requise

Avant d'utiliser les alertes, configurez ces variables dans `.env`:

```
TG_TOKEN=VOTRE_TOKEN_BOT
TG_CHAT=ID_CANAL_PRINCIPAL
TG_CHAT_FREE=ID_CANAL_FREE
```

**Où trouver ces valeurs?**

1. **TG_TOKEN** — Créez un bot avec [@BotFather](https://t.me/botfather) sur Telegram
   - Commande: `/newbot`
   - Recevez un token: `123456789:ABCdef...`

2. **TG_CHAT** — ID du canal principal (alertes VIP)
   - Créez un canal privé sur Telegram
   - Ajoutez votre bot au canal (+ Admin rights)
   - Trouvez l'ID: Envoyez un message au canal, puis utilisez:
     ```
     https://api.telegram.org/botTOKEN/getUpdates
     ```
   - Cherchez `chat.id` (sera négatif: `-1001234567890`)

3. **TG_CHAT_FREE** — ID du canal public (alertes gratuites)
   - Même processus que TG_CHAT

---

## ⚙️ Configuration des Alertes (Panneau ADMIN)

### Accès au panneau

1. Allez à: `https://46.225.234.71/admin`
2. Connectez-vous avec: `loloPrim` / `loloPrim0409@@`
3. Allez à l'onglet **ALERTES**

### 3 Blocs de Configuration

#### **Bloc 1: SMART SIGNALS**

```
Score minimum            → 85 (défaut)
  └─ Signaux avec score < 85 ne seront pas envoyés

Max alertes/cycle        → 3 (défaut)
  └─ Max 3 signaux par cycle de 2 minutes

Cooldown (heures)        → 24 (défaut)
  └─ Pas d'alerte dupliquée pendant 24h pour le même symbole
```

**Impacts:**
- Score ↓ = Plus d'alertes (bruit), mais plus sensible
- Score ↑ = Moins d'alertes, mais plus fiable
- Max alertes ↓ = Moins de spam
- Cooldown ↑ = Alertes plus espacées

#### **Bloc 2: RETRACE RSI**

```
RSI Oversold             → 30 (défaut)
  └─ Seuil de rebond à la baisse

RSI Overbought           → 70 (défaut)
  └─ Seuil de rebond à la hausse

Cooldown (heures)        → 12 (défaut)
  └─ Pas d'alerte dupliquée pendant 12h
```

**Impacts:**
- RSI Oversold ↓ = Rebonds plus extrêmes (moins d'alertes, plus fiables)
- RSI Oversold ↑ = Plus sensible (plus d'alertes)

#### **Bloc 3: MACRO EVENTS**

```
Importance minimale      → moyen (défaut)
  └─ Filtrer par importance: faible / moyen / élevé

Activer macro events     → OUI/NON
  └─ Activer/désactiver ce type d'alerte

Cooldown (heures)        → 6 (défaut)
```

#### **Bloc 4: PLATEFORME**

```
Canaux Telegram          → Sélectionner le canal (VIP ou FREE)
Heure du Morning Brief    → 08:00 (défaut)
Fuseau horaire           → Europe/Paris
```

---

## 📊 Types de Signaux Détaillés

### SMART SIGNALS

**Critères évalués:**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Volume
- Momentum
- Bollinger Bands

**Score:** 0-100
- **0-50:** Hésitant
- **50-70:** Modéré
- **70-85:** Fort
- **85-100:** Très fort ✅ (défaut pour alerte)

**Format du message Telegram:**
```
🔔 SIGNAL SMART #BTC 1h
━━━━━━━━━━━━━━━━━━━
📈 HAUSSIER (Score: 92)
━━━━━━━━━━━━━━━━━━━
RSI: 65 (neutre)
MACD: Positif (+2.5%)
Volume: +180% MA
Momentum: Fort ↗️

Entrée: $45,300
TP1: $46,000
SL: $44,500
```

### RETRACE RSI

**Signaux:**
- **Oversold Bounce:** RSI < 30 + rebond = BUY signal
- **Overbought Pullback:** RSI > 70 + correction = SELL signal

**Format du message:**
```
⚡ RETRACE RSI #ETH 4h
━━━━━━━━━━━━━━━━━━━
RSI: 28 (OVERSOLD) 🟢 ACHAT
━━━━━━━━━━━━━━━━━━━
Prix: $2,450
Supp: $2,400
Rés: $2,500

⏰ Robustesse: Haute
```

### MACRO EVENTS

**Événements surveillés:**
- Communiqués FOMC (USA)
- Réunions BCE (Europe)
- Rapports NFP (emploi USA)
- Données inflation
- Décisions taux de change
- Nouvelles réglementations crypto

**Format du message:**
```
🌍 MACRO EVENT: FOMC Decision
━━━━━━━━━━━━━━━━━━━
Impact: ÉLEVÉ 📊
⏰ 20:00 UTC Mercredi

Attendre décision...
Volatilité attendue: +20%

Risk/Reward: 1:2
```

---

## 🔄 Cycle d'envoi des Alertes

```
Toutes les 2 minutes:
  ├─ Calcul des signaux (tous les symboles)
  ├─ Filtrage par seuils (score minimum, cooldown)
  ├─ Sélection max N alertes
  └─ Envoi Telegram (si conditions remplies)
```

**Cooldown en action:**

```
T=0:00  → Signal #BTC score 90 → ENVOYÉ ✅
T=2:00  → Signal #BTC score 92 → BLOQUÉ (cooldown 24h)
T=2:02  → Signal #ETH score 88 → ENVOYÉ ✅
```

---

## 🎮 Commandes Telegram du Bot

### Disponibles pour les utilisateurs

```
/start           → Afficher menu principal
/status          → Statut actuel du scanner
/signals         → Derniers signaux détectés
/settings        → Modifier préférences personnelles
/help            → Aide et documentation
```

### Admin uniquement

```
/admin           → Accès panneau contrôle
/restart         → Redémarrer le service
/logs [N]        → Voir derniers N logs
/config          → Voir configuration actuelle
```

---

## 📈 Stratégies de Configuration Recommandées

### 🟢 Conservative (Peu d'alertes, haute fiabilité)

```
Score minimum SMART:     90
Max alertes/cycle:       1
Cooldown SMART:          48h
RSI Oversold:            25
RSI Overbought:          75
Cooldown RSI:            24h
```

**Résultat:** 3-5 alertes/jour, très fiables ✅✅✅

### 🟡 Moderate (Équilibre)

```
Score minimum SMART:     85 (défaut)
Max alertes/cycle:       3 (défaut)
Cooldown SMART:          24h (défaut)
RSI Oversold:            30 (défaut)
RSI Overbought:          70 (défaut)
Cooldown RSI:            12h (défaut)
```

**Résultat:** 10-20 alertes/jour, bon ratio signal/bruit ✅✅

### 🔴 Aggressive (Beaucoup d'alertes)

```
Score minimum SMART:     70
Max alertes/cycle:       5
Cooldown SMART:          12h
RSI Oversold:            35
RSI Overbought:          65
Cooldown RSI:            6h
```

**Résultat:** 30-50 alertes/jour, plus de bruit ⚠️

---

## 🐛 Dépannage

### Les alertes ne s'envoient pas

**Causes possibles:**

1. **Bot pas dans le canal**
   - Vérifiez que le bot est ajouté au canal avec Admin rights
   - Testez manuellement: `/start` au bot

2. **Mauvais ID de canal**
   - Vérifiez `TG_CHAT` dans `.env`
   - Format correct: `-1001234567890` (négatif)

3. **Score tous < minimum**
   - Baissez le seuil minimum temporairement
   - Vérifiez les logs: `/logs 50`

4. **Cooldown trop agressif**
   - Réduisez les heures de cooldown
   - Testez avec 1h au lieu de 24h

### Alertes en spam

**Solutions:**
- Augmentez le score minimum (85 → 90)
- Réduisez max alertes/cycle (3 → 1)
- Augmentez cooldown (24h → 48h)
- Créez un canal séparé pour les alertes agressives

### Connecté mais aucun signal

**Possibilités:**
- Marché plat (peu de volatilité)
- Tous les signaux < score minimum
- Tous en cooldown

**Test:** Baissez temporairement score minimum à 50 pour vérifier.

---

## 📊 Monitoring et Logs

### Vérifier les alertes envoyées

```bash
# Sur le serveur:
sudo journalctl -u cryptoscanner -n 50 | grep "Telegram"
```

### Format du log d'alerte

```
[Alert] Smart Signal: BTC 1h | Score: 92 | Status: SENT
[Alert] Retrace RSI: ETH 4h | RSI: 28 | Status: SENT
[Alert] Macro Event: FOMC | Impact: HIGH | Status: BLOCKED (cooldown)
```

---

## 💡 Astuces Pro

✅ **Combinez les types d'alertes:**
- SMART SIGNALS = Trading court terme
- RETRACE RSI = Entrées scalping
- MACRO EVENTS = Contexte + gestion de risque

✅ **Utilisez plusieurs canaux:**
- Canal VIP = Alertes agressives (score 70+)
- Canal FREE = Alertes conservatrices (score 90+)

✅ **Testez avant de déployer:**
- Configurez, testez 24h sur le serveur
- Vérifiez ratio signal/bruit
- Ajustez si nécessaire

✅ **Maintenez un journal:**
- Tracez chaque alerte reçue
- Comparez avec prix réel 1h plus tard
- Ajustez les paramètres mensuellement

---

## 📞 Support

- **Erreurs:** Consultez les logs via le panneau ADMIN
- **Questions:** Cf. documentation `/help` sur Telegram
- **Bugs:** Signalez via le formulaire d'erreur du dashboard

---

**Version:** 2.0 | **Mise à jour:** 2026-05-10 | **Status:** Complète ✅
