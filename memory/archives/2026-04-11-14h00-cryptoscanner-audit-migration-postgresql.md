---
date: 2026-04-11
heure: "14:00"
projet: cryptoscanner
phase: développement actif
tags: [projet/cryptoscanner, type/archive]
---

# Session 2026-04-11 14h00 — CryptoScanner Audit + Migration PostgreSQL

## Résumé
Audit complet du projet CryptoScanner Pro V11 (note globale 6/10). Correction des 3 problèmes critiques identifiés (fake whale alerts, fallback base64, nettoyage artefacts). Création d'une couche d'abstraction DB (`db.py`) rendant l'application portable SQLite ↔ PostgreSQL avec zéro changement de logique métier.

## Travail effectué
- Audit complet du projet : structure, qualité code, sécurité, opérations
- Fix fake whale alerts : `scanner_engine.py` retourne `[]` sans `WHALE_API_KEY` (suppression données fictives)
- Fix fallback base64 : `security.py` lève `RuntimeError` si `cryptography`/`bcrypt` absent (fail-hard)
- Nettoyage : 4 fichiers Qwen supprimés, 3 mockups HTML supprimés, `INTEGRATION_V11.py` archivé dans `memory/archives/`
- Création `db.py` : adapter SQLite ↔ PostgreSQL (auto-détection via `DATABASE_URL`)
  - Convertit `?` → `%s`, `INSERT OR REPLACE` → `ON CONFLICT DO UPDATE`, `AUTOINCREMENT` → `SERIAL`
  - Interface 100% compatible sqlite3 (row_factory, executescript, commit, close...)
  - `get_columns()` remplace les `PRAGMA table_info()` SQLite-only
- Remplacement de 86 appels `sqlite3.connect()` dans 10 fichiers par `get_connection()`
- Ajout `psycopg2-binary==2.9.9` dans `requirements.txt`
- Création `.claude/launch.json` avec configurations des serveurs dev

## Décisions
- **Volume Railway abandonné, migration PostgreSQL complète choisie** : l'utilisateur migre vers un serveur perso pour monétisation — PostgreSQL est la bonne cible long terme
- **Adapter transparent plutôt que réécriture** : `db.py` maintient la compatibilité SQLite (dev local) sans toucher la logique métier dans les 10 fichiers
- **Fail-hard sur dépendances sécurité** : si `cryptography` ou `bcrypt` manquent, l'app refuse de démarrer plutôt que dégrader silencieusement
- **Pas de migration des données SQLite existantes** : à gérer manuellement au moment du passage en prod PostgreSQL

## État du projet
- Phase actuelle : Développement actif — prêt pour déploiement Railway
- Validé : Adapter DB PostgreSQL testé (syntaxe + transformations SQL + get_columns), imports OK
- En cours : Déploiement Railway (l'utilisateur gère lui-même)
- Suspens : Migration données SQLite → PostgreSQL (quand passage en prod)

## Prochaines étapes
1. Déployer sur Railway (push git) — fonctionne en SQLite sans config
2. Pour activer PostgreSQL : ajouter plugin PostgreSQL Railway → `DATABASE_URL` auto-injectée
3. Migrer les données SQLite existantes si nécessaire (script à créer)
4. Sprint suivant : extraire `indicators.py` (dédupliquer RSI/EMA/Bollinger)
5. Ajouter logging centralisé (remplacer `except: pass` par `logger.error()`)
6. CSRF Flask-WTF sur routes POST critiques

## Fichiers modifiés
- `db.py` — créé (adapter SQLite ↔ PostgreSQL)
- `requirements.txt` — ajout psycopg2-binary==2.9.9
- `scanner_engine.py` — fake whale alerts supprimées + `from db import get_connection` + 45 remplacements connect()
- `security.py` — fail-hard cryptography/bcrypt + PRAGMA remplacés par get_columns() + 13 remplacements connect()
- `news_macro.py` — from db import + 7 remplacements
- `cot_engine.py` — from db import + 4 remplacements
- `backtest_engine.py` — from db import + 3 remplacements
- `indices_engine.py` — from db import + 1 remplacement
- `forex_engine.py` — from db import + 1 remplacement
- `morning_brief.py` — from db import + 4 remplacements
- `debloquer_admin.py` — from db import + logique is_postgres()
- `.claude/launch.json` — créé (configurations serveurs dev)
- `memory/archives/INTEGRATION_V11.py` — archivé depuis racine
- Supprimés : `Qwen_python_20260331_*.py` (x3), `Qwen_txt_*.txt`, `templates/mockup_*.html` (x3)

## Assets (URLs)
Aucun.
