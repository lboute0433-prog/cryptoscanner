Retrouver le contexte depuis memory/ après un /clear ou en début de session.

Argument optionnel : nom du projet (ex: `/recall cryptoscanner`). Variable : $ARGUMENTS

## Processus

### 1. Identifier le projet

- Si $ARGUMENTS fourni : utiliser directement comme nom de projet.
- Sinon : lire `memory/_index.md`, afficher les projets disponibles.
- Si memory/_index.md vide ou absent : répondre "Aucune session trouvée. Mémoire initialisée — décris ce sur quoi tu travailles et on commence."

### 2. Charger l'historique

Lire `memory/projets/{nom}/historique.md`.

### 3. Charger le contexte

Priorité 1 — si `memory/projets/{nom}/contexte.md` existe : le lire (voie rapide, ~25 lignes).
Priorité 2 — sinon : lire la dernière archive depuis historique.md.

### 4. Présenter le briefing

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
