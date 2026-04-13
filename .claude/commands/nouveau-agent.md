Créer un nouvel agent conforme au Framework ICA.

Arguments : $ARGUMENTS (format libre — nom, rôle, département, ou description en langage naturel).
Si vide : demander interactivement quel agent créer.

## Processus

### 1. Comprendre le besoin

Si $ARGUMENTS fourni : extraire le nom, le rôle et le département.
Sinon : demander à l'utilisateur :
- Quel rôle pour cet agent ? (ex: "analyste on-chain", "optimiseur de performance")
- Dans quel département ? (ex: "marche", "dev", "reporting") — créer le département si nouveau.

### 2. Consulter le Framework ICA

Lire les références :
- `.claude/agents/_template.md` pour la structure
- `memory/framework/ICA.md` pour la conformité globale
- `memory/framework/I.md` pour définir l'Instruction correctement
- `memory/framework/C.md` pour définir la Connaissance correctement
- `memory/framework/A.md` pour définir l'Action correctement

### 3. Définir l'agent avec l'utilisateur

Dialoguer pour préciser :
- **I (Instruction)** : Rôle précis, responsabilités (3 max), limites claires, ton
- **C (Connaissance)** : Scripts Python concernés, directive associée, contexte métier
- **A (Action)** : Actions concrètes, format de livraison, outils

### 4. Générer le fichier agent

Créer `.claude/agents/{département}/{nom}.md` en suivant la structure de `_template.md`.
Si le dossier département n'existe pas, le créer.

### 5. Créer la zone mémoire

Créer `memory/agents/{nom}/notes.md` avec le contenu initial :
```
# Notes — {Nom}

Zone de notes persistantes pour l'agent {nom}.
```

### 6. Confirmer

```
✅ Agent {nom} créé

→ Fichier : .claude/agents/{dept}/{nom}.md
→ Mémoire : memory/agents/{nom}/notes.md
→ Département : {dept}

Checklist ICA :
✅ I défini (rôle + limites)
✅ C défini (connaissances + références)
✅ A défini (actions + format)
✅ Zone mémoire créée

L'orchestrateur peut maintenant router des demandes vers cet agent.
```
