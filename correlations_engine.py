"""
Correlations Engine — Analyze cross-asset correlations in real-time.
Uses Binance historical price data (no API key needed).
"""
import requests
from datetime import datetime, timedelta
import numpy as np

BINANCE_API = "https://api.binance.com"
API_TIMEOUT = 5

# Top crypto assets to monitor
TOP_ASSETS = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA', 'DOGE', 'XRP', 'AVAX', 'LINK']

def get_price_history(symbol='BTC', interval='1h', limit=24):
    """
    Get 24h price history for a symbol from Binance.

    Args:
        symbol: Trading pair (e.g., 'BTC')
        interval: Kline interval ('1h', '4h', '1d')
        limit: Number of candles (default 24 = 24 hours)

    Returns:
        List of closing prices
    """
    try:
        trading_pair = f"{symbol}USDT"
        resp = requests.get(
            f"{BINANCE_API}/api/v3/klines",
            params={'symbol': trading_pair, 'interval': interval, 'limit': limit},
            timeout=API_TIMEOUT
        )

        if resp.status_code != 200:
            return []

        data = resp.json()
        # Close price is index 4 in kline data
        prices = [float(kline[4]) for kline in data]
        return prices
    except Exception as e:
        print(f"[Correlations] Error fetching {symbol}: {e}")
        return []


def calculate_correlation_matrix(symbols=None, period_hours=24):
    """
    Calculate correlation matrix for top assets.

    Args:
        symbols: List of symbols to correlate (default: TOP_ASSETS)
        period_hours: Historical period (24h recommended)

    Returns:
        {
            'correlation_matrix': [[1.0, 0.85, ...], ...],
            'symbols': ['BTC', 'ETH', ...],
            'period_hours': 24,
            'timestamp': '2026-05-05T14:30:00',
            'pairs': [
                {'symbol1': 'BTC', 'symbol2': 'ETH', 'correlation': 0.85},
                ...
            ]
        }
    """
    if symbols is None:
        symbols = TOP_ASSETS

    # Fetch price history for all symbols
    price_histories = {}
    for symbol in symbols:
        prices = get_price_history(symbol, interval='1h', limit=period_hours)
        if prices and len(prices) > 1:
            price_histories[symbol] = prices

    if len(price_histories) < 2:
        return _fallback_correlations(symbols)

    # Calculate returns (percentage changes)
    returns = {}
    for symbol, prices in price_histories.items():
        # Calculate hourly returns: (price[t] - price[t-1]) / price[t-1]
        sym_returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                sym_returns.append(ret)
        returns[symbol] = sym_returns

    # Align all returns to same length
    min_len = min(len(ret_list) for ret_list in returns.values())
    aligned_returns = {sym: ret_list[-min_len:] for sym, ret_list in returns.items()}

    # Build correlation matrix
    symbols_list = list(aligned_returns.keys())
    n = len(symbols_list)
    corr_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if i == j:
                corr_matrix[i][j] = 1.0
            else:
                returns_i = np.array(aligned_returns[symbols_list[i]])
                returns_j = np.array(aligned_returns[symbols_list[j]])

                # Pearson correlation coefficient
                if len(returns_i) > 1 and len(returns_j) > 1:
                    corr = np.corrcoef(returns_i, returns_j)[0, 1]
                    corr_matrix[i][j] = corr if not np.isnan(corr) else 0.0
                else:
                    corr_matrix[i][j] = 0.0

    # Extract high correlations (> 0.7 strong, < -0.5 inverse)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            corr_val = corr_matrix[i][j]
            if abs(corr_val) > 0.5:  # Strong correlation
                pairs.append({
                    'symbol1': symbols_list[i],
                    'symbol2': symbols_list[j],
                    'correlation': round(corr_val, 3),
                    'strength': 'strong' if abs(corr_val) > 0.7 else 'moderate',
                    'type': 'positive' if corr_val > 0 else 'negative'
                })

    # Sort by absolute correlation strength
    pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)

    return {
        'correlation_matrix': corr_matrix.tolist(),
        'symbols': symbols_list,
        'period_hours': period_hours,
        'timestamp': datetime.now().isoformat(),
        'strong_correlations': pairs[:10],  # Top 10 correlations
        'total_correlations': len(pairs)
    }


def get_asset_clusters(symbols=None):
    """
    Group assets into correlation clusters.
    Assets in same cluster move together.

    Returns:
        {
            'clusters': [
                {'leader': 'BTC', 'members': ['BTC', 'ETH', 'LINK'], 'strength': 0.82},
                ...
            ],
            'ungrouped': ['DOGE'],
            'timestamp': '2026-05-05T14:30:00'
        }
    """
    if symbols is None:
        symbols = TOP_ASSETS

    corr_data = calculate_correlation_matrix(symbols)
    if 'error' in corr_data:
        return corr_data

    # Simple clustering: group by correlation strength > 0.7
    clusters = []
    used = set()

    correlations = corr_data.get('strong_correlations', [])

    for corr_pair in correlations:
        s1, s2 = corr_pair['symbol1'], corr_pair['symbol2']

        if s1 in used or s2 in used:
            continue

        if corr_pair['correlation'] > 0.7:
            clusters.append({
                'leader': s1,
                'members': [s1, s2],
                'strength': corr_pair['correlation'],
                'type': 'positive'
            })
            used.add(s1)
            used.add(s2)

    ungrouped = [s for s in corr_data['symbols'] if s not in used]

    return {
        'clusters': clusters,
        'ungrouped': ungrouped,
        'cluster_count': len(clusters),
        'timestamp': datetime.now().isoformat()
    }


def _fallback_correlations(symbols):
    """Fallback data when API unavailable."""
    return {
        'error': 'Data unavailable',
        'correlation_matrix': [],
        'symbols': symbols,
        'period_hours': 24,
        'timestamp': datetime.now().isoformat(),
        'strong_correlations': [],
        'total_correlations': 0
    }
