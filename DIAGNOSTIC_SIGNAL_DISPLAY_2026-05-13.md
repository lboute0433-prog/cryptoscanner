# Diagnostic: Pourquoi les signaux ne s'affichent pas en ANALYSE/SMART SIGNALS

**Date:** 2026-05-13  
**Problem:** Les signaux ne s'affichent pas dans ANALYSE > SMART SIGNALS  
**Objectif:** Identifier le point de blocage

---

## 🔍 Checklist de Diagnostic

### 1. Cache des signaux: Sont-ils détectés?

**Question:** Y a-t-il des signaux dans `_smart_signals_cache`?

**Où vérifier:**
- Logs du serveur (app.py smart_signal_loop)
- Vérifier que `smart_signal_loop()` tourne
- Vérifier le WebSocket `smart_signals_update` est émis

**Possible Issues:**
- ❌ smart_signal_loop pas lancé → aucun signal détecté
- ❌ Les symbols ne génèrent pas de signaux → cache vide
- ❌ WebSocket pas émis → frontend ne reçoit pas

---

### 2. Score des signaux détectés

**Question:** Les signaux détectés ont-ils score >= score_min?

**Context:**
- score_min actuel: **70** (d'après nos tests)
- Signaux affichés seulement si score >= 70

**Possible Issues:**
- ❌ Tous les signaux détectés ont score < 70 → API filtre tout
- ❌ Score_min a changé sans reload → cache a signaux mais API les filtre
- ⚠️ Peu de signaux détectés (normal, il faut conditions particulières)

---

### 3. API /api/smart_signals: Retourne-t-elle des signaux?

**Question:** L'endpoint retourne-t-il des signaux?

**Test:**
```bash
curl https://46.225.234.71/api/smart_signals?role=paid

Response devrait être:
{
  "signals": [
    {"symbol": "BTC", "score": 75, ...},
    {"symbol": "ETH", "score": 68, ...},
    ...
  ],
  "score_min": 70,
  "ts": "12:34:56"
}
```

**Possible Issues:**
- ❌ Cache vide → signals: []
- ❌ Tous les signaux filtrés → signals: [] (si tous < 70)
- ❌ Erreur API → 500 error
- ❌ score_min très haut → filtre trop agressif

---

### 4. Frontend: Charge-t-il les signaux?

**Question:** Le JavaScript charge-t-il les signaux via l'API?

**Code:**
```javascript
// index.html loadSmartSignals()
const res = await fetch('/api/smart_signals?role=paid');
const data = await res.json();
smartSignalsData = data.signals || [];
renderSmartSignals(smartSignalsData);
```

**Possible Issues:**
- ❌ /api/smart_signals retourne vide
- ❌ Fetch échoue (CORS, SSL, etc)
- ❌ renderSmartSignals() affiche rien (affiche message "Aucun signal")

---

## 🛠️ Plan de Diagnostic

### STEP 1: Vérifier le Cache du Serveur

**Commande SSH:**
```bash
ssh root@46.225.234.71

# Vérifier si smart_signal_loop tourne
ps aux | grep smart_signal

# Vérifier les logs récents
tail -100 /var/log/gunicorn.log | grep -i signal
```

**Ou directement via debug UI:**
- Ajouter endpoint temporaire pour afficher `_smart_signals_cache`

---

### STEP 2: Vérifier l'API en Direct

**Test curl:**
```bash
curl -k https://46.225.234.71/api/smart_signals?role=paid

# Si vide, ajouter logs en app.py:1586
print(f"[DEBUG] Cache contents: {_smart_signals_cache[:2]}")
print(f"[DEBUG] Score_min: {score_min}")
print(f"[DEBUG] Filtered count: {len(filtered_signals)}")
```

---

### STEP 3: Vérifier la Network en Frontend

**Dans le navigateur (F12):**
1. Ouvre DevTools → Network tab
2. Va ANALYSE > SMART SIGNALS
3. Cherche la requête `/api/smart_signals`
4. Verifie:
   - Status: 200 OK?
   - Response: JSON avec signals?
   - Response size > 100 bytes?

**Si 200 OK mais signals vide:**
```json
{
  "signals": [],
  "score_min": 70,
  "ts": "12:34:56"
}
```
→ Cache vide OU tous les signaux filtrés

---

## 🎯 Diagnostics Probables

### Problème 1: Cache Vide

**Symptôme:** `/api/smart_signals` retourne signals: []

**Cause:**
- smart_signal_loop() n'a pas détecté de signals
- Pas assez de conditions réunies pour génerer des signaux
- smart_signal_loop() pas actif

**Solution:**
- Vérifier logs smart_signal_loop()
- Attendre quelques cycles (2-5 minutes)
- Vérifier que analyze_coin_smart() détecte effectivement

---

### Problème 2: Tous les Signaux Filtrés

**Symptôme:** Cache a signals mais API retourne vide

**Cause:**
```python
# app.py:1618
for signal in _smart_signals_cache:
    if signal.get("score", 0) < score_min:
        continue  # Skip tous les signaux!
```

**Solutions:**
- Baisser score_min (Admin)
- Ou vérifier les scores des signaux en cache

---

### Problème 3: WebSocket Pas Émis

**Symptôme:** Frontend reçoit rien

**Code concerné:**
```python
# app.py:349
socketio.emit("smart_signals_update", 
              {"signals": _smart_signals_cache, "ts": _smart_signals_ts})
```

**Vérifier:**
- Console du navigateur (F12) → Messages WebSocket
- Chercher "smart_signals_update"

---

## 📋 Quick Diagnostic Checklist

```
[ ] 1. Vérifier que smart_signal_loop() tourne (ps aux)
[ ] 2. Vérifier logs: Y a-t-il des "[SmartSignals]" messages?
[ ] 3. Appeler /api/smart_signals en curl
    [ ] 3a. Status 200?
    [ ] 3b. "signals": [] ou ["data"]?
    [ ] 3c. score_min valeur?
[ ] 4. Vérifier score_min actuel (Admin UI)
[ ] 5. Frontend Network tab: /api/smart_signals response
[ ] 6. Frontend Console: Errors?
[ ] 7. Vérifier que symbols sont analyzed (logs)
```

---

## 🎯 Next Steps

1. **Vérifie cache:**
   - Va dans app.py ligne 327 (cache update)
   - Ajoute: `print(f"[CACHE] Updated {len(results)} signals, cached {len(_smart_signals_cache)}")`
   - Redeploy
   - Observe logs

2. **Vérifie API:**
   - Curl `/api/smart_signals?role=paid`
   - Compte les signaux retournés
   - Si 0 → vérifier pourquoi

3. **Vérifie Frontend:**
   - DevTools Network tab
   - Voir la réponse de l'API
   - Si vide → cache vide
   - Si data → pourquoi pas affiché?

---

**Status:** À INVESTIGUER
**Root Cause:** À DETERMINER (cache, API filter, ou frontend)

Donne-moi le résultat de ces checks et je peux identifier le problème exact!
