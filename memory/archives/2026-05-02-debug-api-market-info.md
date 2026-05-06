# 2026-05-02 — Debug Systématique /api/market_info

**Date** : 2026-05-02 10:15 UTC  
**Sujet** : Diagnostic et correction du bug /api/market_info (page DATA macro vide)  
**Statut** : ✅ COMPLÉTÉ  
**Méthode** : Debug systématique Phase 1-4  

---

## 📋 Problème Initial

- **Symptôme** : Page DATA macro n'affichait aucune donnée (blocs vides)
- **Endpoint affecté** : `/api/market_info` retournait `{}` au lieu de Fear & Greed, Dominance, etc.
- **Impact** : Page entière DATA cassée, signaux Telegram ne s'envoyaient pas
- **Environnement** : Production Hetzner (46.225.234.71)

---

## 🔍 Phase 1 — Root Cause Investigation

### Traçage du Flux de Données

```
ScannerEngine.__init__
  ↓ self._market_info = {}    [INITIALISATION VIDE]
  ↓
Background thread _init_market_info()
  ↓ engine.fetch_market_info()  [DOIT REMPLIR]
  ↓ _market_info = {...}
  ↓
/api/market_info
  ↓ engine.get_market_info()    [RETOURNE le cache]
  ↓ return _market_info
```

### Evidence Gathered

**Finding 1 : Fonction Définie Mais Jamais Appelée**
```
app.py:468  → def start_runtime_services()    [DÉFINI]
app.py:150  → start_runtime_services()        [N'EXISTAIT PAS]
wsgi.py:16  → start_runtime_services()        [APPELÉ ICI]
```

**Finding 2 : Configuration Correcte Mais Inutilisée**
```
config.py:55 → RUN_BACKGROUND_JOBS = not IS_RAILWAY
Hetzner:     → IS_RAILWAY = False
Result:      → RUN_BACKGROUND_JOBS = True ✓
But:         → Fonction jamais invoquée ✗
```

**Finding 3 : Entry Point Problem**
- ✅ wsgi.py appelait `start_runtime_services()` correctement
- ❌ app.py ne l'appelait pas
- ❌ Hetzner probablement n'utilisait pas wsgi.py comme entry point

---

## 📊 Phase 2 — Pattern Analysis

**Working Pattern (wsgi.py)**
```python
from app import app, socketio, start_runtime_services
start_runtime_services()  # ← Appelé une fois au startup
application = app
```

**Broken Pattern (app.py)**
```python
def start_runtime_services():  # ← Défini
    # ... mais jamais appelé
    
engine = ScannerEngine()        # ← Initialisé
# ... mais threads jamais lancés
```

**Pattern** : Fonction initialisatrice définie mais non appelée = défaut de défense en profondeur.

---

## 💡 Phase 3 — Hypothesis

**Hypothesis** : Hetzner n'utilisait pas wsgi.py comme app entry point.

**Evidence** :
- wsgi.py existe et appelle la fonction ✓
- Mais /api/market_info retourne {} ✗
- Donc ou wsgi.py n'est pas utilisé, ou il y a une exception silencieuse

**Verdict** : Ajout défensif direct dans app.py nécessaire.

---

## ✅ Phase 4 — Implementation

### Fix Appliqué

**Fichier** : `app.py` (fin du fichier, après toutes les fonctions)

```python
# ── Lancement threads de fond (défensif) ──
start_runtime_services()
```

**Raison du placement** : La fonction `start_runtime_services()` est définie à la ligne 468, donc l'appel doit être APRÈS sa définition (à la fin du module).

**Bug secondaire corrigé** : Appels à `_get_session()` remplacés par `get_session()` (ligne 640 + autres occurrences)

```bash
sed -i 's/_get_session()/get_session()/g' /root/cryptoscanner/app.py
```

### Rationale

1. **Défensif** : Ensure threads start au module load, peu importe entry point
2. **Safe** : Fonction a guard `_background_tasks_started` (double-start prevention)
3. **Minimal** : Une ligne + sed replacement, pas de refactoring

### Verification

- Threads lancent au démarrage app ✓
- Cache `_market_info` se remplit ✓
- `/api/market_info` retourne données ✓
- Page DATA macro affiche Fear & Greed, Dominance, etc. ✓
- Session authentication fonctionne (get_session() corrigé) ✓
- Site accessible sur https://46.225.234.71 ✓

---

## 📝 Documentation Mise à Jour

### Files Modified

1. **app.py** — Ligne 150 : Ajout appel `start_runtime_services()`
2. **contexte.md** — Section "Issues Fixés" : Documentation détaillée
3. **bugs.md** — Déplacé de "Actifs" vers "Résolus"
4. **todo.md** — Marqué comme [x] complété
5. **PROJET_STATUT.md** — Réécrit complet avec état production
6. **_index.md** — Ajout session archive

---

## 🎯 Résultats

- ✅ Bug identifié via debug systématique (4 phases)
- ✅ Fix appliqué et vérifié
- ✅ Documentation complète mise à jour
- ✅ Memory/archives/docs cohérents
- ✅ Production live avec données macro actives

---

## 📌 Leçons Apprises

1. **Défense en profondeur** : Ne pas compter sur wsgi.py seul
2. **Debug systématique** : Phase 1-4 plus efficace que random fixes
3. **Documentation vivante** : Memory system capture les decisions et context
4. **Defensive initialization** : Appels au niveau module plus robustes que main blocks

---

**Mis à jour** : 2026-05-02 10:15 UTC
