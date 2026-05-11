"""
RSI Heatmap Engine for CryptoScanner Pro
Fetches RSI data for top 50 cryptocurrencies from CoinGlass API with Binance fallback
"""

import requests
import time
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Session with retry strategy
session = requests.Session()
retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
session.mount('http://', adapter)

# Add User-Agent header for API compatibility
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

_cache_ttl = 300  # 5 minutes


class RSIHeatmapCache:
    """Memory cache with TTL support for RSI heatmap data"""

    def __init__(self, ttl_seconds=300):
        self.data = {}
        self.timestamps = {}
        self.ttl = ttl_seconds

    def get(self, key):
        """Get cached value if not expired"""
        if key in self.data:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.data[key]
            else:
                del self.data[key]
                del self.timestamps[key]
        return None

    def set(self, key, value):
        """Store value with timestamp"""
        self.data[key] = value
        self.timestamps[key] = time.time()

    def clear(self, key=None):
        """Clear single key or entire cache"""
        if key:
            self.data.pop(key, None)
            self.timestamps.pop(key, None)
        else:
            self.data.clear()
            self.timestamps.clear()


# Global cache instance
cache = RSIHeatmapCache(ttl_seconds=300)


def get_top50_symbols():
    """
    Get top 50 cryptocurrencies by market cap from CoinGecko.
    Returns: ['BTC', 'ETH', 'BNB', ...]
    """
    try:
        r = session.get(
            "https://api.coingecko.com/api/v3/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 50,
                "page": 1
            },
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        if r.status_code == 200:
            data = r.json()
            return [coin['symbol'].upper() for coin in data if coin.get('symbol')]
    except Exception as e:
        print(f"[RSI] get_top50_symbols error: {e}")

    # Fallback: hardcoded top 20 (always available)
    return ['BTC', 'ETH', 'BNB', 'XRP', 'SOL', 'DOGE', 'ADA', 'AVAX', 'LINK', 'MATIC',
            'WBTC', 'ARB', 'OP', 'LTC', 'UNI', 'SUI', 'ATOM', 'BCH', 'DOT', 'PEPE']


def fetch_coinglass_rsi(symbol, timeframe='7d'):
    """
    Fetch RSI directly from CoinGlass API.

    Args:
        symbol: 'BTC', 'ETH', etc.
        timeframe: '7d' (1W) or '30d' (1M)

    Returns:
        {'rsi': 65.2, 'timestamp': '2026-05-11T...', ...} or None
    """
    try:
        pair = f"{symbol}USDT"

        # Map timeframe
        cg_timeframe = '7' if timeframe == '1w' else '30' if timeframe == '1m' else '7'

        r = session.get(
            "https://open-api.coinglass.com/public/v2/indicators/kline_rsi",
            params={
                "pair": pair,
                "timeframe": cg_timeframe
            },
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        data = r.json()
        if data.get("success") and data.get("data"):
            rsi_data = data["data"]
            return {
                'symbol': symbol,
                'rsi': rsi_data.get('rsi', None),
                'timestamp': rsi_data.get('updateTime'),
                'source': 'coinglass'
            }
    except Exception as e:
        print(f"[RSI] CoinGlass error for {symbol}: {e}")

    return None


def calculate_rsi_from_binance(symbol, interval='1w', period=14):
    """
    Calculate RSI from Binance klines (fallback if CoinGlass fails).

    Args:
        symbol: 'BTC', 'ETH', etc.
        interval: '1w' or '1M'
        period: RSI period (default 14)

    Returns:
        rsi_value (float) or None
    """
    try:
        # Map interval to Binance format
        binance_interval = '1w' if interval == '1w' else '1M'

        r = session.get(
            f"https://api.binance.com/api/v3/klines",
            params={
                "symbol": f"{symbol}USDT",
                "interval": binance_interval,
                "limit": period + 5
            },
            timeout=8
        )

        if r.status_code != 200:
            return None

        klines = r.json()
        closes = [float(k[4]) for k in klines]  # closing price

        # RSI calculation
        if len(closes) < period + 1:
            return None

        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 1)

    except Exception as e:
        print(f"[RSI] Binance calc error for {symbol}: {e}")
        return None


def build_rsi_heatmap_data(timeframe='1w'):
    """
    Main function: Build RSI heatmap for top 50 coins.

    Returns:
        [
            {'symbol': 'BTC', 'rsi_1w': 65.2, 'rsi_1m': 58.5, ...},
            ...
        ]
    """
    cache_key = f"rsi_heatmap_{timeframe}"
    cached = cache.get(cache_key)
    if cached:
        print(f"[RSI] Cache hit for {cache_key}")
        return cached

    print(f"[RSI] Building heatmap for {timeframe}...")
    symbols = get_top50_symbols()
    result = []

    for symbol in symbols:
        try:
            # Try CoinGlass first
            rsi_data = fetch_coinglass_rsi(symbol, timeframe)

            if rsi_data and rsi_data.get('rsi') is not None:
                result.append({
                    'symbol': symbol,
                    f'rsi_{timeframe[:2]}': round(rsi_data['rsi'], 1),
                    'timestamp': rsi_data.get('timestamp', ''),
                    'state': 'success'
                })
            else:
                # Fallback to Binance
                rsi_val = calculate_rsi_from_binance(symbol, timeframe)
                if rsi_val is not None:
                    result.append({
                        'symbol': symbol,
                        f'rsi_{timeframe[:2]}': rsi_val,
                        'timestamp': datetime.now().isoformat(),
                        'state': 'fallback'
                    })
        except Exception as e:
            print(f"[RSI] Error building for {symbol}: {e}")
            continue

    # Cache result
    cache.set(cache_key, result)

    print(f"[RSI] Built {len(result)} / {len(symbols)} coins for {timeframe}")
    return result


def build_scatter_plot_data():
    """
    Build data for scatter plot: RSI 1W vs RSI 1M for all coins.
    Uses cached data first, then Binance API if cache is empty.

    Returns:
        [
            {'symbol': 'BTC', 'rsi_1w': 65.2, 'rsi_1m': 58.5, 'zone': 'overbought'},
            ...
        ]
    """
    cache_key = "rsi_scatter_plot"
    cached = cache.get(cache_key)
    if cached:
        print("[RSI] Cache hit for scatter plot")
        return cached

    print("[RSI] Building scatter plot...")

    # Get RSI 1W and 1M from cache first
    rsi_1w_data = cache.get("rsi_heatmap_1w")
    rsi_1m_data = cache.get("rsi_heatmap_1m")

    # If cache is empty, calculate from Binance directly (reliable fallback)
    if not rsi_1w_data or not rsi_1m_data:
        print("[RSI] Cache empty - calculating from Binance API...")
        symbols = get_top50_symbols()
        rsi_1w_data = []
        rsi_1m_data = []

        for symbol in symbols:
            try:
                # Calculate RSI 1W
                rsi_1w = calculate_rsi_from_binance(symbol, '1w')
                if rsi_1w is not None:
                    rsi_1w_data.append({
                        'symbol': symbol,
                        'rsi_1w': rsi_1w,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'binance'
                    })

                # Calculate RSI 1M
                rsi_1m = calculate_rsi_from_binance(symbol, '1M')
                if rsi_1m is not None:
                    rsi_1m_data.append({
                        'symbol': symbol,
                        'rsi_1m': rsi_1m,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'binance'
                    })
            except Exception as e:
                print(f"[RSI] Error calculating for {symbol}: {e}")
                continue

        print(f"[RSI] Calculated {len(rsi_1w_data)} coins from Binance")

    # Map data by symbol
    rsi_1w_map = {c['symbol']: c.get('rsi_1w') for c in rsi_1w_data}
    rsi_1m_map = {c['symbol']: c.get('rsi_1m') for c in rsi_1m_data}

    result = []
    for symbol in rsi_1w_map.keys():
        rsi_1w_val = rsi_1w_map.get(symbol)
        rsi_1m_val = rsi_1m_map.get(symbol)

        if rsi_1w_val is None or rsi_1m_val is None:
            continue

        # Determine zone based on RSI values
        zone = 'neutral'
        if rsi_1w_val > 70 or rsi_1m_val > 70:
            zone = 'overbought'
        elif rsi_1w_val < 30 or rsi_1m_val < 30:
            zone = 'oversold'
        elif 60 <= rsi_1w_val <= 70 or 60 <= rsi_1m_val <= 70:
            zone = 'strong'
        elif 30 <= rsi_1w_val <= 40 or 30 <= rsi_1m_val <= 40:
            zone = 'weak'

        result.append({
            'symbol': symbol,
            'rsi_1w': float(rsi_1w_val),
            'rsi_1m': float(rsi_1m_val),
            'zone': zone,
            'timestamp': datetime.now().isoformat()
        })

    # Cache result
    cache.set(cache_key, result)

    print(f"[RSI] Built scatter plot with {len(result)} coins")
    return result


def init_rsi_db():
    """Initialize RSI engine"""
    print("[RSI] Engine initialized")


def clear_rsi_cache(key=None):
    """Manually clear RSI cache"""
    cache.clear(key)
    print(f"[RSI] Cache cleared: {key or 'all'}")
