# Règle — Mémoire Partagée

## Protocole de session

- **Début de session** : exécuter `/recall cryptoscanner` pour charger le contexte.
- **Fin de session** : exécuter `/archive` avant tout `/clear`.
- Sans archive, le contexte est perdu définitivement.

## Où vit la mémoire

Tout le système de mémoire est dans `memory/` à la racine du projet.

```
memory/
├── _index.md              # Index de tous les projets et archives
├── archives/              # Sessions immuables (ne jamais modifier)
├── projets/               # État courant par projet (mutable)
│   └── cryptoscanner/
│       ├── contexte.md    # Snapshot courant (~25 lignes)
│       ├── historique.md  # Fil chronologique
│       └── data/          # Données du projet
└── agents/                # Notes persistantes par agent
    └── {nom}/
        └── notes.md
```

## Règles d'accès

- Les **archives** sont immuables — ne jamais les modifier après création.
- Le **contexte.md** est écrasé à chaque `/archive` — c'est l'état courant, pas un historique.
- Chaque agent peut lire toute la mémoire partagée.
- Chaque agent écrit ses notes dans `memory/agents/{son-nom}/notes.md`.
- L'index `_index.md` est la porte d'entrée — toujours à jour.

## Hiérarchie

```
Tier 1 — Agent     : memory/agents/{nom}/notes.md (notes locales)
Tier 2 — Projet    : memory/projets/cryptoscanner/contexte.md (état courant)
Tier 3 — Système   : memory/archives/*.md (historique complet)
```
