# Directive — Debug

## Objectif

Diagnostiquer et corriger un bug avec un impact minimal sur le code existant.

## Agent responsable

`.claude/agents/dev/debugger.md`

## Entrées

- Message d'erreur ou traceback
- Description du comportement observé vs attendu
- Contexte : local ou production Railway

## Procédure

### 1. Lire et comprendre l'erreur

- Lire le message d'erreur **complet** (ne pas s'arrêter à la première ligne)
- Identifier : quel fichier, quelle ligne, quelle fonction
- Identifier : quel type d'erreur (TypeError, ImportError, HTTPError, SQLite...)

### 2. Reproduire si possible

- En local : `python app.py` puis reproduire l'action qui déclenche l'erreur
- Lire les logs dans le terminal ou dans Railway → Deployments → Logs

### 3. Lire le code concerné

- Lire le fichier et la ligne identifiés
- Remonter dans la stack trace jusqu'à la cause racine

### 4. Corriger (fix minimal)

- Appliquer le correctif le plus petit possible
- Ne pas refactorer du code non lié au bug
- Si l'impact est incertain : proposer le fix et demander confirmation

### 5. Valider

- Relancer le test minimal qui reproduisait le bug
- Vérifier qu'il ne réapparaît pas
- Vérifier les fonctionnalités adjacentes (pas de régression)

### 6. Documenter si non-évident

- Ajouter un commentaire si la cause était subtile
- Mettre à jour `memory/agents/debugger/notes.md` si pattern récurrent

## Règles de sécurité

- **API payantes** (Groq, Anthropic, exchanges) : confirmer avec l'utilisateur avant de relancer un test qui consomme des crédits
- **Base de données** : ne jamais modifier `cryptoscanner.db` directement — passer par le code
- **Variables d'environnement** : ne jamais afficher les valeurs de clés API dans les logs ou le chat

## Patterns d'erreurs fréquents

| Erreur | Cause probable | Solution |
|--------|---------------|----------|
| `ModuleNotFoundError` | Dépendance manquante | Ajouter dans `requirements.txt`, `pip install` |
| `KeyError: 'GROQ_API_KEY'` | Variable d'env manquante | Vérifier `.env` ou Railway Variables |
| `sqlite3.OperationalError` | Chemin DB incorrect | Vérifier `DATABASE_PATH` |
| `ConnectionError` exchange | API externe down | Vérifier statut exchange, réessayer |
| `Telegram 401` | TG_TOKEN invalide | Régénérer le token via BotFather |
| Flask `500` | Exception non catchée | Lire le traceback dans les logs |
| `AttributeError: NoneType` | Donnée manquante non gérée | Ajouter validation avant utilisation |
