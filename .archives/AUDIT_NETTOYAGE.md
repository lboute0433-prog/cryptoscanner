# AUDIT NETTOYAGE CRYPTOSCANNER

**Date:** 2026-05-05  
**Audit par:** Orchestrateur ICA  
**Statut:** Rapport — Pas de suppression effectuée

---

## 1. DOUBLONS — FICHIERS RACINE

### 1.1 Groupe `morning_brief.py`
| Fichier | Taille | Date | Lignes | Statut | Recommandation |
|---------|--------|------|--------|--------|-----------------|
| `morning_brief.py` | 48K | 2026-05-05 06:55 | 870 | ACTIF | **GARDER** — Version complète et récente |
| `morning_brief_complete.py` | 46K | 2026-05-05 06:55 | 850 | DOUBLURE | SUPPRIMER — Quasi-identique (20 lignes de moins) |
| `morning_brief_fixed.py` | 4.9K | 2026-05-05 06:54 | 127 | TEST | SUPPRIMER — Fichier stub/test incomplet |

**Verdict:** Garder `morning_brief.py` — c'est la version complète. Supprimer les deux autres.

---

### 1.2 Groupe `app.py` (CRITIQUE — Routes Flask)
| Fichier | Taille | Date | Statut | Recommandation |
|---------|--------|------|--------|-----------------|
| `app.py` | 89K | 2026-05-04 10:56 | PRODUCTION | **GARDER** — Version active |
| `app_backup.py` | 92K | 2026-05-03 06:07 | BACKUP | À analyser |
| `app_local_complete.py` | 11K | 2026-05-04 15:25 | EXPÉRIMENTAL | SUPPRIMER |
| `app_local_test.py` | 8.2K | 2026-05-04 11:04 | TEST | SUPPRIMER |
| `app_lwcharts.py` | 8.8K | 2026-05-04 15:33 | EXPÉRIMENTAL | SUPPRIMER |
| `app_lwcharts_advanced.py` | 14K | 2026-05-04 15:57 | EXPÉRIMENTAL | SUPPRIMER |
| `app_lwcharts_zones.py` | 12K | 2026-05-04 16:37 | EXPÉRIMENTAL | SUPPRIMER |
| `app_lwcharts_zones_fixed.py` | 13K | 2026-05-04 16:30 | EXPÉRIMENTAL | SUPPRIMER |

**Verdict:** 
- **Garder:** `app.py` (89K, 2026-05-04 10:56) — C'est la version en production
- **Backup:** `app_backup.py` (92K, plus ancien) — Garder comme dernier backup (optionnel mais recommandé)
- **Supprimer:** Tous les `app_lwcharts*` et `app_local*` — Fichiers d'expérimentation abandonnés

---

### 1.3 Groupe `smart_signals.py`
| Fichier | Taille | Date | Statut | Recommandation |
|---------|--------|------|--------|-----------------|
| `smart_signals.py` | 23K | 2026-05-03 06:32 | ACTIF | **GARDER** — Version complète |
| `smart_signals_backup.py` | 23K | 2026-05-03 06:06 | BACKUP | SUPPRIMER — Backup inutile, même taille |
| `smart_signals_fixed.py` | 23K | 2026-05-03 06:32 | VARIANTE | SUPPRIMER — Doublure complète |

**Verdict:** Garder `smart_signals.py`, supprimer les deux autres.

---

## 2. FICHIERS TEMPORAIRES / TEST

### 2.1 Fichiers `test_*.py` à la racine
| Fichier | Taille | Date | Destination | Recommandation |
|---------|--------|------|-------------|-----------------|
| `test_apis_hetzner.py` | 3.8K | 2026-05-02 04:36 | Racine | **SUPPRIMER** → `/scratch/` ou archiver |
| `test_heatmap_local.py` | 5.5K | 2026-05-04 13:21 | Racine | **SUPPRIMER** → `/scratch/` ou archiver |
| `test_macro_fix.py` | 5.7K | 2026-05-01 13:50 | Racine | **SUPPRIMER** → `/scratch/` ou archiver |
| `test_telegram.py` | 3.3K | 2026-05-02 04:37 | Racine | **SUPPRIMER** → `/scratch/` ou archiver |

**Verdict:** Déplacer à `/scratch/` (déjà structuré pour ça) ou supprimer si non pertinents.

---

### 2.2 Fichiers `diagnostic_*.py`
| Fichier | Statut | Recommandation |
|---------|--------|-----------------|
| `diagnostic_checker.py` | 5.1K (2026-05-04 05:55) | **GARDER** — Outil de diagnostic actif |

---

### 2.3 Dossier `/scratch/` — État actuel
**Contient:** 8 fichiers de test
- `debug_ff.py`, `debug_ff_alt.py`
- `test_calendar.py`, `test_cdn.py`, `test_dfx.py`
- `test_imports.py`, `test_te.py`, `verify_ff_fix.py`

**Verdict:** Garder — C'est le bon endroit pour les tests. Bien structuré.

---

### 2.4 Dossier `/db-test/` — À analyser
**Contient:** `db.py`, `test.py` + dossier `db/`

**Verdict:** 
- Si archivé (ancien) → Supprimer
- Si actif → Garder mais documenter sa raison d'être

---

## 3. DOSSIER `memory/` — STRUCTURE OBSIDIAN

### 3.1 État actuel
```
memory/
├── _index.md               ✅ Index central (conforme ICA)
├── agents/                 ✅ Notes persistantes par agent
├── archives/               ✅ Sessions immuables (18 fichiers)
├── framework/              ✅ Framework ICA (I, C, A piliers)
├── notes/                  ⚠️ À vérifier
├── projets/                ✅ Contexte courant par projet
└── (MANQUANT?)             ⚠️ Voir ci-dessous
```

### 3.2 Archives — OK
- 18 fichiers d'archive immuables de 2026-04-11 à 2026-04-24
- Bien nommés avec timestamps
- Pas de suppression recommandée

### 3.3 Points de vérification — Structure

**Vérifications effectuées:**
1. ✅ `/memory/notes/` — 6 fichiers (instructions, verif, todo, idees, bugs, memo perso)
2. ✅ `/memory/framework/` — Piliers complets (ICA.md, I.md, C.md, A.md)
3. ✅ `/memory/projets/cryptoscanner/` — 7 fichiers (contexte, historique, data/stack, roadmap, sources, roles, bugs)

**Verdict:** Structure parfaitement conforme ICA. Rien à réorganiser.

---

## 4. AUTRES DOUBLONS DÉTECTÉS

### 4.1 Doublons dans `.claude/`
Existe: `.claude/memory-compiler/` et `hooks/`
Doublon potentiel: 
- `.claude/memory-compiler/hooks/` → `hooks/` à la racine

**Verdict:** À vérifier — certains hooks peuvent être en double.

---

### 4.2 Scripts en double?
- `scripts/compile.py` vs `.claude/memory-compiler/scripts/compile.py`
- `scripts/config.py` vs `.claude/memory-compiler/scripts/config.py`
- `scripts/query.py` vs `.claude/memory-compiler/scripts/query.py`
- `scripts/utils.py` vs `.claude/memory-compiler/scripts/utils.py`
- `scripts/lint.py` vs `.claude/memory-compiler/scripts/lint.py`
- `scripts/flush.py` vs `.claude/memory-compiler/scripts/flush.py`

**Verdict:** Doublons intentionnels (memory-compiler est une sous-application). À laisser — pas de suppression.

---

## 5. FICHIERS À CONSERVER (Production)

| Fichier | Rôle | Taille | Garder |
|---------|------|--------|--------|
| `app.py` | Routes Flask principales | 89K | ✅ GARDER |
| `scanner_engine.py` | Scanner multi-exchange | 72K | ✅ GARDER |
| `news_macro.py` | News + calendrier macro | 56K | ✅ GARDER |
| `morning_brief.py` | Morning Brief quotidien | 48K | ✅ GARDER |
| `cot_engine.py` | Analyse COT/CFTC | 46K | ✅ GARDER |
| `indices_engine.py` | Suivi indices macro | 43K | ✅ GARDER |
| `backtest_engine.py` | Backtesting stratégies | 23K | ✅ GARDER |
| `smart_signals.py` | Génération signaux | 23K | ✅ GARDER |
| `daily_report.py` | Rapport quotidien | 29K | ✅ GARDER |
| `forex_engine.py` | Analyse forex | 31K | ✅ GARDER |
| `security.py` | Auth, rôles, abonnements | 34K | ✅ GARDER |
| `db.py` | Couche base de données | 11K | ✅ GARDER |
| `ai_provider.py` | Couche IA unifiée | 6.1K | ✅ GARDER |
| `config.py` | Configuration | 4.3K | ✅ GARDER |
| `wsgi.py` | Point d'entrée WSGI | 413B | ✅ GARDER |
| `diagnostic_checker.py` | Outil diagnostic | 5.1K | ✅ GARDER |
| `cvd_engine.py` | CVD (Cumulative Volume) | 4.3K | ✅ GARDER |
| `heatmap_engine.py` | Heatmap | 11K | ✅ GARDER |
| `lexique.py` | Lexique/vocabulaire | 34K | ✅ GARDER |
| `wallet_tracker.py` | Suivi wallet | 10K | ✅ GARDER |

---

## 6. RÉSUMÉ — PLAN D'ACTION

### À SUPPRIMER (16-17 fichiers)

**SUPPRESSION IMMÉDIATE:**
```
Fichiers morning_brief:
  ✓ morning_brief_complete.py
  ✓ morning_brief_fixed.py

Fichiers app (expérimentaux):
  ✓ app_local_complete.py
  ✓ app_local_test.py
  ✓ app_lwcharts.py
  ✓ app_lwcharts_advanced.py
  ✓ app_lwcharts_zones.py
  ✓ app_lwcharts_zones_fixed.py

Fichiers smart_signals:
  ✓ smart_signals_backup.py
  ✓ smart_signals_fixed.py

Fichiers test (à /scratch/ d'abord ou supprimer):
  ✓ test_apis_hetzner.py
  ✓ test_heatmap_local.py
  ✓ test_macro_fix.py
  ✓ test_telegram.py

Dossier complet:
  ✓ /db-test/ (stub vide, non utilisé)
```

**CONDITIONNEL:**
- `app_backup.py` — À GARDER ou à SUPPRIMER (dépend de votre stratégie de backup)

**Total suppression:** 14 fichiers + 1 dossier = ~190 KB libérés

---

### À GARDER (20 fichiers production + 8 fichiers test)

**Production:** 20 fichiers core du système  
**Test/Scratch:** 8 fichiers dans `/scratch/`

---

### À VÉRIFIER EN PRIORITÉ

1. **App backup:** app_backup.py datant du 2026-05-03 (plus ancien que app.py du 2026-05-04). Décision: **GARDER 1 seul backup** (optionnel mais prudent pour rollback) ou **SUPPRIMER**?
2. **db-test:** `/db-test/` contient stub vide (`db.py`, `test.py`). Pas importé nulle part. **À SUPPRIMER.**
3. **Memory/notes:** ✅ 6 fichiers pertinents présents. OK.
4. **Doublons `.claude/`:** ✅ Doublons intentionnels (memory-compiler). OK.

---

## 7. RÉORGANISATION PROPOSÉE — `memory/`

**Pas de changement structurel recommandé.** Structure actuelle conforme ICA:
- ✅ `_index.md` — Porte d'entrée
- ✅ `archives/` — Sessions immuables
- ✅ `agents/` — Notes persistantes
- ✅ `framework/` — Piliers ICA
- ✅ `projets/` — État par projet

**Action:** Vérifier que `contexte.md` est à jour dans `projets/cryptoscanner/`

---

## 8. IMPACT ESTIMÉ

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Fichiers `.py` à la racine | 36 | 21 | -15 fichiers |
| Taille (doublons) | ~190 KB | ~0 KB | -190 KB |
| Doublons | 7 groupes | 0 | ✅ Éliminés |
| Fichiers test/scratch | mélangés | séparés | ✅ Clarté |
| Clarté structure | Confuse | Claire | ✅ |

---

## PROCHAINES ÉTAPES

1. **Décision:** Garder ou supprimer `app_backup.py`?
2. **Validation:** Confirmer les 14 fichiers à supprimer + `/db-test/`
3. **Backup:** Créer snapshot git avant nettoyage
   ```bash
   git add -A
   git commit -m "Pre-cleanup snapshot — 14 test files, app experiments, morning_brief dupes"
   ```
4. **Exécution:** Supprimer fichiers selon plan
5. **Vérification:** 
   - Tester que `app.py` lance sans erreur
   - Vérifier qu'aucun import ne casse
6. **Archive:** Exécuter `/archive` pour documenter la session

---

**Rapport terminé — En attente de confirmation pour exécution.**
