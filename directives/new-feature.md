# Directive — Nouvelle Fonctionnalité

## Objectif

Implémenter une nouvelle fonctionnalité dans CryptoScanner Pro en respectant l'architecture et les conventions du projet.

## Agent responsable

`.claude/agents/dev/feature.md`

## Entrées

- Description de la feature et son objectif
- Rôles autorisés à y accéder (visitor / member / paid / vip / admin)
- Données requises et sources

## Procédure

### 1. Comprendre l'existant

- Lire `CLAUDE.md` et `agent.md` pour l'architecture globale
- Identifier les fichiers concernés (routes dans `app.py`, moteur dans `*_engine.py`, template)
- Vérifier si un script existant couvre déjà partiellement le besoin

### 2. Proposer un plan

Avant tout code, présenter :
- Fichiers à créer ou modifier
- Approche d'implémentation
- Impact sur les fonctionnalités existantes
- Variables d'environnement requises si nouvelles

### 3. Implémenter

Respecter les conventions :

| Élément | Convention |
|---------|-----------|
| Routes | Dans `app.py` |
| Logique métier lourde | Dans un fichier `{module}_engine.py` dédié |
| Appels IA | Via `ai_provider.py` uniquement |
| Templates | Dans `templates/` — suivre le style existant |
| Configuration | Via `config.py` ou `os.environ.get()` |
| Auth/rôles | Via `security.py` — ne pas réinventer |

### 4. Contrôle d'accès

Appliquer le bon niveau d'accès :
```python
# Exemples de patterns Flask pour les rôles
@require_role('member')   # member+
@require_role('paid')     # paid+
@require_role('admin')    # admin seulement
```

### 5. Tester

- Local : `python app.py` → `http://localhost:5000`
- Tester le chemin nominal (golden path)
- Tester les cas d'erreur (données manquantes, accès non autorisé)

### 6. Documenter

- Mettre à jour `README.md` si la feature est visible dans les "Fichiers principaux" ou "Priorités de suite"
- Mettre à jour `memory/projets/cryptoscanner/data/roadmap.md` si la feature était dans la roadmap

## Règles

- Ne jamais modifier une fonctionnalité existante si la nouvelle feature peut être ajoutée sans la toucher
- Si une modification de `security.py` est nécessaire : demander confirmation explicite
- Si de nouvelles dépendances sont requises : les ajouter dans `requirements.txt` et vérifier la compatibilité Railway
- Si de nouvelles variables d'environnement sont requises : les documenter dans `README.md` section "Variables utiles"
