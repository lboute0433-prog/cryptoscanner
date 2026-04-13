---
tags: [projet/cryptoscanner, type/sources]
---

# Sources de Données — CryptoScanner Pro

## Principe

La logique retenue n'est pas "une seule source pour tout", mais **une source maîtresse par usage**.

## Crypto

| Source | Usage maître | Script | Notes |
|--------|-------------|--------|-------|
| CoinGecko | Discovery, couverture large, données investor | `scanner_engine.py` | Gratuit, large couverture |
| Binance | Scanner spot principal | `scanner_engine.py` | API key optionnelle |
| Kraken | Scanner spot (alternative) | `scanner_engine.py` | Haute qualité |
| Bybit | Perpétuels, multi-exchange | `scanner_engine.py` | Données dérivés |
| OKX | Perpétuels, open interest | `scanner_engine.py` | Données dérivés |

## Institutionnel / Macro

| Source | Usage maître | Script | Notes |
|--------|-------------|--------|-------|
| CFTC | Rapports COT (Commitments of Traders) | `cot_engine.py` | Public, hebdomadaire |
| Yahoo Finance | ETF, indices macro (backup) | `indices_engine.py` | Gratuit, parfois instable |

## News & Calendrier

| Source | Usage | Script | Notes |
|--------|-------|--------|-------|
| RSS FR + EN | News crypto et macro | `news_macro.py` | Gratuit |
| Calendrier macro | Événements économiques | `news_macro.py` | Sources multiples |

## IA

| Provider | Rôle | Clé |
|----------|------|-----|
| Groq | Principal (rapide, économique) | `GROQ_API_KEY` |
| Anthropic | Fallback (qualité, fiabilité) | `ANTHROPIC_API_KEY` |

Toujours passer par `ai_provider.py` — jamais d'appel direct.
