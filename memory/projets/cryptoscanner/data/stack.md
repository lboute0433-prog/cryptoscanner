---
tags: [projet/cryptoscanner, type/stack]
---

# Stack Technique — CryptoScanner Pro

## Backend

| Composant | Version | Fichier principal |
|-----------|---------|-------------------|
| Python | 3.11 | `runtime.txt` |
| Flask | latest | `app.py` |
| Flask-SocketIO | latest | `app.py` |
| SQLite | built-in | `cryptoscanner.db` |
| WSGI | gunicorn | `wsgi.py` |

## Déploiement

| Élément | Détail |
|---------|--------|
| Plateforme | Railway |
| Config | `railway.json`, `Procfile` |
| Dépendances | `requirements.txt` |

## Intelligence Artificielle

| Provider | Rôle | Variable |
|----------|------|----------|
| Groq | Principal | `GROQ_API_KEY` |
| Anthropic | Fallback | `ANTHROPIC_API_KEY` |
| Couche commune | `ai_provider.py` | `AI_PROVIDER` |

**Règle** : toujours passer par `ai_provider.py` — jamais d'appel direct.

## Sources de données

| Source | Usage | Type |
|--------|-------|------|
| CoinGecko | Couverture large, discovery, investor | Gratuit |
| Binance / Kraken | Scanner spot principal | API |
| Bybit / OKX | Multi-exchange et perpétuels | API |
| CFTC | Rapports COT | Public |
| Yahoo Finance | ETF, macro (backup) | Gratuit |
| RSS FR + EN | News crypto et macro | Public |

## Scripts principaux

| Script | Taille | Rôle |
|--------|--------|------|
| `app.py` | 67KB | Application Flask principale |
| `scanner_engine.py` | 60KB | Scanner crypto multi-exchange |
| `cot_engine.py` | 45KB | Analyse COT/CFTC |
| `news_macro.py` | 39KB | News et calendrier macro |
| `indices_engine.py` | 39KB | Indices macro |
| `morning_brief.py` | 37KB | Morning Brief IA |
| `forex_engine.py` | 30KB | Forex |
| `backtest_engine.py` | 22KB | Backtesting |
| `daily_report.py` | 23KB | Rapport Telegram |
| `smart_signals.py` | 17KB | Signaux de trading |
| `security.py` | 33KB | Auth + rôles |
| `ai_provider.py` | 4.5KB | Couche IA unifiée |

## Frontend

| Fichier | Taille | Rôle |
|---------|--------|------|
| `templates/index.html` | 472KB | Dashboard principal |
| `templates/admin.html` | 39KB | Panel admin |

## Variables d'environnement

```
SECRET_KEY            ← Sécurité Flask (obligatoire)
RUN_BACKGROUND_JOBS   ← "true" pour les jobs auto
DATABASE_PATH         ← Chemin vers cryptoscanner.db
AI_PROVIDER           ← "groq" ou "anthropic"
GROQ_API_KEY
ANTHROPIC_API_KEY
TG_TOKEN              ← Bot Telegram
TG_CHAT               ← Canal Telegram
SMTP_SERVER, SMTP_PORT, SMTP_LOGIN, SMTP_PASSWORD
SMTP_FROM_EMAIL, ADMIN_NOTIFY_EMAIL
```
