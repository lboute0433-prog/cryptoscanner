# Agents — Guide de Création

## Créer un agent

**Option 1 — Commande** (recommandé) :
```
/nouveau-agent
```
La commande guide la création pas à pas en suivant le Framework ICA.

**Option 2 — Manuel** :
1. Copier `_template.md`
2. Remplir les sections I, C, A
3. Placer dans `.claude/agents/{département}/{nom}.md`
4. Créer `memory/agents/{nom}/notes.md`

## Organisation

Les agents sont organisés par département :
```
.claude/agents/
├── _template.md           ← Cellule souche ICA (ne pas modifier)
├── README.md              ← Ce fichier
├── dev/                   ← Développement logiciel
│   ├── debugger.md
│   └── feature.md
├── marche/                ← Analyse de marché
│   ├── scanner.md
│   └── analyse.md
└── reporting/             ← Rapports et briefings
    ├── morning-brief.md
    └── rapport.md
```

## Framework ICA

Chaque agent suit le pattern ICA :
- **I (Instruction)** : Qui il est, ses limites
- **C (Connaissance)** : Ce qu'il sait, ses références, les scripts Python qu'il utilise
- **A (Action)** : Ce qu'il fait, son format de livraison

Voir `memory/framework/ICA.md` pour le framework complet.

## Mémoire

Chaque agent a sa zone mémoire dans `memory/agents/{nom}/notes.md`.
Il peut aussi lire la mémoire partagée dans `memory/projets/cryptoscanner/`.
