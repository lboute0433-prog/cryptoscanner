# Directive — Scanner Marché

## Objectif

Exécuter le scanner crypto multi-exchange et produire un rapport de signaux exploitable.

## Agent responsable

`.claude/agents/marche/scanner.md`

## Entrées

- Exchange(s) cible(s) : Binance, Kraken, Bybit, OKX, CoinGecko
- Paires à scanner (ou "toutes")
- Paramètres spécifiques si fournis (timeframe, seuil de variation)

## Scripts à utiliser

| Ordre | Script | Action |
|-------|--------|--------|
| 1 | `scanner_engine.py` | Scan principal multi-exchange |
| 2 | `smart_signals.py` | Filtrage et génération des signaux |
| 3 | `ai_provider.py` | Analyse IA des signaux (optionnel) |

## Procédure

1. **Vérifier** les variables d'environnement requises (clés API exchanges si nécessaire)
2. **Lire** `scanner_engine.py` pour identifier la fonction d'entrée principale
3. **Exécuter** le scan sur les exchanges/paires demandés
4. **Filtrer** les signaux via `smart_signals.py`
5. **Interpréter** les résultats (variations, volumes, confluences)
6. **Produire** le rapport au format standard

## Sorties

- Rapport de scan avec liste des signaux détectés
- Paires notables avec variation, volume et exchange
- Points d'attention identifiés

## Cas limites

- **Rate limit exchange** : attendre et réessayer, ou utiliser un exchange alternatif
- **Exchange indisponible** : noter dans le rapport, continuer avec les autres
- **Aucun signal significatif** : indiquer clairement "marché calme" avec les données brutes
- **Clé API manquante** : signaler à l'utilisateur avant d'exécuter

## Fréquence recommandée

- Scan spot : à la demande ou en arrière-plan (`RUN_BACKGROUND_JOBS=true`)
- Rapport complet : matin avant le Morning Brief
