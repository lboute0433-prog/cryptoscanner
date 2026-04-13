# C — Connaissance
## Le deuxième pilier du Framework [[ICA]]

---

## Définition

**La Connaissance c'est CE QUE l'agent sait pour bien agir.**

C'est la mémoire du système.
Ce qui permet d'agir intelligemment plutôt que génériquement.

```
La Connaissance répond à :
→ Quel est le contexte ?
→ Qu'est-ce qu'on a déjà fait ?
→ Quelles sont les références et préférences ?
→ Quelles procédures suivre pour cette tâche ?
```

---

## Dans CryptoScanner Pro — 3 niveaux de Connaissance

### Niveau C1 — Skills (connaissance opérationnelle permanente)

Fichiers `.md` dans `.claude/skills/` — procédures techniques toujours pertinentes.

```
.claude/skills/
├── ica-creation.md    ← Comment créer une entité ICA conforme
├── archive.md         ← Procédure d'archivage de session
└── recall.md          ← Procédure de récupération de contexte
```

### Niveau C2 — Directives (procédures opérationnelles du projet)

Fichiers `.md` dans `directives/` — SOPs spécifiques à CryptoScanner.

```
directives/
├── scanner.md         ← Comment exécuter le scanner marché
├── morning-brief.md   ← Comment générer le morning brief
├── daily-report.md    ← Comment envoyer le rapport Telegram
├── deploy.md          ← Comment déployer sur Railway
├── debug.md           ← Comment diagnostiquer un bug
└── new-feature.md     ← Comment implémenter une feature
```

### Niveau C3 — Mémoire (contexte mémoriel et historique)

Vault Obsidian dans `memory/` — décisions, archives, état courant.

```
memory/
├── projets/cryptoscanner/contexte.md    ← État courant (~25 lignes)
├── projets/cryptoscanner/data/          ← Données du projet
├── agents/{nom}/notes.md               ← Notes par agent
└── archives/                           ← Sessions immuables
```

---

## La Différence Connaissance vs Instruction

```
INSTRUCTION                    CONNAISSANCE
───────────────                ─────────────────
Permanent                      Variable selon le projet
Ne change pas                  S'enrichit avec le temps
Qui tu es                      Ce que tu sais
Règles de comportement         Données et références
"Tu es un dev Flask senior"    "Notre stack : Flask 3.11, SQLite..."
```

---

## Hiérarchie de la Connaissance

```
Critique   — dans CLAUDE.md directement
             Contexte sans lequel l'agent ne peut pas fonctionner

Important  — dans .claude/skills/ ou directives/
             Procédures techniques récurrentes

Contextuel — dans memory/projets/
             Historiques, décisions, état courant

Archivé    — dans memory/archives/
             Sessions passées immuables
```

---

## Navigation

← [[ICA]] — Framework complet
← [[I]] — Pilier précédent : Instruction
→ [[A]] — Pilier suivant : Action
