---
name: ica-creation
description: Guide procédural pour créer toute entité conforme au Framework ICA — agents, commands, skills, prompts ou systèmes entiers.
---

# Création ICA — Guide Procédural

## INSTRUCTION

Ce skill guide la création de toute entité conforme au Framework ICA.
Il s'applique à : agents, commands, skills, prompts, et systèmes entiers.
Le même pattern se répète à chaque échelle — c'est la fractalité.

## CONNAISSANCE

### Sources de référence

- `memory/framework/ICA.md` — Framework complet, Règle d'Or, niveaux de zoom
- `memory/framework/I.md` — Pilier Instruction en détail (rôle, limites, ton, format)
- `memory/framework/C.md` — Pilier Connaissance en détail (contexte, skills, mémoire, RAG)
- `memory/framework/A.md` — Pilier Action en détail (agents, commands, MCP, livraison)

### Règle d'Or (memory/framework/ICA.md)

```
I sans C  = Agent aveugle
C sans I  = Agent perdu
I+C sans A = Agent paralysé
I + C + A = Agent autonome
```

### Anti-patterns courants (memory/framework/I.md)

- I trop long : noie l'identité dans le détail
- Mélanger I et C : confondre qui l'agent EST avec ce qu'il SAIT
- Oublier les limites : l'agent déborde de son périmètre
- I sans format de sortie : l'agent livre n'importe comment

## ACTION

### Étape 1 — Définir I (Instruction)

Déterminer :
- **Rôle** : Qui est cette entité ? (1 phrase)
- **Responsabilités** : Que fait-elle ? (3 max)
- **Limites** : Que ne fait-elle JAMAIS ? (2-3)
- **Ton** : Comment communique-t-elle ?
- **Références système** : quelles rules s'appliquent ?

### Étape 2 — Définir C (Connaissance)

Déterminer :
- **Contexte spécifique** : Quelles connaissances sont nécessaires pour ce rôle ?
- **Scripts** : Quels fichiers Python dans le projet sont pertinents ?
- **Directive** : Quelle SOP dans `directives/` s'applique ?
- **Mémoire** : Où dans `memory/` cette entité lit/écrit ?

### Étape 3 — Définir A (Action)

Déterminer :
- **Actions concrètes** : Que produit cette entité ? (livrables)
- **Format de livraison** : Comment le résultat est présenté ?
- **Outils** : Quels MCP ou commands sont utilisés ?
- **Zone mémoire** : Où sont stockées les notes persistantes ?

### Étape 4 — Valider

Checklist de conformité :
- [ ] I est défini et distinct de C
- [ ] C fournit le contexte suffisant pour que I fonctionne
- [ ] A est concret et actionnable
- [ ] I + C + A = entité autonome (Règle d'Or)

### Format de sortie

```markdown
# {Nom} — {Contexte}
## Système ICA · Instruction · Connaissance · Action

---

## INSTRUCTION (I)
{contenu I}

---

## CONNAISSANCE (C)
{contenu C}

---

## ACTION (A)
{contenu A}
```
