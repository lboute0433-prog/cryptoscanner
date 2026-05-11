#!/usr/bin/env python3
"""
RSI Heatmap Engine — CoinGlass RSI Data + Binance Fallback
Fetches RSI indicators for top 50 cryptos with memory cache (5-minute TTL)
"""

import requests
import time
from datetime import datetime
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# ── Session Configuration ─────────────────────────────────────
def _create_session():
    """Create requests session with retry strategy"""
    session = requests.Session()

    # Retry strategy: 2 retries, wait 1s between attempts
    # Retry on: 429 (rate limit), 500, 502, 503, 504
    retry_strategy = Retry(
        total=2,
        status_forcelist=[429, 500, 502, 503, 504],
        backoff_factor=1
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Add User-Agent header for API compatibility
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    return session

_session = _create_session()

# ── Global Cache Configuration ────────────────────────────────
class RSIHeatmapCache:
    """Memory cache with TTL support for RSI data"""

    def __init__(self, ttl_seconds=300):
        self.ttl_seconds = ttl_seconds
        self.data = {}
        self.timestamps = {}

    def get(self, key):
        """Get value from cache if not expired"""
        if key not in self.data:
            return None

        # Check TTL
        age = time.time() - self.timestamps[key]
        if age > self.ttl_seconds:
            del self.data[key]
            del self.timestamps[key]
            return None

        return self.data[key]

    def set(self, key, value):
        """Set value in cache with timestamp"""
        self.data[key] = value
        self.timestamps[key] = time.time()

    def clear(self, key=None):
        """Clear specific key or entire cache"""
        if key is None:
            self.data.clear()
            self.timestamps.clear()
        else:
            if key in self.data:
                del self.data[key]
            if key in self.timestamps:
                del self.timestamps[key]

# Global cache instance
_cache = RSIHeatmapCache(ttl_seconds=300)


# ── API Functions ──────────────────────────────────────────────
def get_top50_symbols():
    """
    Fetch top 50 cryptocurrencies by market cap from CoinGecko
    Returns: list of symbols (uppercase) e.g. ['BTC', 'ETH', ...]
    Fallback: hardcoded top 20 if API fails
    """
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "sparkline": False
        }

        response = _session.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        symbols = [coin['symbol'].upper() for coin in data]
        print(f"[RSI] Fetched {len(symbols)} symbols from CoinGecko")
        return symbols

    except Exception as e:
        print(f"[RSI] CoinGecko API failed: {e}, using fallback")
        # Hardcoded top 20 fallback
        return [
            'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'SUI', 'LINK',
            'NEAR', 'UNI', 'AAVE', 'ARB', 'OP', 'MNT', 'JTO', 'USDC', 'USDT', 'DAI'
        ]


def fetch_coinglass_rsi(symbol, timeframe='7d'):
    """
    Fetch RSI from CoinGlass API

    Args:
        symbol: e.g. 'BTC'
        timeframe: '7d' for 1 week, '30d' for 1 month

    Returns:
        dict: {'symbol': str, 'rsi': float, 'timestamp': int, 'source': 'coinglass'}
        or None if API fails
    """
    try:
        url = "https://open-api.coinglass.com/public/v2/indicators/kline_rsi"

        # Map timeframe to CoinGlass format
        timeframe_map = {
            '7d': '7',    # 1w
            '30d': '30',  # 1m
            '1w': '7',
            '1m': '30'
        }
        cg_timeframe = timeframe_map.get(timeframe, '7')

        params = {
            "pair": f"{symbol}USDT",
            "timeframe": cg_timeframe
        }

        response = _session.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        # Validate response structure
        if not data.get("success") or not data.get("data"):
            return None

        rsi_data = data.get("data", {})
        rsi_value = rsi_data.get("rsi")

        if rsi_value is None:
            return None

        return {
            'symbol': symbol,
            'rsi': float(rsi_value),
            'timestamp': int(time.time()),
            'source': 'coinglass'
        }

    except Exception as e:
        print(f"[RSI] CoinGlass failed for {symbol}: {e}")
        return None


def calculate_rsi_from_binance(symbol, interval='1w', period=14):
    """
    Calculate RSI from Binance Klines (fallback method)

    Args:
        symbol: e.g. 'BTC'
        interval: '1w' for weekly, '1M' for monthly
        period: RSI period (default 14)

    Returns:
        float: RSI value (0-100) or None if fails
    """
    try:
        url = "https://api.binance.com/api/v3/klines"

        # Ensure interval format matches Binance expectations
        binance_interval = '1w' if interval == '1w' else '1M'

        params = {
            "symbol": f"{symbol}USDT",
            "interval": binance_interval,
            "limit": period + 5
        }

        response = _session.get(url, params=params, timeout=8)
        response.raise_for_status()
        klines = response.json()

        if not klines or len(klines) < period:
            return None

        # Extract close prices
        closes = [float(kline[4]) for kline in klines]

        # Calculate deltas
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]

        # Separate gains and losses
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        # Calculate averages over period
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        # Calculate RS and RSI
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    except Exception as e:
        print(f"[RSI] Binance fallback failed for {symbol}: {e}")
        return None


# ── Main Orchestrator ──────────────────────────────────────────
def build_rsi_heatmap_data(timeframe='1w'):
    """
    Main function to build RSI heatmap data for top 50 cryptos

    Args:
        timeframe: '1w' or '1m'

    Returns:
        list: [{'symbol': str, 'rsi_1w'|'rsi_1m': float, 'timestamp': int, 'state': str}, ...]
    """
    cache_key = f"rsi_heatmap_{timeframe}"

    # Check cache first
    cached = _cache.get(cache_key)
    if cached is not None:
        print(f"[RSI] Cache hit for {timeframe}")
        return cached

    print(f"[RSI] Building heatmap for {timeframe}...")

    # Get top 50 symbols
    symbols = get_top50_symbols()

    result = []
    successful = 0

    # Fetch RSI for each symbol
    for symbol in symbols:
        try:
            # Try CoinGlass first
            rsi_data = fetch_coinglass_rsi(symbol, timeframe)

            # Fallback to Binance if CoinGlass fails
            if rsi_data is None:
                rsi_value = calculate_rsi_from_binance(symbol, timeframe)
                if rsi_value is not None:
                    rsi_data = {
                        'symbol': symbol,
                        'rsi': rsi_value,
                        'timestamp': int(time.time()),
                        'source': 'binance'
                    }

            # Determine state based on RSI
            if rsi_data is not None:
                rsi = rsi_data['rsi']
                if rsi < 30:
                    state = "oversold"
                elif rsi > 70:
                    state = "overbought"
                else:
                    state = "neutral"

                # Build response dict with dynamic RSI key
                rsi_key = f"rsi_{'1w' if timeframe in ['7d', '1w'] else '1m'}"

                result.append({
                    'symbol': symbol,
                    rsi_key: rsi,
                    'timestamp': rsi_data['timestamp'],
                    'state': state,
                    'source': rsi_data['source']
                })
                successful += 1

        except Exception as e:
            print(f"[RSI] Error processing {symbol}: {e}")
            continue

    print(f"[RSI] Built {successful} / {len(symbols)} coins for {timeframe}")

    # Cache result
    _cache.set(cache_key, result)

    return result


# ── Utility Functions ──────────────────────────────────────────
def init_rsi_db():
    """Initialize RSI database (placeholder for future DB setup)"""
    print("[RSI] Database initialization (not required for cache-based RSI)")


def clear_rsi_cache(key=None):
    """
    Clear RSI cache

    Args:
        key: specific cache key to clear, or None to clear all
    """
    if key is None:
        _cache.clear()
        print("[RSI] All cache cleared")
    else:
        _cache.clear(key)
        print(f"[RSI] Cache cleared for {key}")


# ── Module test ────────────────────────────────────────────────
if __name__ == "__main__":
    # Test basic functionality
    print("Testing RSI Engine...")

    # Test 1-week RSI
    data_1w = build_rsi_heatmap_data('1w')
    print(f"✓ Got {len(data_1w)} coins for 1w")

    if data_1w:
        print(f"  Sample: {data_1w[0]}")

    # Test 1-month RSI
    data_1m = build_rsi_heatmap_data('1m')
    print(f"✓ Got {len(data_1m)} coins for 1m")

    # Test cache (should be fast)
    start = time.time()
    data_cached = build_rsi_heatmap_data('1w')
    elapsed = time.time() - start
    print(f"✓ Cache hit: {elapsed:.3f}s for {len(data_cached)} coins")

    print("\n✅ RSI Engine tests passed!")
