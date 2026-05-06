# Convention — 100% Français

À partir de 2026-04-24, tout le système CryptoScanner fonctionne **100% en français**.

## Périmètre

✅ **Français obligatoire** :
- Tous les fichiers markdown (`*.md`)
- Tous les fichiers dans `memory/` (archives, contexte, notes)
- Tous les fichiers dans `references/` (articles, données, idées)
- Tous les commentaires de code Python/JS (si pertinent)
- Tous les logs et output (si possible)

✅ **Code reste multilingue** :
- Code Python/JavaScript (conventions standards)
- Variables et fonction names (conventions standards)
- Commentaires techniques (peuvent être en anglais si clairs)

## Exemples

### ✅ Bon
```markdown
# Architecture API Mix

## Contexte
Orchestration intelligente des APIs gratuites.

## Phase 3 — Déploiement
- [x] Backup app.py
- [x] Deploy app_new.py
- [ ] Configurer SSL
```

### ✅ Bon aussi
```python
def fetch_price_coingecko(coins):
    """Récupère les prix depuis CoinGecko"""
    response = requests.get(COINGECKO_URL, params={'ids': coins})
    return response.json()
```

### ❌ Mauvais
```markdown
# API Mix Architecture

English content here... should be in French.
```

### ❌ Mauvais aussi
```python
# Bad: mixing French and English without reason
def get_data():  # Récupère les données
    """Get data from API"""  # Wrong: should be "Récupère données de l'API"
    return api.fetch()
```

## Système Memory — Comment Claude Apprend

À chaque session, Claude :

1. **Lit** les fichiers dans `references/{articles,donnees,idees}/`
2. **Comprend** votre contexte (qu'est-ce qui est important pour vous)
3. **Adapte** ses réponses basé sur vos données/idées
4. **Améliore** ses suggestions en connaissant votre domaine

### Exemple Concret

**Vous créez** `references/donnees/metriques-crypto-avril.md`:
```markdown
# Métriques Crypto — Avril 2026

- BTC: $78k (dominance 58%)
- ETH: $2.3k
- Portfolio total: $150k
```

**Claude utilise** ces données pour:
- Répondre avec chiffres actuels
- Adapter les seuils (ex: "si tu as $150k")
- Proposer stratégies basées sur votre composition réelle

## Prochaines Étapes

1. ✅ **Fait** : Contexte.md traduit, structure references créée
2. ⏭️ **À faire** : Remplir `references/` avec vos premières fiches
3. ⏭️ **À faire** : Claude utilisera vos fiches à partir de la session prochaine

## Contact/Questions

Si une fiche est en anglais par erreur, ou si tu as des questions, signale-le directement!

---

**Convention établie** : 2026-04-24
**Statut** : Actif pour tous les fichiers markdown et memory
