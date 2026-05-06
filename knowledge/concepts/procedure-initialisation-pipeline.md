---
title: "Procédure d'Initialisation du Pipeline"
aliases: [setup-pipeline, initialisation-memory-compiler, validation-end-to-end]
tags: [setup, validation, procédure, pipeline]
sources:
  - "daily/test-setup.md"
created: 2026-04-24
updated: 2026-04-24
---

# Procédure d'Initialisation du Pipeline

La séquence complète pour initialiser et valider le memory compiler dans un nouveau projet. Quatre étapes ordonnées permettent de passer d'un dépôt vide à un pipeline opérationnel capable de générer automatiquement des articles de knowledge base à partir de logs de conversation.

## Key Points

- **Étape 1 — Configuration** : créer `.claude/settings.json` avec les trois hooks (SessionStart, SessionEnd, PreCompact)
- **Étape 2 — Dépendances** : exécuter `uv sync` pour installer l'environnement virtuel depuis `pyproject.toml`
- **Étape 3 — Premier test** : lancer `uv run python scripts/compile.py --file daily/<premier-log>.md` sur un log existant
- **Étape 4 — Validation** : vérifier que `knowledge/concepts/` contient les articles générés et que `knowledge/index.md` est à jour
- Un premier log de test peut générer 5 articles ou plus dès le premier lancement, confirmant que le pipeline est fonctionnel

## Details

L'initialisation suit un ordre strict car chaque étape dépend de la précédente. Sans `.claude/settings.json`, les hooks ne se déclenchent pas et aucune capture automatique n'est possible. Sans `uv sync`, les scripts échouent avec une erreur d'importation (`ModuleNotFoundError`). Le test de compilation sur un fichier spécifique (`--file`) est préféré à une compilation globale pour valider le pipeline sans risque d'effets de bord.

La validation finale repose sur deux vérifications concrètes : (1) la présence de fichiers `.md` dans `knowledge/concepts/` avec un frontmatter YAML valide, et (2) une entrée dans `knowledge/index.md` pour chaque article créé. Si ces deux conditions sont remplies, le pipeline est opérationnel de bout en bout. Une entrée correspondante dans `knowledge/log.md` confirme également que la compilation a été tracée correctement.

La génération de 5 articles distincts lors du test initial (lors de la session du 2026-04-23) valide non seulement le script `compile.py`, mais aussi la qualité du premier log quotidien utilisé comme source — un log trop pauvre en contenu produit peu ou pas d'articles.

## Related Concepts

- [[concepts/hook-system]] — Les hooks configurés à l'étape 1 sont le mécanisme de capture automatique
- [[concepts/uv-dependency-management]] — `uv sync` à l'étape 2 installe les dépendances requises
- [[concepts/memory-compiler-architecture]] — Le pipeline validé par cette procédure
- [[concepts/knowledge-base-structure]] — La structure vérifiée à l'étape 4

## Sources

- [[daily/test-setup.md]] — Procédure exécutée lors de la session de test initiale ; génération confirmée de 5 articles au premier lancement de compile.py
