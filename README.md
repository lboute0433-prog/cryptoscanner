# CryptoScanner Pro

Notice de référence rapide du projet.

## Vue d'ensemble

CryptoScanner Pro est une application Flask de suivi et d'analyse de marche orientee crypto, macro et trading. Le projet combine:

- dashboard web,
- espace membre,
- administration,
- signaux et outils de trading,
- COT / ETF / open interest / liquidations,
- news et calendrier macro,
- Morning Brief,
- rapports Telegram,
- analyses IA.

## Stack

- Backend: Python 3.11, Flask, Flask-SocketIO
- Frontend: HTML, CSS, JavaScript
- Base locale: SQLite
- Deploiement actuel: Railway

## Fichiers principaux

- [app.py](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/app.py)
- [scanner_engine.py](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/scanner_engine.py)
- [cot_engine.py](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/cot_engine.py)
- [news_macro.py](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/news_macro.py)
- [morning_brief.py](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/morning_brief.py)
- [daily_report.py](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/daily_report.py)
- [ai_provider.py](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/ai_provider.py)
- [templates/index.html](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/templates/index.html)
- [templates/admin.html](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/templates/admin.html)

## Acces et roles

Le projet utilise maintenant une logique de roles et d'abonnement plus claire.

Roles supportes:

- `visitor`
- `member`
- `paid`
- `vip`
- `admin`
- `banned`

Statuts d'abonnement:

- `inactive`
- `trial`
- `active`
- `overdue`
- `canceled`

Principes:

- `member+` pour les outils personnels comme portefeuille, journal, alertes et watchlist
- `paid+` pour les modules premium comme COT, ETF, IA et backtests
- `admin` pour la gestion globale

## Sources de donnees

La logique retenue n'est pas "une seule source pour tout", mais une source maitresse par usage.

- `CoinGecko`: couverture large, discovery, investor
- `Binance` ou `Kraken`: scanner spot principal
- `Bybit` et `OKX`: multi-exchange et perps
- `CFTC`: rapports COT
- `Yahoo Finance` et sources de secours: certaines donnees ETF ou macro quand necessaire
- `RSS FR + EN`: news crypto et macro

## IA

L'IA passe maintenant par une couche commune:

- provider principal vise: `Groq`
- fallback compatible: `Anthropic`

Le module commun est:

- [ai_provider.py](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/ai_provider.py)

Usages deja relies a cette couche:

- Morning Brief
- analyse investisseur
- futures analyses premium

## Email

Le projet dispose d'un meilleur diagnostic SMTP, mais l'envoi email de production n'est pas encore finalise.

Etat actuel:

- diagnostic SMTP visible dans l'admin,
- test d'envoi admin disponible,
- compatibilite `SMTP_LOGIN` et `SMTP_FROM_EMAIL`,
- Gmail SMTP teste mais peu fiable sur l'hebergement actuel,
- migration future recommandee vers un provider transactionnel avec domaine verifie.

## Installation locale

1. Installer Python 3.11
2. Installer les dependances:

```bash
pip install -r requirements.txt
```

3. Lancer l'application:

```bash
python app.py
```

4. Ouvrir:

- `http://localhost:5000`
- admin: `http://localhost:5000/admin`

## Variables utiles

Exemples de variables importantes:

- `SECRET_KEY`
- `RUN_BACKGROUND_JOBS`
- `DATABASE_PATH`
- `TG_TOKEN`
- `TG_CHAT`
- `AI_PROVIDER`
- `GROQ_API_KEY`
- `ANTHROPIC_API_KEY`
- `SMTP_SERVER`
- `SMTP_PORT`
- `SMTP_LOGIN`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `ADMIN_NOTIFY_EMAIL`

## Documents utiles

- recap produit et technique: [PLAN_EMAIL_ACCES_IA.md](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/PLAN_EMAIL_ACCES_IA.md)
- documentation plus large: [CRYPTOSCANNER_DOC.md](C:/Users/loyan/Documents/CryptoScanner%20Codex%20Projet/cryptoscanner-main-cryptoScanner-Codex/CRYPTOSCANNER_DOC.md)

## Priorites de suite

- finaliser les ajustements UI et wording restants
- consolider le portfolio multi-exchange
- poursuivre l'uniformisation IA
- reprendre l'email plus tard avec domaine et provider adaptes
