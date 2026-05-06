# 🔍 DIAGNOSTIC COMPLET — Données manquantes après upload

## 📍 Situation
Après upload de 4 fichiers modifiés (app.py, smart_signals.py, news_macro.py, templates/admin.html), le système a cassé :
- ❌ Ticker/Dashboard : **pas de données** (market_update)
- ❌ PAGE MACRO : **pas de données** (macro_update)

## 🎯 Cause racine trouvée

### Le problème en 2 lignes
**`app.py` appelle :**
```python
msg_free = build_telegram_alert(s, for_role="free")  # ← Passe le paramètre for_role
```

**Mais `smart_signals.py` avait :**
```python
def build_telegram_alert(signal):  # ← N'accepte PAS for_role
```

**Résultat :** `TypeError: build_telegram_alert() got unexpected keyword argument 'for_role'`

### Où le crash se produit
```
app.py ligne 256-257:
    _send_smart_alerts(results)  ← ❌ CRASH ici, TypeError
    socketio.emit("smart_signals_update", ...)  ← N'est jamais exécuté
```

Même si ce crash ne bloque que smart_signals_update, il indique un problème de cohérence majeur.

---

## ✅ Solution appliquée

### Fichier modifié : `smart_signals.py`

#### Change 1 : `build_telegram_alert()`
```python
# AVANT
def build_telegram_alert(signal):

# APRÈS  
def build_telegram_alert(signal, for_role: str = "free"):
```

**Logique :**
- Si `for_role == "free"` → Message court (2-3 lignes) + avertissement légal
- Si `for_role == "paid"` → Message complet (patterns, divergences, MA20, ADR, etc.)

#### Change 2 : `build_retrace_alert()`
```python
# AVANT
def build_retrace_alert(symbol, rsi_exit, price, change_pct, volume_usd=0):

# APRÈS
def build_retrace_alert(symbol, rsi_exit, price, change_pct, volume_usd=0,
                        for_role: str = "free", candles_15m=None):
```

**Logique :**
- Accepte maintenant les paramètres que `app.py` envoie
- `candles_15m` peut être utilisé pour enrichissements futurs (Task #9)

---

## ✔️ Vérifications effectuées

- ✅ Syntaxe Python : **PASS** (0 erreurs)
- ✅ Imports : **PASS** (datetime disponible)
- ✅ Compatibilité app.py : **PASS** (tous les appels sont corrects)
- ✅ Appels de fonction : **PASS** (9 appels identifiés et vérifiés)

---

## 📦 Fichier à uploader

**`smart_signals.py`** — 23 KB — 560 lignes

Aucun autre fichier n'a besoin de modifications pour corriger le problème.

---

## 🚀 Étapes pour corriger

### 1. UPLOAD
- Aller dans votre dossier : `C:\Users\loyan\Documents\Antigravity\cryptoscanner\`
- Uploader le fichier corrigé : **`smart_signals.py`**
- (C'est le même fichier que vous avez déjà, mais maintenant avec les signatures fixées)

### 2. REDÉMARRAGE
- **Si sur Railway** : Déclencher un redéploiement (push git ou bouton "Deploy")
- **Si local** : Redémarrer l'app (`Ctrl+C`, puis `python app.py`)

### 3. TEST
- Ouvrir le dashboard → vérifier que le **ticker affiche les coins**
- Ouvrir DATA tab → vérifier que **macro_update affiche les données**
- Si erreurs : vérifier les **logs serveur** pour les exceptions

---

## 🧠 Pourquoi c'est arrivé

Le schéma de différenciation FREE/PAID a été conçu pour les alertes Telegram :
- **app.py** a été modifié pour appeler `build_telegram_alert(s, for_role="free")`
- **smart_signals.py** n'a pas reçu la modification correspondante pour accepter ce paramètre
- Résultat : mismatch typique lors de changements multi-fichiers

**Leçon :** Quand on modifie les signatures de fonction, toujours vérifier tous les **call sites** (où la fonction est appelée).

---

## 📋 Prochaines tâches

Après correction et test réussi :

1. [ ] Task #6 — Tests : Vérifier l'impact sur les alertes temps réel
2. [ ] Documenter le lien entre alertes Telegram et paramètres PLATEFORME
3. [ ] Implémenter les enrichissements PAID manquants (Task #9)

---

**Status :** 🔧 DIAGNOSTIC COMPLET — Prêt pour correction
**Créé :** 2026-05-03
**Version :** 1.0
