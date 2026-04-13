Auditer un livrable ou un agent pour conformité ICA et qualité.

Arguments : $ARGUMENTS (chemin du fichier à auditer, ou "dernier" pour le dernier livrable).
Si vide : auditer le dernier fichier créé ou modifié dans la session.

## Processus

### 1. Identifier la cible

- Si $ARGUMENTS est un chemin : auditer ce fichier.
- Si $ARGUMENTS est un nom d'agent : chercher dans `.claude/agents/`.
- Sinon : identifier le dernier livrable de la session en cours.

### 2. Audit ICA (si c'est un agent ou fichier structurel)

Vérifier la structure ICA :
- [ ] **I (Instruction)** : Le rôle est-il défini ? Les limites sont-elles claires ?
- [ ] **C (Connaissance)** : Le contexte est-il suffisant ? Les références sont-elles présentes ?
- [ ] **A (Action)** : Les actions sont-elles concrètes ? Le format de livraison est-il défini ?
- [ ] **Règle d'Or** : I + C + A = agent autonome ? Aucun pilier manquant ?

Référence : `memory/framework/ICA.md`, `memory/framework/I.md`, `memory/framework/C.md`, `memory/framework/A.md`

### 3. Audit qualité (si c'est un livrable)

Vérifier contre `.claude/rules/qualite.md` :
- [ ] Le résultat correspond à la demande initiale
- [ ] Le format de livraison est respecté (`.claude/rules/livraison.md`)
- [ ] Les fichiers sont aux bons emplacements
- [ ] Pas de régression sur l'existant

### 4. Rapport

```
## Review — {nom du fichier}

### Conformité ICA
{PASS ou FAIL avec détails}

### Qualité
{PASS ou FAIL avec détails}

### Suggestions
- {suggestion 1}
- {suggestion 2}

### Verdict
{✅ Conforme | ⚠️ À améliorer | ❌ Non conforme}
```
