"""
Tests unitaires pour les APIs
À lancer: python -m pytest tests/test_apis.py
"""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock
import sys
from pathlib import Path

# Ajouter parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_coingecko import CoinGeckoAPI
from api_binance import BinanceAPI
from api_manager import APIManager, CircuitBreaker, RateLimiter, CacheManager


class TestCircuitBreaker:
    def test_circuit_breaker_initial_state(self):
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        assert not cb.is_open
        assert cb.can_attempt()

    def test_circuit_breaker_opens_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        for _ in range(3):
            cb.record_failure()
        assert cb.is_open
        assert not cb.can_attempt()

    def test_circuit_breaker_success_resets(self):
        cb = CircuitBreaker(failure_threshold=3, timeout=60)
        cb.record_failure()
        cb.record_success()
        assert not cb.is_open
        assert cb.failure_count == 0


class TestRateLimiter:
    def test_rate_limiter_allows_requests(self):
        rl = RateLimiter(max_requests=10, window_seconds=1)
        for _ in range(10):
            assert rl.can_request()
            rl.record_request()

    def test_rate_limiter_blocks_excess(self):
        rl = RateLimiter(max_requests=5, window_seconds=1)
        for _ in range(5):
            rl.record_request()
        assert not rl.can_request()


class TestCacheManager:
    def test_cache_set_and_get(self):
        cm = CacheManager()
        cm.set('key1', 'value1', ttl_seconds=10)
        assert cm.get('key1') == 'value1'

    def test_cache_expiry(self):
        cm = CacheManager()
        cm.set('key1', 'value1', ttl_seconds=0)  # Expire immediately
        import time
        time.sleep(0.1)
        assert cm.get('key1') is None


class TestCoinGeckoAPI:
    @pytest.mark.asyncio
    async def test_fetch_price_mock(self):
        """Test avec mock response"""
        api = CoinGeckoAPI()

        mock_response = {
            'bitcoin': {'usd': 42000},
            'ethereum': {'usd': 2200}
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )

            result = await api.fetch_price()
            assert 'bitcoin' in result
            assert result['bitcoin']['usd'] == 42000

    @pytest.mark.asyncio
    async def test_fetch_price_rate_limit(self):
        """Test rate limit error"""
        api = CoinGeckoAPI()

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 429

            with pytest.raises(Exception, match="rate limit"):
                await api.fetch_price()


class TestBinanceAPI:
    @pytest.mark.asyncio
    async def test_get_price_mock(self):
        """Test avec mock response"""
        api = BinanceAPI()

        mock_response = {
            'symbol': 'BTCUSDT',
            'price': '42000.00'
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )

            result = await api.get_price('BTCUSDT')
            assert result['symbol'] == 'BTCUSDT'
            assert result['price'] == '42000.00'

    @pytest.mark.asyncio
    async def test_get_orderbook_mock(self):
        """Test orderbook fetch"""
        api = BinanceAPI()

        mock_response = {
            'bids': [['42000.00', '1.5'], ['41999.00', '2.0']],
            'asks': [['42001.00', '1.0'], ['42002.00', '2.5']],
        }

        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )

            result = await api.get_orderbook('BTCUSDT')
            assert len(result['bids']) == 2
            assert len(result['asks']) == 2


class TestAPIManager:
    @pytest.mark.asyncio
    async def test_smart_fetch_with_cache(self):
        """Test cache hit"""
        manager = APIManager()
        manager.cache.set('price:None', {'bitcoin': {'usd': 42000}}, ttl_seconds=60)

        result = await manager.smart_fetch('price')
        # Should return cached value


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
