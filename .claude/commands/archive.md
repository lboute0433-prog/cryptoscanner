Archiver la session de travail en cours avant un /clear.

## Processus

### 1. Collecter le contexte

Synthétiser depuis la conversation :
- Projet concerné
- Travail effectué : livrables, fichiers créés/modifiés
- Décisions prises et pourquoi
- État du projet : phase, validé, en cours
- Prochaines étapes
- Fichiers modifiés avec chemins complets
- Assets générés (URLs) — noter "Aucun." si session logique

### 2. Écrire le fichier archive

Chemin : `memory/archives/YYYY-MM-DD-HHhMM-{projet}-{resume}.md`

Format :
```
---
date: YYYY-MM-DD
heure: "HH:MM"
projet: {nom}
phase: {phase actuelle}
tags: [projet/{nom}, type/archive]
---

# Session YYYY-MM-DD HHhMM — {Projet} {Résumé}

## Résumé
[2-3 phrases]

## Travail effectué
- {action}

## Décisions
- **{Décision}** : {raison}

## État du projet
- Phase actuelle : ...
- Validé : ...
- En cours : ...

## Prochaines étapes
1. ...

## Fichiers modifiés
- `{chemin}` — {action}

## Assets (URLs)
{URLs ou "Aucun."}
```

### 3. Écraser contexte.md

Écrire `memory/projets/{nom}/contexte.md` avec l'état courant synthétisé (~25 lignes).
Remplacer entièrement si existant.

### 4. Mettre à jour l'historique

Ajouter dans `memory/projets/{nom}/historique.md` :
`- [YYYY-MM-DD HHhMM — {résumé}](../../archives/YYYY-MM-DD-HHhMM-{projet}-{resume}.md)`

### 5. Mettre à jour l'index

Dans `memory/_index.md`, ajouter dans la section "Archives".

`- [YYYY-MM-DD HHhMM — {Projet} {résumé}](archives/YYYY-MM-DD-HHhMM-{projet}-{resume}.md)`

S'assurer que le projet figure dans la section "Projets".

### 6. Confirmer

```
Archive créée : memory/archives/{fichier}.md
Contexte mis à jour : memory/projets/{nom}/contexte.md
Le /clear est safe — utiliser /recall {projet} pour reprendre.
```
