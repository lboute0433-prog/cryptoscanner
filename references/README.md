# Références — Système Memory Personnel

Dossier de stockage **persistent** pour vos articles, données, idées. Claude lit automatiquement ces fiches et les utilise pour vous aider et s'améliorer.

## Structure

```
references/
├── articles/        # Articles, blog posts, analyses, rapports
├── donnees/         # Données, stats, benchmarks, résultats
├── idees/           # Idées, brainstorm, TODO, concepts
└── README.md        # Ce fichier
```

## Mode d'emploi

### 1. Créer une note

**Exemple article** (`articles/analyse-bitcoin-macro.md`):
```markdown
# Analyse Bitcoin Macro 2026

## Contexte
- Tendance: Hausse depuis 2024
- Support: $40k
- Résistance: $100k

## Conclusions
- RSI en zone neutre
- Volume en hausse
- Dominance BTC stable à 58%
```

**Exemple donnée** (`donnees/metriques-portfolio.md`):
```markdown
# Métriques Portfolio Q1 2026

| Coin | Prix | % Portefeuille |
|------|------|---|
| BTC | $78k | 45% |
| ETH | $2.3k | 30% |
| SOL | $180 | 25% |

**Total**: $150k (+12% YoY)
```

**Exemple idée** (`idees/features-futures.md`):
```markdown
# Features À Implémenter

- [ ] Scanner whale tracking temps réel
- [ ] Alertes multi-exchange fusion
- [ ] Dashboard personnalisé par utilisateur
- [ ] API REST publique

## Priorité
1. Whale tracking (urgent)
2. API REST (Q2)
```

### 2. Convention de nommage

- **Articles** : `titre-en-kebab-case.md` (ex: `analyse-ethereum-2026.md`)
- **Données** : `metriques-domaine-period.md` (ex: `donnees-btc-daily-avril.md`)
- **Idées** : `categorie-description.md` (ex: `features-priority.md`, `brainstorm-api-mix.md`)

### 3. Claude lit automatiquement

À chaque session, Claude:
1. **Lit** toutes les fiches dans `references/`
2. **Comprend** votre contexte (données, idées, articles)
3. **Utilise** ces infos pour adapter ses réponses
4. **S'améliore** en connaissant mieux votre domaine

**Résultat** : Plus vous remplissez `references/`, plus Claude vous aide bien!

## Conventions en Français

⚠️ **Important** : Tous les fichiers `references/` doivent être **100% en français**.

- Titres en français
- Contenu en français
- Pas de termes anglais (ou entre guillemets)

Exemple ✅ :
```markdown
# Analyse Données Crypto

- Graphique: up-trend
- Stratégie: mean-reversion sur la dominance BTC
```

Exemple ❌ :
```markdown
# Analysis of Crypto Data

- Chart: up-trend
- Strategy: mean-reversion on BTC dominance
```

---

**Créé** : 2026-04-24
**Statut** : Template pour memory system français
