# Framework ICA — Instruction · Connaissance · Action
## Fractality Studio — Documentation Complète

---

## Qu'est-ce que ICA ?

ICA est un framework fractal pour organiser tout système d'intelligence artificielle.
Il repose sur une observation simple : **tout système intelligent — humain ou IA —
fonctionne selon trois piliers fondamentaux.**

```
I — Instruction    Qui tu es. Comment tu te comportes.
C — Connaissance   Ce que tu sais. Ce dont tu as besoin pour agir.
A — Action         Ce que tu fais. Comment tu agis dans le monde.
```

Ce qui rend ICA puissant : **le même pattern se répète à chaque niveau de zoom.**
C'est ça la fractalité.

---

## La Fractalité ICA — 3 niveaux

### Niveau 1 — Le Prompt

Le niveau le plus simple. Une seule interaction avec Claude.

```
## INSTRUCTION
Tu es un expert en [domaine].
Tu réponds toujours en français.
Tu es direct et concret.

## CONNAISSANCE
Contexte : [qui je suis, mon projet, mes contraintes]
Données : [informations pertinentes pour cette tâche]

## ACTION
Tâche : [ce que je te demande de faire]
Format : [comment je veux le résultat]
```

**Correspondance avec Anthropic :**
```
Instructions  →  I — qui est l'agent, ses règles
Context       →  C — ce qu'il sait
Task          →  A — ce qu'il fait
```

---

### Niveau 2 — L'Agent Augmenté

Un fichier CLAUDE.md + une structure de fichiers.
Claude Code devient un agent avec une identité, une mémoire, des outils.

```
I = CLAUDE.md + .claude/rules/
    Qui est l'agent, ses règles permanentes,
    son rôle, ses limites, son ton.
    Ne change pas entre les sessions.

C = .claude/skills/ + directives/ + memory/
    Ce que l'agent sait faire.
    Les procédures, les références, les données.
    S'enrichit au fil du temps.

A = .claude/agents/ + .claude/commands/ + scripts Python
    Ce que l'agent peut faire dans le monde réel.
    Les spécialistes qu'il peut appeler.
    Les scripts déterministes qui exécutent le travail.
```

---

### Niveau 3 — Le Système Agentique

Plusieurs agents, plusieurs départements, un pipeline autonome.

```
I = rules/ globales + CLAUDE.md racine
    Les règles de toute l'organisation.
    Qui fait quoi, comment on travaille ensemble.

C = skills/ partagés + directives/ + memory/
    La mémoire collective du projet.
    Les savoir-faire, les historiques, les décisions.

A = Départements + agents spécialisés + scripts Python
    Les équipes qui exécutent.
    Les scripts déterministes qui font le vrai travail.
```

---

## La Règle d'Or

```
I sans C  =  Agent aveugle
             Il sait qui il est mais manque de contexte

C sans I  =  Agent perdu
             Il a les infos mais ne sait pas comment les filtrer

I+C sans A  =  Agent paralysé
               Il comprend mais ne peut pas agir

I + C + A  =  Agent autonome
               Il sait qui il est, ce qu'il sait, et comment agir
```

---

## ICA et le Prompting Anthropic

```
Anthropic     →    ICA
──────────         ───────────────────────────────
Instructions  →    I  Qui tu es, comment tu te comportes
Context       →    C  Ce que tu sais, le background
Task          →    A  Ce que tu fais, la tâche précise
```

**L'ordre recommandé : I → C → A**

Toujours dans cet ordre. Pourquoi ?
- I d'abord → Claude sait QUI il est avant de recevoir les informations
- C ensuite → Claude a le contexte AVANT de recevoir la tâche
- A enfin   → Claude agit avec TOUT le contexte nécessaire

---

## Liens entre piliers

- [[I]] — L'Instruction en détail (rôle, limites, ton)
- [[C]] — La Connaissance en détail (skills, mémoire, directives)
- [[A]] — L'Action en détail (agents, commands, scripts)

---

*Framework ICA — Fractality Studio — @fractality.studio*
