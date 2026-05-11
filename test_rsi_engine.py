#!/usr/bin/env python3
"""
Test suite for RSI Engine
Tests: cache, RSI bounds, top50 symbols fetch, build_rsi_heatmap_data orchestration
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from rsi_engine import (
    RSIHeatmapCache,
    get_top50_symbols,
    fetch_coinglass_rsi,
    calculate_rsi_from_binance,
    build_rsi_heatmap_data,
    clear_rsi_cache,
    _cache
)


class TestRSIHeatmapCache:
    """Test cache TTL and basic operations"""

    def test_cache_set_and_get(self):
        """Test setting and retrieving from cache"""
        cache = RSIHeatmapCache(ttl_seconds=300)
        cache.set("key1", {"value": "data"})
        assert cache.get("key1") == {"value": "data"}

    def test_cache_ttl_expiration(self):
        """Test cache expires after TTL"""
        cache = RSIHeatmapCache(ttl_seconds=1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_clear_specific_key(self):
        """Test clearing a specific cache key"""
        cache = RSIHeatmapCache(ttl_seconds=300)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear("key1")
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_cache_clear_all(self):
        """Test clearing entire cache"""
        cache = RSIHeatmapCache(ttl_seconds=300)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_cache_miss_nonexistent_key(self):
        """Test getting non-existent key returns None"""
        cache = RSIHeatmapCache(ttl_seconds=300)
        assert cache.get("nonexistent") is None


class TestGetTop50Symbols:
    """Test top 50 symbols fetching"""

    @patch('rsi_engine._session.get')
    def test_get_top50_symbols_success(self, mock_get):
        """Test successful CoinGecko API call"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'symbol': 'btc', 'market_cap': 1000000},
            {'symbol': 'eth', 'market_cap': 500000},
            {'symbol': 'bnb', 'market_cap': 300000},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        symbols = get_top50_symbols()

        assert 'BTC' in symbols
        assert 'ETH' in symbols
        assert 'BNB' in symbols
        assert all(isinstance(s, str) for s in symbols)

    @patch('rsi_engine._session.get')
    def test_get_top50_symbols_fallback_on_failure(self, mock_get):
        """Test fallback to hardcoded list when API fails"""
        mock_get.side_effect = Exception("API error")

        symbols = get_top50_symbols()

        # Should return hardcoded fallback
        assert len(symbols) > 0
        assert isinstance(symbols, list)
        assert all(isinstance(s, str) for s in symbols)
        # Check some expected ones in fallback
        assert 'BTC' in symbols
        assert 'ETH' in symbols


class TestFetchCoinglassRSI:
    """Test CoinGlass RSI fetching"""

    @patch('rsi_engine._session.get')
    def test_fetch_coinglass_rsi_success(self, mock_get):
        """Test successful CoinGlass API response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'rsi': 65.5,
                'updateTime': 1234567890
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_coinglass_rsi('BTC', '7d')

        assert result is not None
        assert result['symbol'] == 'BTC'
        assert result['rsi'] == 65.5
        assert result['source'] == 'coinglass'
        assert 0 <= result['rsi'] <= 100

    @patch('rsi_engine._session.get')
    def test_fetch_coinglass_rsi_invalid_response(self, mock_get):
        """Test handling invalid CoinGlass response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'success': False}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_coinglass_rsi('BTC', '7d')
        assert result is None

    @patch('rsi_engine._session.get')
    def test_fetch_coinglass_rsi_api_failure(self, mock_get):
        """Test CoinGlass API timeout/failure"""
        mock_get.side_effect = Exception("Request timeout")

        result = fetch_coinglass_rsi('BTC', '7d')
        assert result is None


class TestCalculateRSIFromBinance:
    """Test RSI calculation from Binance klines"""

    @patch('rsi_engine._session.get')
    def test_calculate_rsi_from_binance_success(self, mock_get):
        """Test RSI calculation with valid klines data"""
        # Create mock klines with prices: 100, 101, 102, 103, ..., 120
        mock_klines = [
            [0, 0, 0, 0, str(100 + i), 0, 0, 0, 0, 0, 0, 0]
            for i in range(20)
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = mock_klines
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        rsi = calculate_rsi_from_binance('BTC', '1w', period=14)

        assert rsi is not None
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    @patch('rsi_engine._session.get')
    def test_calculate_rsi_from_binance_insufficient_data(self, mock_get):
        """Test with insufficient kline data"""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            [0, 0, 0, 0, str(100), 0, 0, 0, 0, 0, 0, 0]
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        rsi = calculate_rsi_from_binance('BTC', '1w', period=14)
        assert rsi is None

    @patch('rsi_engine._session.get')
    def test_calculate_rsi_bounds(self, mock_get):
        """Test RSI bounds (0-100)"""
        # All gains scenario
        mock_klines = [
            [0, 0, 0, 0, str(100 + i), 0, 0, 0, 0, 0, 0, 0]
            for i in range(20)
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_klines
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        rsi = calculate_rsi_from_binance('BTC', '1w', period=14)
        assert 0 <= rsi <= 100

    @patch('rsi_engine._session.get')
    def test_calculate_rsi_from_binance_api_failure(self, mock_get):
        """Test API failure handling"""
        mock_get.side_effect = Exception("Network error")

        rsi = calculate_rsi_from_binance('BTC', '1w')
        assert rsi is None


class TestBuildRSIHeatmapData:
    """Test main orchestrator function"""

    def test_build_rsi_heatmap_data_cache_hit(self):
        """Test cache hit on second call"""
        # Clear cache first
        clear_rsi_cache('rsi_heatmap_1w')

        with patch('rsi_engine.get_top50_symbols') as mock_top50:
            with patch('rsi_engine.fetch_coinglass_rsi') as mock_cg:
                mock_top50.return_value = ['BTC', 'ETH']
                mock_cg.return_value = {'symbol': 'BTC', 'rsi': 65.0, 'timestamp': int(time.time()), 'source': 'coinglass'}

                # First call - should fetch
                data1 = build_rsi_heatmap_data('1w')
                call_count_first = mock_top50.call_count

                # Second call - should hit cache
                data2 = build_rsi_heatmap_data('1w')
                call_count_second = mock_top50.call_count

                assert call_count_first == call_count_second  # No new calls
                assert data1 == data2

    @patch('rsi_engine.get_top50_symbols')
    @patch('rsi_engine.fetch_coinglass_rsi')
    @patch('rsi_engine.calculate_rsi_from_binance')
    def test_build_rsi_heatmap_data_with_fallback(self, mock_binance, mock_cg, mock_top50):
        """Test fallback to Binance when CoinGlass fails"""
        clear_rsi_cache('rsi_heatmap_1w')

        mock_top50.return_value = ['BTC', 'ETH']
        mock_cg.return_value = None  # CoinGlass fails
        mock_binance.return_value = 65.0  # Binance fallback succeeds

        data = build_rsi_heatmap_data('1w')

        assert len(data) > 0
        assert all('rsi_1w' in item for item in data)
        assert all(0 <= item['rsi_1w'] <= 100 for item in data)

    @patch('rsi_engine.get_top50_symbols')
    @patch('rsi_engine.fetch_coinglass_rsi')
    @patch('rsi_engine.calculate_rsi_from_binance')
    def test_build_rsi_heatmap_data_structure(self, mock_binance, mock_cg, mock_top50):
        """Test output structure"""
        clear_rsi_cache('rsi_heatmap_1w')

        mock_top50.return_value = ['BTC', 'ETH']
        mock_cg.return_value = {
            'symbol': 'BTC',
            'rsi': 65.0,
            'timestamp': int(time.time()),
            'source': 'coinglass'
        }
        mock_binance.return_value = 55.0

        data = build_rsi_heatmap_data('1w')

        assert isinstance(data, list)
        assert len(data) > 0

        for item in data:
            assert 'symbol' in item
            assert 'rsi_1w' in item or 'rsi_1m' in item
            assert 'timestamp' in item
            assert 'state' in item
            assert 'source' in item
            assert item['state'] in ['oversold', 'overbought', 'neutral']

    @patch('rsi_engine.get_top50_symbols')
    @patch('rsi_engine.fetch_coinglass_rsi')
    def test_build_rsi_heatmap_data_state_classification(self, mock_cg, mock_top50):
        """Test RSI state classification"""
        clear_rsi_cache('rsi_heatmap_1w')

        mock_top50.return_value = ['BTC', 'ETH', 'BNB']

        def rsi_values(symbol, timeframe):
            rsi_map = {'BTC': 25.0, 'ETH': 65.0, 'BNB': 75.0}
            return {
                'symbol': symbol,
                'rsi': rsi_map.get(symbol, 50.0),
                'timestamp': int(time.time()),
                'source': 'coinglass'
            }

        mock_cg.side_effect = rsi_values

        data = build_rsi_heatmap_data('1w')
        states = {item['symbol']: item['state'] for item in data}

        assert states['BTC'] == 'oversold'  # RSI 25 < 30
        assert states['ETH'] == 'neutral'   # RSI 65 is neutral
        assert states['BNB'] == 'overbought'  # RSI 75 > 70

    @patch('rsi_engine.get_top50_symbols')
    @patch('rsi_engine.fetch_coinglass_rsi')
    def test_build_rsi_heatmap_data_1m_timeframe(self, mock_cg, mock_top50):
        """Test 1-month timeframe"""
        clear_rsi_cache('rsi_heatmap_1m')

        mock_top50.return_value = ['BTC']
        mock_cg.return_value = {
            'symbol': 'BTC',
            'rsi': 55.0,
            'timestamp': int(time.time()),
            'source': 'coinglass'
        }

        data = build_rsi_heatmap_data('1m')

        assert len(data) == 1
        assert 'rsi_1m' in data[0]
        assert data[0]['rsi_1m'] == 55.0


class TestRSIBoundsAndValidation:
    """Test RSI value bounds and validation"""

    @patch('rsi_engine.get_top50_symbols')
    @patch('rsi_engine.fetch_coinglass_rsi')
    def test_all_rsi_values_in_bounds(self, mock_cg, mock_top50):
        """Test all returned RSI values are between 0-100"""
        clear_rsi_cache('rsi_heatmap_1w')

        mock_top50.return_value = ['BTC', 'ETH', 'BNB', 'XRP', 'SOL']

        rsi_values = [15.0, 35.0, 50.0, 70.0, 95.0]
        call_count = [0]

        def mock_rsi(symbol, timeframe):
            val = rsi_values[call_count[0] % len(rsi_values)]
            call_count[0] += 1
            return {
                'symbol': symbol,
                'rsi': val,
                'timestamp': int(time.time()),
                'source': 'coinglass'
            }

        mock_cg.side_effect = mock_rsi

        data = build_rsi_heatmap_data('1w')

        for item in data:
            rsi = item.get('rsi_1w', item.get('rsi_1m'))
            assert 0 <= rsi <= 100, f"RSI {rsi} out of bounds for {item['symbol']}"


class TestClearRSICache:
    """Test cache clearing utility"""

    def test_clear_specific_cache_key(self):
        """Test clearing specific cache key"""
        clear_rsi_cache('rsi_heatmap_1w')
        _cache.set('rsi_heatmap_1w', [])

        clear_rsi_cache('rsi_heatmap_1w')
        assert _cache.get('rsi_heatmap_1w') is None

    def test_clear_all_cache(self):
        """Test clearing entire cache"""
        _cache.set('rsi_heatmap_1w', [])
        _cache.set('rsi_heatmap_1m', [])

        clear_rsi_cache()

        assert _cache.get('rsi_heatmap_1w') is None
        assert _cache.get('rsi_heatmap_1m') is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
