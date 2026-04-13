# Directive — Déploiement Railway

## Objectif

Déployer une version stable de CryptoScanner Pro sur Railway.

## Agent responsable

`.claude/agents/dev/feature.md` (valide le code) + déploiement manuel

## Prérequis

- Code testé en local (`python app.py`, `http://localhost:5000`)
- Aucun bug bloquant connu
- `requirements.txt` à jour
- Variables d'environnement configurées dans Railway

## Fichiers de déploiement

| Fichier | Rôle |
|---------|------|
| `railway.json` | Configuration Railway (build, start command) |
| `Procfile` | Commande de démarrage (Railway/Heroku) |
| `runtime.txt` | Version Python (3.11) |
| `requirements.txt` | Dépendances Python |
| `wsgi.py` | Point d'entrée WSGI |

## Variables d'environnement à vérifier sur Railway

Variables critiques à configurer dans le dashboard Railway :
```
SECRET_KEY            ← Obligatoire (sécurité Flask)
DATABASE_PATH         ← Chemin SQLite (ex: /data/cryptoscanner.db)
RUN_BACKGROUND_JOBS   ← "true" pour activer les jobs auto
AI_PROVIDER           ← "groq" ou "anthropic"
GROQ_API_KEY
ANTHROPIC_API_KEY
TG_TOKEN
TG_CHAT
ADMIN_NOTIFY_EMAIL
```

## Procédure

1. **Tester** en local : `python app.py` → vérifier `http://localhost:5000`
2. **Vérifier** `requirements.txt` : toutes les dépendances présentes ?
3. **Vérifier** que les fichiers modifiés sont dans le bon état
4. **Commiter** et pousser sur le branch de déploiement
5. **Surveiller** les logs Railway pendant le build
6. **Vérifier** le déploiement : `http://{app}.railway.app`
7. **Tester** les fonctionnalités critiques en production

## Cas limites

- **Build failure** : lire les logs Railway, identifier la dépendance ou l'erreur de config
- **Import error** : dépendance manquante dans `requirements.txt`
- **500 en production** : activer les logs détaillés, reproduire en local
- **Variables d'env manquantes** : vérifier dans Railway → Settings → Variables
- **Base de données** : sur Railway, utiliser un volume persistant pour SQLite ou migrer vers PostgreSQL

## Points d'attention Railway

- SQLite sur Railway : les fichiers sont éphémères sauf volume monté — vérifier `DATABASE_PATH`
- Le `Procfile` définit la commande de démarrage — ne pas modifier sans tester
- Si `RUN_BACKGROUND_JOBS=true`, les jobs tournent dans le même processus
