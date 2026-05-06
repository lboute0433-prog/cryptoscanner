# Sources & Références

## Comment ça marche

Tu ajoutes tes sources ici → Le compilateur les scanne → Elles sont intégrées à la knowledge base.

## Structure

### `articles/`
Articles, documentations, blog posts que tu veux mémoriser.

**Format :** Crée des fichiers `.md` avec le titre et contenu.

### `donnees/`
Données brutes, stats, liens APIs, métadonnées importantes.

**Format :** JSON, CSV, ou markdown avec structure claire.

### `idees/`
Brainstorm, concepts, améliorations, features ideas.

**Format :** Markdown libre, une idée par fichier.

---

## Exemples

### Article
Fichier: `articles/strategie-trading.md`
```markdown
# Stratégie Trading RSI

Source: https://...
Date: 2026-04-24

Contenu...
```

### Donnée
Fichier: `donnees/exchanges-api.json`
```json
{
  "binance": {"rate_limit": 1200, "free": true},
  "kraken": {"rate_limit": 600, "free": true}
}
```

### Idée
Fichier: `idees/dashboard-heatmap.md`
```markdown
# Heatmap crypto réallocation mensuelle

Concept: afficher les coins qui ont bougé le plus en 30 jours...
```

---

## Compilation

Le compilateur scanne `references/` à chaque exécution :

```powershell
python scripts/compile.py --all
```

Articles, données, idées sont convertis en concepts/connexions dans la knowledge base.

---

## Notes

- Les fichiers dans `references/` restent tels quels (pas modifiés)
- Le compilateur crée des **articles dérivés** dans `knowledge/`
- Tu peux mettre à jour `references/` à tout moment
