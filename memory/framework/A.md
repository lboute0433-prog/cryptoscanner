# A — Action
## Le troisième pilier du Framework [[ICA]]

---

## Définition

**L'Action c'est CE QUE l'agent fait concrètement dans le monde.**

```
L'Action répond à :
→ Quels outils peut-il utiliser ?
→ Qui peut-il appeler pour l'aider ?
→ Quelles séquences peut-il déclencher ?
→ Comment livre-t-il le résultat ?
```

---

## Dans CryptoScanner Pro — 3 composantes d'Action

### Composante A1 — Agents spécialisés

Fichiers `.md` dans `.claude/agents/` — sous-agents avec rôles définis.

```
.claude/agents/
├── dev/
│   ├── debugger.md      ← Diagnostique et corrige les bugs
│   └── feature.md       ← Implémente de nouvelles fonctionnalités
├── marche/
│   ├── scanner.md       ← Exécute et interprète le scanner marché
│   └── analyse.md       ← Analyse COT, ETF, macro, open interest
└── reporting/
    ├── morning-brief.md ← Génère le Morning Brief quotidien
    └── rapport.md       ← Envoie le rapport Telegram/email
```

### Composante A2 — Commands (raccourcis)

Fichiers `.md` dans `.claude/commands/` — slash commands.

```
/status          ← Vue d'ensemble du système
/recall          ← Recharger le contexte
/archive         ← Sauvegarder la session
/nouveau-agent   ← Créer un agent ICA
/nouveau-projet  ← Initialiser la mémoire d'un projet
/review          ← Auditer la conformité ICA
```

### Composante A3 — Scripts Python (execution déterministe)

Les scripts Python à la racine sont la couche Execution.

```
scanner_engine.py  ← Scanner multi-exchange
morning_brief.py   ← Morning Brief IA
daily_report.py    ← Rapport Telegram
cot_engine.py      ← Analyse COT
ai_provider.py     ← Couche IA unifiée
app.py             ← Application Flask
```

---

## La Différence Agents vs Scripts vs Commands

```
AGENTS              SCRIPTS             COMMANDS
────────            ──────────          ──────────
Un rôle précis      Déterministe        Un raccourci
Décision + action   Execution pure      Séquence déclenchée
Appel à la demande  Toujours pareil     Déclenché par /
"L'agent Scanner"   "scanner_engine.py" "/status"
```

**Métaphore :**
```
Agent   = un employé qui réfléchit et agit
Script  = une machine qui exécute toujours la même chose
Command = un bouton qui déclenche une séquence
```

---

## Format de Livraison Standard

Chaque agent doit livrer dans ce format (voir `.claude/rules/livraison.md`) :

```markdown
✅ [{livrable}] terminé

→ Ce qui a été fait :
  - {action 1}

→ Fichiers modifiés :
  - `{chemin}` — {créé|modifié|supprimé}

→ Prochaine étape suggérée :
  {action suivante}
```

---

## Navigation

← [[ICA]] — Framework complet
← [[I]] — Pilier Instruction
← [[C]] — Pilier Connaissance
