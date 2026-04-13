---
name: archive
description: Archiver la session de travail en cours avant un /clear. Résume le contexte, les décisions, l'état du projet et les URLs d'assets pour pouvoir reprendre plus tard via /recall.
---

# Archive — Sauvegarder la session

## INSTRUCTION

Tu archives la session en cours dans le dossier `memory/` du projet.
L'objectif : permettre à l'utilisateur de faire `/clear` sans perdre le contexte.
L'archive doit contenir tout ce qu'il faut pour reprendre dans une session future.

## ACTION

### 1. Collecter le contexte de la session

Synthétiser depuis la conversation en cours :
- **Projet** concerné
- **Travail effectué** : livrables produits, fichiers créés/modifiés
- **Décisions** prises et pourquoi
- **État du projet** : phase actuelle, ce qui est validé, ce qui est en cours
- **Prochaines étapes** prévues
- **Fichiers modifiés** avec chemins complets
- **Assets générés** : URLs (noter "Aucun." si session purement logique)

### 2. Générer le fichier archive

Écrire dans `memory/archives/` avec le nommage :
`YYYY-MM-DD-HHhMM-{projet}-{resume-court}.md`

Format :

```markdown
---
date: YYYY-MM-DD
heure: "HH:MM"
projet: {nom}
phase: {phase actuelle}
tags: [projet/{nom}, type/archive]
---

# Session YYYY-MM-DD HHhMM — {Projet} {Résumé}

## Résumé
[2-3 phrases : objectif de la session + résultat livré]

## Travail effectué
- {action 1}

## Décisions
- **{Décision}** : {raison}

## État du projet
- Phase actuelle : {phase}
- Validé : {éléments terminés}
- En cours : {éléments en cours}

## Prochaines étapes
1. {étape 1}

## Fichiers modifiés
- `{chemin}` — {créé|modifié|supprimé}

## Assets (URLs)
{URLs ou "Aucun."}
```

### 3. Créer ou écraser le contexte projet

Écrire `memory/projets/{nom}/contexte.md`.
Ce fichier est la vue courante du projet — mutable, écrasé à chaque archivage.

### 4. Mettre à jour l'historique projet

Ajouter dans `memory/projets/{nom}/historique.md` :
```
- [YYYY-MM-DD HHhMM — {résumé}](../../archives/YYYY-MM-DD-HHhMM-{projet}-{resume}.md)
```

### 5. Mettre à jour l'index

Dans `memory/_index.md`, ajouter le lien dans la section "Archives".

### 6. Confirmer

```
Archive créée : memory/archives/YYYY-MM-DD-HHhMM-{projet}-{resume}.md
Contexte mis à jour : memory/projets/{nom}/contexte.md

Le /clear est safe — utiliser /recall {projet} pour reprendre.
```
