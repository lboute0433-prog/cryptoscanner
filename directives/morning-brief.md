# Directive — Morning Brief

## Objectif

Générer le Morning Brief quotidien via `morning_brief.py` et la couche IA.

## Agent responsable

`.claude/agents/reporting/morning-brief.md`

## Entrées

- Date du jour
- Données marché disponibles (scanner, indices, news)
- Provider IA actif (Groq ou Anthropic)

## Scripts à utiliser

| Ordre | Script | Action |
|-------|--------|--------|
| 1 | `morning_brief.py` | Génération principale du brief |
| 2 | `ai_provider.py` | Couche IA (Groq principal → Anthropic fallback) |
| 3 | `news_macro.py` | Enrichissement avec actualités |
| 4 | `scanner_engine.py` | Données marché du matin |

## Variables d'environnement requises

```
AI_PROVIDER       ← "groq" ou "anthropic" (défaut: groq)
GROQ_API_KEY      ← Obligatoire si AI_PROVIDER=groq
ANTHROPIC_API_KEY ← Obligatoire si AI_PROVIDER=anthropic ou fallback
```

## Procédure

1. **Vérifier** que les variables IA sont définies
2. **Exécuter** `morning_brief.py`
3. **Vérifier** la structure du brief généré :
   - Résumé exécutif présent
   - Données crypto incluses (BTC, ETH minimum)
   - Section macro présente
   - News filtrées (3-5 max)
4. **Valider** avec l'utilisateur avant publication
5. **Transmettre** à l'agent Rapport pour envoi si demandé

## Sorties

- Texte structuré du Morning Brief
- Prêt à être envoyé via Telegram (`daily_report.py`) ou affiché dans le dashboard

## Cas limites

- **Groq indisponible** : basculer automatiquement sur Anthropic (`ai_provider.py` gère le fallback)
- **Les deux providers indisponibles** : générer un brief minimal avec données brutes sans IA
- **Données marché manquantes** : indiquer "données indisponibles" pour la section concernée
- **Brief vide ou malformé** : signaler à l'utilisateur avant tout envoi

## Fréquence recommandée

- Une fois par matin, idéalement avant 9h
- Peut être déclenché manuellement ou via `RUN_BACKGROUND_JOBS=true`
