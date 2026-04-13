---
tags: [projet/cryptoscanner, type/roadmap]
---

# Roadmap — CryptoScanner Pro

## En cours / Priorités actives

- [ ] Finaliser les ajustements UI et wording restants
- [ ] Consolider le portfolio multi-exchange
- [ ] Poursuivre l'uniformisation IA (tous les modules via `ai_provider.py`)

## En attente / Dépendances externes

- [ ] Email production : reprendre plus tard avec domaine vérifié et provider transactionnel
  - État : Gmail SMTP peu fiable sur Railway
  - Prochaine action : migrer vers Mailgun, Resend ou SendGrid avec domaine personnalisé

## Modules existants (déployés)

- [x] Dashboard web avec espace membre
- [x] Administration (`/admin`)
- [x] Scanner crypto multi-exchange (Binance, Kraken, Bybit, OKX, CoinGecko)
- [x] Signaux de trading (`smart_signals.py`)
- [x] Analyse COT/CFTC (`cot_engine.py`)
- [x] Indices macro (`indices_engine.py`)
- [x] Forex (`forex_engine.py`)
- [x] News + calendrier macro (`news_macro.py`)
- [x] Morning Brief IA (`morning_brief.py`)
- [x] Rapport Telegram quotidien (`daily_report.py`)
- [x] Backtesting (`backtest_engine.py`)
- [x] Système de rôles et abonnements (`security.py`)
- [x] Diagnostic SMTP dans l'admin
- [x] Couche IA unifiée Groq + Anthropic (`ai_provider.py`)

## Idées futures (non priorisées)

- Alertes prix en temps réel (WebSocket)
- Portfolio tracker multi-exchange consolidé
- Backtests paramétrables depuis le dashboard
- Intégration Webhook Telegram pour commandes
