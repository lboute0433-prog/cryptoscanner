Afficher l'état complet du système agentique.

## Processus

### 1. Scanner les agents

Lister tous les fichiers dans `.claude/agents/` (hors `_template.md` et `README.md`).
Grouper par département (sous-dossiers).

### 2. Scanner les projets

Lire `memory/_index.md` pour lister les projets actifs.
Pour chaque projet, lire `memory/projets/{nom}/contexte.md` pour la phase actuelle.

### 3. Scanner les connexions

Lire `.mcp.json` pour lister les MCP connectés.

### 4. Scanner les règles et commands

Lister les fichiers dans `.claude/rules/` et `.claude/commands/`.

### 5. Afficher

```
## Status — CryptoScanner Pro

### Agents ({N} total)
{Par département :}
- {dept}/ : {agent1}, {agent2}

### Projets ({N} actifs)
- {projet} — Phase : {phase}

### Directives ({N} disponibles)
- {directive1}, {directive2}, ...

### Rules ({N} chargées)
- {rule1}, {rule2}, ...

### Commands ({N} disponibles)
- /{command1}, /{command2}, ...

### MCP ({N} connectés)
- {mcp1}, {mcp2}, ...
{Ou "Aucun MCP connecté. Configurer .mcp.json pour ajouter des outils."}

### Framework
ICA.md ✅ | I.md ✅ | C.md ✅ | A.md ✅ (dans memory/framework/)
```
