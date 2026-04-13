Initialiser la mémoire pour un nouveau projet.

Arguments : $ARGUMENTS = nom du projet (ex: `/nouveau-projet mon-app`).
Si vide : demander le nom du projet.

## Processus

### 1. Identifier le nom

- Si $ARGUMENTS fourni : utiliser comme nom (en kebab-case).
- Sinon : demander à l'utilisateur.

### 2. Créer la structure mémoire

Créer `memory/projets/{nom}/contexte.md` :
```markdown
---
projet: {nom}
phase: initialisation
derniere-session: {date du jour}
tags: [projet/{nom}]
---

# {Nom} — Contexte actif

## État courant
- Phase : Initialisation
- Validé : Structure mémoire créée
- En cours : Définition du projet

## Décisions cumulées
- Aucune pour le moment

## Prochaines étapes
1. Définir les objectifs du projet
2. Identifier les agents nécessaires

## Assets actifs (URLs)
Aucun.
```

Créer `memory/projets/{nom}/historique.md` :
```markdown
---
projet: {nom}
tags: [projet/{nom}]
---

# {Nom} — Historique des sessions

<!-- Les sessions apparaîtront ici après /archive -->
```

### 3. Mettre à jour l'index

Ajouter dans `memory/_index.md` section "Projets" :
`- [{Nom}](projets/{nom}/historique.md)`

### 4. Confirmer

```
✅ Projet {nom} initialisé

→ Contexte : memory/projets/{nom}/contexte.md
→ Historique : memory/projets/{nom}/historique.md
→ Index mis à jour : memory/_index.md

Mémoire prête. Décris les objectifs du projet pour commencer.
```
