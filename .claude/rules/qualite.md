# Règle — Qualité

## Principes

- Le résultat correspond exactement à la demande — ni plus, ni moins.
- Ne jamais livrer sans vérification : le résultat fait ce qui a été demandé.
- L'orchestrateur ne fait pas le travail lui-même — il délègue au bon spécialiste.
- Si aucun agent n'existe pour la tâche, proposer `/nouveau-agent` avant de continuer.

## Avant chaque livraison

1. Le livrable répond à la demande initiale
2. Le format de livraison est respecté (voir `livraison.md`)
3. Les fichiers créés/modifiés sont aux bons emplacements
4. Aucune régression sur l'existant

## Standards spécifiques à CryptoScanner Pro

- Ne pas modifier les scripts Python existants sans avoir lu leur contenu au préalable
- Ne pas toucher à `app.py` (routes) sans comprendre l'impact sur le frontend
- Toujours vérifier les variables d'environnement nécessaires avant de lancer un script
- Si une modification consomme des crédits API (Groq, Anthropic, exchanges) : demander confirmation avant d'exécuter
