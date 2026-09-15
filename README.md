# Relais Farside — flux ETF spot

Cette branche ne contient **que** le relais qui alimente ApexView en flux
ETF spot Bitcoin et Ethereum. Elle est volontairement isolée du code de
l'application.

## Pourquoi ce relais existe

Farside Investors publie l'historique complet des flux depuis le
lancement des ETF (11 janvier 2024). Le site est derrière Cloudflare, qui
**refuse les IP de datacenter** : mesuré le 15/09/2026, HTTP 200 depuis
une machine résidentielle et **HTTP 403 depuis le serveur** — avec quatre
jeux d'en-têtes différents, jusqu'au jeu navigateur complet. Ce n'est donc
pas une question d'en-tête, c'est l'adresse IP.

Les exécuteurs GitHub Actions sortent par des adresses acceptées. Le
workflow télécharge la page **une fois par jour** et publie deux fichiers
JSON ; le serveur ApexView les lit ensuite via `raw.githubusercontent.com`,
joignable en 0,22 s.

Une requête quotidienne, pas une par visiteur : la charge imposée à la
source reste négligeable.

## Contenu

| Fichier | Rôle |
|---|---|
| `scripts/farside_fetch.py` | téléchargement et analyse du tableau |
| `.github/workflows/farside.yml` | exécution quotidienne à 06:20 UTC |
| `data/farside_btc.json` | 687 jours depuis le 11/01/2024 |
| `data/farside_eth.json` | 549 jours depuis le 23/07/2024 |

## Vérification croisée

Le cumul calculé par ce script — **55 384 M$** pour BTC — a été comparé à
une source indépendante exploitant la même page : **55 383,5 M$**. Soit
0,5 M$ d'écart sur 55 milliards.
