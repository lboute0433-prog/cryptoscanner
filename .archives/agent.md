# Instructions Pour l'Agent — CryptoScanner Pro

Ce fichier définit l'architecture de travail du projet et la manière dont un agent IA doit opérer dans ce dépôt.

## Architecture du Dépôt

Le projet suit une architecture à 3 couches à responsabilités séparées :

1. `CLAUDE.md` + `agent.md`
   Le point d'entrée de l'agent. Définit l'orchestrateur ICA, le routing vers les agents spécialisés, et les règles de fonctionnement.

2. `directives/`
   La couche "Quoi faire".
   Contient des procédures opérationnelles standard (SOP) en Markdown. Chaque directive décrit un objectif, les entrées attendues, les scripts à utiliser, les sorties attendues et les cas limites.

3. Scripts Python à la racine (couche Execution)
   La couche "Faire le travail".
   Scripts déterministes qui exécutent les tâches réelles : appels API, transformations, base de données, intégrations externes.

   | Script | Rôle |
   |--------|------|
   | `scanner_engine.py` | Scanner crypto multi-exchange |
   | `morning_brief.py` | Morning Brief IA quotidien |
   | `daily_report.py` | Rapport Telegram |
   | `cot_engine.py` | Analyse COT/CFTC |
   | `indices_engine.py` | Indices macro |
   | `forex_engine.py` | Forex |
   | `smart_signals.py` | Signaux de trading |
   | `news_macro.py` | News + calendrier macro |
   | `backtest_engine.py` | Backtesting |
   | `ai_provider.py` | Couche IA unifiée (Groq + Anthropic) |
   | `app.py` | Application Flask principale |

4. `.claude/`
   Configuration de l'agent Claude Code.
   Contient les règles, agents spécialisés, skills partagés et slash commands.

5. `memory/`
   Mémoire persistante du projet.
   Vault Obsidian avec l'état courant, les archives de sessions et les notes des agents.

6. `ai/`
   Compatibilité multi-agents.
   Variantes des instructions pour d'autres environnements IA (AGENTS.md, GEMINI.md).

## Mode de Fonctionnement

L'agent opère dans une architecture à 3 couches :

### 1. Directives

Les fichiers de `directives/` définissent quoi faire.
Ce sont des SOP en langage naturel, rédigées pour décrire la marche à suivre de façon précise mais lisible.

Directives disponibles :
- `directives/scanner.md` — Exécuter et interpréter le scanner marché
- `directives/morning-brief.md` — Générer le morning brief quotidien
- `directives/daily-report.md` — Générer et envoyer le rapport Telegram
- `directives/deploy.md` — Déployer sur Railway
- `directives/debug.md` — Diagnostiquer et corriger un bug
- `directives/new-feature.md` — Implémenter une nouvelle fonctionnalité

### 2. Orchestration

L'agent assure la prise de décision.
Son rôle est de :
- lire les fichiers pertinents ;
- identifier la bonne directive et/ou le bon agent spécialisé ;
- vérifier s'il existe déjà un script adapté ;
- exécuter les étapes dans le bon ordre ;
- gérer les erreurs et les cas limites ;
- demander une clarification uniquement quand c'est nécessaire ;
- produire un compte-rendu clair au format standard.

L'agent ne doit pas faire manuellement ce qui existe déjà sous forme de script fiable.

### 3. Execution

Les scripts Python à la racine font le travail déterministe.
Ils doivent être privilégiés dès qu'une tâche répétitive, sensible ou vérifiable peut être automatisée.

## Règles de Décision

### 1. Vérifier d'abord l'existant

Avant d'écrire un nouveau script :
- lire `CLAUDE.md` et `agent.md` ;
- consulter `directives/` ;
- vérifier si un script Python existant couvre déjà le besoin ;
- réutiliser l'existant autant que possible.

Ne créer un nouveau script que si aucun composant existant ne couvre correctement le besoin.

### 2. Privilégier le déterministe

Si une tâche peut être confiée à un script, elle doit l'être.
L'agent sert à raisonner, coordonner et valider, pas à remplacer une logique outillée par de l'improvisation.

### 3. Auto-correction

Quand une exécution échoue :
- lire le message d'erreur ;
- identifier la cause probable ;
- corriger le script ou l'appel ;
- relancer un test minimal de validation ;
- documenter l'apprentissage dans la directive concernée si pertinent.

Si l'exécution consomme des ressources payantes (API Groq, Anthropic, exchanges), vérifier avec l'utilisateur avant de relancer.

### 4. Modifications de directives

Les directives sont des documents vivants, mais elles ne doivent pas être modifiées à la légère.
Par défaut :
- ne pas créer de nouvelle directive sans demande explicite ;
- ne pas écraser une directive existante sans validation ;
- proposer les améliorations avant de les appliquer.

### 5. Validation obligatoire

Après toute modification d'un script ou d'un flux :
- exécuter la vérification la plus petite et la plus sûre possible ;
- confirmer ce qui a été testé ;
- signaler clairement ce qui n'a pas pu être validé.

## Ordre de Lecture Recommandé

Quand l'agent entre dans le projet, il doit lire dans cet ordre :

1. `CLAUDE.md` (orchestrateur + routing)
2. `agent.md` (ce fichier — architecture 3 couches)
3. `directives/` pertinentes selon la tâche
4. Scripts Python concernés
5. `memory/projets/cryptoscanner/contexte.md` (état courant)
6. `.claude/agents/` si délégation à un agent spécialisé

## Résultat Attendu d'une Intervention

À la fin d'une tâche, l'agent fournit un retour au format standard (voir `.claude/rules/livraison.md`) :

```
✅ [{livrable}] terminé

→ Ce qui a été fait :
  - {action 1}
  - {action 2}

→ Fichiers modifiés :
  - `{chemin}` — {créé|modifié|supprimé}

→ Prochaine étape suggérée :
  {description de l'étape suivante logique}
```
