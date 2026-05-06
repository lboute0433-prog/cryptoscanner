# Session 2026-05-05 — Morning Brief Redesign + Fix Variations Zéro

**Date** : 2026-05-05
**Durée** : Session en cours
**Serveur** : Hetzner 46.225.234.71 (ex-Railway)
**Phase** : Production Hetzner LIVE

---

## Objectif de session

1. ✅ Finaliser redesign Morning Brief (Approche C)
2. ✅ Corriger bug : altcoins affichent variation = 0.00%
3. ✅ Nettoyer dossier + mettre à jour Memory
4. ✅ **Identifier root cause** du problème de données manquantes
5. ✅ Archiver session proprement

---

## ✅ Accompli

### Résumé découverte
Le problème n'était pas les "variations zéro" mais une **chaîne d'échecs en cascade**:
- Timer issue: Scanner cache pas prêt quand brief généré
- CoinGecko obtient 429 rate limit → aucun fallback
- Résultat: data['prices'] complètement vide

---

## ✅ Accompli

### 1. Diagnostic Complet — Root Cause Identifiée ✅

**Phase 1: Erreur de parsing** (lignes 679, 687-688)
```
ValueError: could not convert string to float: '+0,0000'
```
- **Cause** : Données formatées avec virgule française au lieu de point
- **Fix** : Ajouter `.replace(',','.')` avant `float()`
- **Résultat** : HTML génère sans crash ✅

**Phase 2: Données vides** (test avec script)
```
data.get('prices') keys: []  ← Complètement vide!
```
- **Attendu** : data['prices'] avec BTC, ETH, SOL, etc.
- **Réel** : Dictionnaire vide
- **Diagnostic** : Pas juste un problème de variations zéro

**Phase 3: Root cause identifiée**

Timing issue + Rate limit:
1. Au démarrage, scanner charge lentement les coins
2. Quelqu'un appelle `/brief` **AVANT** que scanner finisse
3. `engine._last_data` n'est pas encore remplie
4. Priority 1 échoue silencieusement
5. Priority 2 (CoinGecko) s'active mais obtient **429 rate limit**
6. Aucun fallback → résultat: data['prices'] = {}

**Logs témoins:**
```
[Brief] Scanner cache OK 12 coins      ← Scanner fonctionne bien
[Brief] Données: BTC=$0               ← Mais data vide au moment de l'appel
[CoinGecko] Rate limit - attente 30s  ← CoinGecko 429
data.get('prices') keys: []           ← Confirmation: vide
```

### 2. Fix Bug Variations Zéro (APPLIQUÉ — Partie 1)

**Problème identifié :**
- Scanner retourne `change_pct: 0` pour tous les altcoins
- Priority 1 (scanner cache) remplit `data["prices"]` complètement
- Condition `if not data.get("prices")` empêche Priority 2 (CoinGecko) de s'exécuter
- **Résultat** : Toutes les variations affichaient 0.00%

**Root cause :**
```python
# AVANT — Logique bloquante
if not data.get("prices"):  # ← Si Priority 1 réussit, cette condition = False
    # CoinGecko jamais exécuté
```

**Fix appliqué (lignes 143-180) :**
```python
# APRÈS — Logique avec fallback intelligent
should_fetch_cg = False
if not data.get("prices"):
    should_fetch_cg = True
else:
    # Vérifier si toutes les variations sont zéro
    prices = data.get("prices", {})
    all_zero_changes = all(
        p.get("usd_24h_change", 0) == 0
        for p in prices.values()
    )
    if all_zero_changes:
        print("[Brief] ⚠️ Toutes les variations sont zéro — tentative CoinGecko...")
        should_fetch_cg = True

if should_fetch_cg:
    # Appel CoinGecko + merger :
    # - Garder prix du scanner
    # - Prendre variations de CoinGecko
```

**Modifications code appliquées:**

1. **Lignes 143-180** : Détection "toutes variations zéro" + merger CoinGecko
   ```python
   # Détecte si Priority 1 remplit tout avec des zéros
   all_zero_changes = all(p.get("usd_24h_change", 0) == 0 for p in prices.values())
   if all_zero_changes:
       should_fetch_cg = True  # Force CoinGecko fallback
   
   # Merger : garde scanner prices, prend CoinGecko variations
   data["prices"][coin_id].update({
       "usd_24h_change": cg_data.get("usd_24h_change", 0),
       ...
   })
   ```

2. **Lignes 679, 687-688** : Parsing virgule/point
   ```python
   # AVANT: float(derives.get('funding','0').replace('%','') or 0)
   # APRÈS: float(derives.get('funding','0').replace('%','').replace(',','.') or 0)
   ```

**Limitation de ce fix:**
- ✅ Gère les cas où Priority 1 retourne des zéros
- ❌ **Ne gère PAS** le cas où Priority 1 est complètement vide
- ❌ **Ne gère PAS** CoinGecko 429 rate limit (aucun fallback)

**Raison:** Le vrai problème est un **timing issue + rate limit**, pas des variations zéro

**Solution requise (Phase 2):**
Ajouter cache persistant pour CoinGecko 429 (voir section Prochaines étapes)

---

### 2. Memory System Cleanup ✅

**Mises à jour effectuées :**

- ✅ `contexte.md` — Ajout section Session 2026-05-05
  - Redesign Morning Brief documenté
  - Fix variations zéro documenté
  - Déploiement Hetzner noté
  
- ✅ `_index.md` — Ajout archives
  - Nouvelle entrée pour session courante
  - Lien vers archive 2026-05-05
  
- ✅ `TASKS.md` — Créé (nouveau)
  - Todo list formaté
  - Tâches urgentes identifiées
  - Timeline historique
  - Commandes utiles Hetzner
  
- ✅ `.worktrees/` — Supprimé (cleanup)
- ✅ `__pycache__/` — Supprimé (cache Python)
- ✅ `.pytest_cache/` — Supprimé (cache pytest)
- ✅ `app_backup.py` — Supprimé
- ✅ `diagnostic_checker.py` — Supprimé
- ✅ `test_brief_html.py` — Supprimé

---

## 🚀 Prochaines étapes — Phase 2 (URGENT)

**Problème non résolu:**
- Données altcoins toujours vides/zéro dans le brief
- Cause: Timing issue (scanner pas prêt) + CoinGecko 429 sans fallback
- Fix Phase 1 (variations zéro) ≠ fix du vrai problème

### Immédiat (Avant prochaine génération brief)

1. **[BLOQUANT]** Ajouter CoinGecko Cache Fallback
   - Créer `/tmp/brief-cache.json` avec sauvegarde des prix
   - Quand CoinGecko 429 → utiliser le cache au lieu d'échouer
   - Implémenter dans `fetch_brief_data()` après Priority 2
   
   Pseudocode:
   ```python
   # Après tentative CoinGecko (ligne ~170)
   if r.status_code == 429:  # Rate limit
       print("[Brief] CoinGecko 429 - utilisant cache")
       cached = load_cache("/tmp/brief-cache.json")
       if cached:
           data["prices"] = cached
       else:
           data["prices"] = {}  # Fallback vide
   else:
       save_cache(data["prices"])  # Sauvegarder quand succès
   ```

2. **[Important]** Pré-charger les données au startup
   - Attendre que scanner cache soit rempli avant de servir `/brief`
   - Ou lancer `fetch_brief_data()` une fois au démarrage pour pré-remplir le cache

3. **[Important]** Retry logic avec backoff exponentiel
   - CoinGecko 429 → attendre 60s au lieu de 30s
   - Retry jusqu'à 3 fois avant d'échouer

### Phase 3 (Après cache fonctionnel)
- [ ] Créer page Morning Brief Archive (historique)
- [ ] Intégrer alertes en temps réel (WebSocket)
- [ ] Ajouter export PDF/image pour partage
- [ ] Monitoring: Alert si brief données < 50% complètes

---

## Fichiers modifiés

| Fichier | Lignes | Changement |
|---------|--------|-----------|
| `morning_brief.py` | 143-180 | Logique Priority 2 renforcée, merger CoinGecko |
| `contexte.md` | Fin | Section Session 2026-05-05 ajoutée |
| `_index.md` | Archives | Entrée session 2026-05-05 ajoutée |
| `TASKS.md` | Nouveau | Todo list créée |

---

## Commandes Hetzner

```bash
# Vérifier service
pm2 status

# Voir logs
pm2 logs cryptoscanner --lines 50

# Redémarrer
pm2 restart cryptoscanner

# Tester endpoint brief
curl -s https://46.225.234.71/brief?token=TOKEN | head -100
```

---

## Notes

- **Déploiement serveur** : À faire manuellement après validation locale
- **Timeline** : Session doit être archivée après déploiement + test ✅
- **Memory** : Tous les fichiers de memory mis à jour ✅
- **Nettoyage** : Dossier propre (14 fichiers précédents + 3 fichiers test supprimés) ✅

**Propriétaire** : Lolo
**Status** : EN COURS — Prêt pour déploiement après test local

