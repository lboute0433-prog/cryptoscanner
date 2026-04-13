---
tags: [projet/cryptoscanner, type/roles]
---

# Rôles et Accès — CryptoScanner Pro

## Rôles utilisateurs

| Rôle | Accès |
|------|-------|
| `visitor` | Pages publiques uniquement |
| `member` | Outils personnels (portfolio, journal, alertes, watchlist) |
| `paid` | Modules premium (COT, ETF, IA, backtests) |
| `vip` | Accès complet premium + fonctionnalités exclusives |
| `admin` | Gestion globale (panel admin, diagnostics) |
| `banned` | Accès bloqué |

## Statuts d'abonnement

| Statut | Description |
|--------|-------------|
| `inactive` | Pas d'abonnement actif |
| `trial` | Période d'essai en cours |
| `active` | Abonnement actif |
| `overdue` | Paiement en retard |
| `canceled` | Abonnement annulé |

## Règles d'accès par module

| Module | Accès minimum |
|--------|--------------|
| Dashboard, pages publiques | `visitor` |
| Portfolio personnel | `member+` |
| Journal de trading | `member+` |
| Alertes et watchlist | `member+` |
| Scanner avancé | `paid+` |
| COT / CFTC | `paid+` |
| ETF tracker | `paid+` |
| Analyses IA | `paid+` |
| Backtesting | `paid+` |
| Panel admin | `admin` |

## Implémentation

- Logique d'authentification et de rôles : `security.py`
- **Ne jamais modifier `security.py`** sans comprendre l'impact sur tous les modules

## Patterns Flask (référence rapide)

```python
# Restreindre une route à un rôle minimum
@require_role('paid')
def ma_route_premium():
    ...

# Vérifier le rôle dans le code
if user.role in ['paid', 'vip', 'admin']:
    ...
```
