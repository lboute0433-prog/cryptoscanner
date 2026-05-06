"""
APIManager — Orchestrateur des APIs crypto
Gère fallbacks, caching, rate limiting, circuit breaking
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Circuit breaker pour éviter les appels répétés à une API down"""

    def __init__(self, failure_threshold=3, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False

    def record_success(self):
        self.failure_count = 0
        self.is_open = False

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True

    def can_attempt(self) -> bool:
        if not self.is_open:
            return True
        # Retry après timeout
        if time.time() - self.last_failure_time > self.timeout:
            self.is_open = False
            self.failure_count = 0
            return True
        return False


class RateLimiter:
    """Rate limiter pour éviter les bans"""

    def __init__(self, max_requests=100, window_seconds=60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_times = []

    def can_request(self) -> bool:
        now = time.time()
        # Nettoyer les requêtes hors de la fenêtre
        self.request_times = [t for t in self.request_times if now - t < self.window_seconds]
        return len(self.request_times) < self.max_requests

    def record_request(self):
        self.request_times.append(time.time())

    async def wait_if_needed(self):
        while not self.can_request():
            await asyncio.sleep(1)


class CacheManager:
    """Cache en mémoire avec TTL"""

    def __init__(self):
        self.cache = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None

        value, expiry = self.cache[key]
        if time.time() > expiry:
            del self.cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl_seconds: int):
        expiry = time.time() + ttl_seconds
        self.cache[key] = (value, expiry)

    def clear(self):
        self.cache.clear()


class APIManager:
    """Orchestrateur principal des APIs"""

    def __init__(self):
        self.cache = CacheManager()
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

        # Circuit breakers par API
        self.breakers = {
            'coingecko': CircuitBreaker(),
            'coinmarketcap': CircuitBreaker(),
            'binance': CircuitBreaker(),
            'arkham': CircuitBreaker(),
        }

        # Imports dynamiques (lazy loading)
        self.coingecko = None
        self.binance = None
        self.arkham = None

    async def _load_apis(self):
        """Charge les modules API au besoin"""
        if self.coingecko is None:
            from .api_coingecko import CoinGeckoAPI
            self.coingecko = CoinGeckoAPI()

        if self.binance is None:
            from .api_binance import BinanceAPI
            self.binance = BinanceAPI()

    async def smart_fetch(self, endpoint: str, params: Dict = None, **kwargs) -> Dict:
        """
        Fetch avec fallback automatique, caching, rate limiting

        Endpoints disponibles:
        - 'price': Prix BTC/ETH (CoinGecko → CoinMarketCap fallback)
        - 'others': Autres cryptos
        - 'whales': Mouvements whale
        - 'volume': Volume orderbook
        """

        await self._load_apis()
        await self.rate_limiter.wait_if_needed()

        # Chercher en cache d'abord
        cache_key = f"{endpoint}:{str(params)}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit: {endpoint}")
            return cached

        try:
            # Router vers les APIs
            if endpoint == 'price':
                result = await self._fetch_price(params)
            elif endpoint == 'others':
                result = await self._fetch_others(params)
            elif endpoint == 'whales':
                result = await self._fetch_whales(params)
            elif endpoint == 'volume':
                result = await self._fetch_volume(params)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")

            # Cacher le résultat
            ttl = kwargs.get('ttl', 60)
            self.cache.set(cache_key, result, ttl)
            self.rate_limiter.record_request()

            return result

        except Exception as e:
            logger.error(f"smart_fetch failed: {e}")
            raise

    async def _fetch_price(self, params: Dict) -> Dict:
        """Fetch prix — CoinGecko principal, CMC fallback"""

        if self.breakers['coingecko'].can_attempt():
            try:
                result = await self.coingecko.fetch_price(params or {})
                self.breakers['coingecko'].record_success()
                return result
            except Exception as e:
                logger.warning(f"CoinGecko failed: {e}, trying fallback...")
                self.breakers['coingecko'].record_failure()

        # Fallback
        logger.info("Using CoinMarketCap fallback for price")
        # TODO: Implémenter CoinMarketCap fallback
        raise Exception("All price APIs failed")

    async def _fetch_others(self, params: Dict) -> Dict:
        """Fetch autres cryptos"""
        return await self._fetch_price(params)

    async def _fetch_whales(self, params: Dict) -> Dict:
        """Fetch mouvements whales — Arkham principal"""

        if self.breakers['arkham'].can_attempt():
            try:
                result = await self.arkham.detect_whales(params or {})
                self.breakers['arkham'].record_success()
                return result
            except Exception as e:
                logger.warning(f"Arkham failed: {e}")
                self.breakers['arkham'].record_failure()

        # Fallback: vides (Arkham n'a pas de good fallback)
        logger.warning("Whales API unavailable")
        return {"whales": [], "status": "unavailable"}

    async def _fetch_volume(self, params: Dict) -> Dict:
        """Fetch volume orderbook — Binance"""

        if self.breakers['binance'].can_attempt():
            try:
                result = await self.binance.get_orderbook(params or {})
                self.breakers['binance'].record_success()
                return result
            except Exception as e:
                logger.warning(f"Binance failed: {e}")
                self.breakers['binance'].record_failure()

        raise Exception("Volume API failed")

    def get_status(self) -> Dict:
        """Status des APIs et breakers"""
        return {
            'breakers': {
                name: {
                    'is_open': breaker.is_open,
                    'failure_count': breaker.failure_count,
                }
                for name, breaker in self.breakers.items()
            },
            'cache_size': len(self.cache.cache),
            'timestamp': datetime.utcnow().isoformat(),
        }


# Instance globale
manager = APIManager()
