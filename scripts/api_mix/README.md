# API Mix Stack — Phase 1

Smart orchestration des APIs gratuites avec fallbacks automatiques, caching, rate limiting.

## Structure

```
api_mix/
├── __init__.py              # Import principal
├── api_manager.py           # Orchestrateur (circuit breaker, cache, rate limit)
├── api_coingecko.py         # Wrapper CoinGecko (prix, market data, OHLC)
├── api_binance.py           # Wrapper Binance (orderbook, trades, stats)
├── cache_manager.py         # Gestion du cache
├── rate_limiter.py          # Rate limiting (100 req/min max)
└── tests/
    └── test_apis.py         # Tests unitaires

NOT YET:
├── api_coinmarketcap.py     # Fallback prix
├── api_arkham.py            # Whales detection
├── api_glassnode.py         # On-chain metrics
└── tests/
    ├── test_fallbacks.py    # Test circuit breaker
    └── mock_responses.json  # Fixtures
```

## Usage

### 1. Tester CoinGecko localement (curl)

```bash
# Obtenir prix BTC/ETH
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"

# Obtenir market data global
curl "https://api.coingecko.com/api/v3/global"

# Limite: 30 requêtes/min
```

### 2. Tester Binance localement (curl)

```bash
# Prix temps réel BTC
curl "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

# Orderbook
curl "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=10"

# Stats 24h
curl "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"

# Limite: Illimité
```

### 3. Lancer tests unitaires

```bash
cd /path/to/cryptoscanner

# Installer pytest + pytest-asyncio
pip install pytest pytest-asyncio aiohttp

# Lancer les tests
python -m pytest scripts/api_mix/tests/test_apis.py -v

# Résumé attendu:
# test_circuit_breaker_initial_state PASSED
# test_rate_limiter_allows_requests PASSED
# test_cache_set_and_get PASSED
# test_fetch_price_mock PASSED
# test_get_orderbook_mock PASSED
# ... (5-10 tests total)
```

## Phase 1 Checklist

### Agent Feature
- [x] Créer api_manager.py (orchestrateur)
- [x] Créer api_coingecko.py (wrapper)
- [x] Créer api_binance.py (wrapper)
- [ ] Créer app_new.py (copie de test)

### Agent Scanner
- [ ] Tester endpoints curl (Binance, CoinGecko)
- [ ] Mesurer latence (P95 < 300ms)
- [ ] Valider rate limits (30 req/min CoinGecko, illimité Binance)
- [ ] Documenter réponses format

### Agent Debugger (Phase 2)
- [ ] Lancer tests unitaires
- [ ] Vérifier circuit breakers
- [ ] Tester fallbacks
- [ ] Valider cache TTL

## Prochaines étapes

**Phase 1b (une fois local validé):**
- Créer app_new.py (copie de app.py)
- Remplacer endpoints dans app_new.py pour utiliser api_manager
- Tester en local: `python app_new.py`

**Phase 2 (optionnel, fallbacks):**
- Ajouter CoinMarketCap fallback pour prix
- Ajouter Glassnode fallback pour on-chain
- Tester circuit breakers

**Phase 3+ (après validation locale complet):**
- Créer tests de charge (100+ users)
- Déployer sur Hetzner (backup ancien app.py d'abord!)

## Notes

- Tous les APIs testés en gratuit (aucune clé requise)
- CoinGecko: 30 req/min = ~1800 req/jour (suffisant)
- Binance: illimité (parfait)
- Circuit breaker: retry après 60s si API down
- Cache: prix 30s, OHLC 1h, sentiment 24h
- Rate limiter: max 100 req/min globales

## Logs

Tous les appels API loggés dans:
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"CoinGecko price fetch: {len(data)} coins")
```

Enable logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```
