---
name: recall
description: Retrouver le contexte depuis le dossier memory/ après un /clear ou en début de session. Charge le contexte projet et les décisions cumulées pour reprendre le travail sans re-briefing.
---

# Recall — Reprendre le contexte

## INSTRUCTION

Tu retrouves le contexte de travail depuis le dossier `memory/` du projet.
L'objectif : reprendre en 30 secondes après un `/clear` ou au début d'une nouvelle session.
Charge uniquement ce qui est nécessaire — pas tout le dossier.

Argument optionnel : nom du projet (ex: `/recall cryptoscanner`). Variable : `$ARGUMENTS`

## ACTION

### 1. Identifier le projet

- Si `$ARGUMENTS` est fourni, l'utiliser comme nom de projet directement.
- Sinon, lire `memory/_index.md` et afficher les projets disponibles.
- Si `memory/_index.md` n'existe pas : répondre "Aucune session trouvée. Décris ce sur quoi tu travailles et on commence."

### 2. Charger l'historique

Lire `memory/projets/{nom}/historique.md` pour voir le fil chronologique des sessions.

### 3. Charger le contexte (voie rapide)

**Si `memory/projets/{nom}/contexte.md` existe** : le lire en priorité.
C'est l'état courant synthétisé (~25 lignes). Voie rapide, 2x moins de tokens.

**Si `contexte.md` n'existe pas** : lire la dernière archive listée dans `historique.md`.

### 4. Présenter le briefing

Format de réponse :

```
## Reprise — {Projet}

**Dernière session** : {date} — {résumé}
**Phase actuelle** : {phase}

### État
- Validé : ...
- En cours : ...

### Décisions clés
- ...

### Prochaines étapes
1. ...

### Assets disponibles
- {URLs ou "Aucun"}
```

### 5. Proposer la suite

Demander : "On reprend à l'étape {X} ?"
