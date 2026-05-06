# Plan Hybride — API Mix + Agents + Local Testing

## Scope

**Critiques (Phase 1):**
- CoinGecko (prix BTC/ETH) + fallback CoinMarketCap
- Binance API (volumes/orderbook)
- Arkham Intelligence (whales)

**Importants (Phase 2):**
- CoinPaprika (OHLC historique)
- Glassnode (on-chain metrics)
- DexScreener (DEX prices)

**Optionnels (Phase 3):**
- LunarCrush (sentiment, cache 1h)
- Finnhub (macro forex)

---

## Agents + Tasks

### Agent: Feature Developer
**Task 1: Créer api_manager.py**
- Orchestrateur des APIs (smart_fetch, fallbacks, caching)
- Circuit breaker (gestion des timeouts)
- Rate limiter (max 100 req/min distribué)
- Status: local/ folder, non intégré à app.py encore

**Task 2: Créer api_coingecko.py + api_binance.py**
- Wrappers pour APIs critiques
- Tests unitaires (curl mock)
- Logge les calls + latences

---

### Agent: Scanner
**Task 3: Tester les APIs localement**
- CURL sur chaque endpoint (gratuit)
- Validate responses format
- Mesurer latence (CoinGecko ~200ms, Binance ~150ms)
- Document limits: CoinGecko 30/min, Binance illimité, Arkham limité

**Task 4: Créer api_stack_test.py**
- Test suite pour toutes les APIs
- Mock responses (pas vrais appels)
- Verify fallback logic marche

---

### Agent: Feature Developer (suite)
**Task 5: Intégrer dans app.py (modifiée)**
- Créer copie `app_new.py` (pas toucher original)
- Replace `/api/crypto/total3` → api_manager.smart_fetch('price')
- Replace `/api/crypto/others` → api_manager.smart_fetch('others')
- Replace `/api/whales` → api_manager.smart_fetch('whales')
- Keep old endpoints (fallback si bug)

---

### Agent: Debugger
**Task 6: Test de regression**
- Lance `app_new.py` localement
- Vérifie endpoints retournent mêmes données
- Vérifie fallbacks marchent (kill une API, test l'autre)
- Mesure latence vs app.py original

**Task 7: Fix bugs trouvés**
- Rate limit trop agressif? Adjust
- Timeout trop court? Augmente
- Cache trop long? Réduit

---

## Structure de code local

```
Antigravity--cryptoscanner/
├── scripts/
│   ├── compile.py (existant)
│   └── api_mix/                    ← NOUVEAU
│       ├── __init__.py
│       ├── api_manager.py          (orchestrateur)
│       ├── api_coingecko.py        (prices)
│       ├── api_binance.py          (volumes)
│       ├── api_arkham.py           (whales)
│       ├── cache_manager.py        (caching local)
│       ├── rate_limiter.py         (rate limit)
│       └── tests/
│           ├── test_apis.py        (unitaire)
│           ├── test_fallbacks.py   (redondance)
│           └── mock_responses.json (fixtures)
│
├── app.py                          (original, inchangé)
├── app_new.py                      (nouvelle version test)
└── logs/
    └── api_calls.log               (monitoring)
```

---

## Phases locales (timeline)

**Phase 1 (Day 1 - 4h):**
- Feature: Créer api_manager.py + api_coingecko + api_binance
- Scanner: Tester endpoints curl (sans code)
- Feature: Créer app_new.py (copie test)

**Phase 2 (Day 2 - 3h):**
- Feature: Intégrer api_manager dans app_new.py endpoints
- Debugger: Test regression (vs app.py original)
- Debugger: Fix bugs trouvés

**Phase 3 (Day 3 - 2h):**
- Feature: Ajouter APIs importants (CoinPaprika, Glassnode)
- Scanner: Valider toutes les APIs en parallel
- Documenté: Logs performance dans memory/projets/

---

## Déploiement Hetzner (Phase 4, PLUS TARD)

```
JAMAIS avant que app_new.py soit validé localement 100%.

Checklist déploiement:
[ ] app_new.py passe tous les tests locaux
[ ] Fallbacks testés manuellement
[ ] Rate limits OK sous charge 100 users
[ ] Logs tournent proprement 24h en local
[ ] Zéro bug critique détecté

Seulement APRÈS:
1. Copier api_mix/ sur Hetzner
2. Copier app_new.py → app.py
3. Test en live 1h (petit traffic)
4. Rollback rapide si pb (garder ancien app.py)
```

---

## Points de risque + mitigation

| Risque | Mitigation |
|--------|-----------|
| API down pendant test | Fallbacks testés d'abord en local |
| Rate limit hit | Rate limiter + queue système |
| Cache stale | TTL court (30s prix, 1h sentiment) |
| Code complexe = bugs | Tests unitaires avant intégration |
| Hetzner crash | Stay local, deploy après validation |

---

## Validation avant Hetzner

```python
# En local, tester ça:
assert api_manager.smart_fetch('price') returns valid data
assert fallback works when primary is down
assert rate_limit doesn't exceed 100/min
assert latency < 500ms (P95)
assert no price discrepancies between APIs
```

---

**Prêt à lancer Phase 1 ?**
