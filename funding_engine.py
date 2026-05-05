"""
Funding Rate Engine — Track perpetual funding rates from Binance.
Indicates market sentiment (positive = bulls paying, negative = bears paying).
"""
import requests
from datetime import datetime
from functools import lru_cache

BINANCE_API = "https://fapi.binance.com"
API_TIMEOUT = 3
TOP_SYMBOLS = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'ARB']

@lru_cache(maxsize=1)
def get_funding_rates(limit=20):
    """
    Get current funding rates for top perpetual contracts.

    Returns:
        [
            {
                'symbol': 'BTC',
                'funding_rate': 0.00085,
                'funding_rate_pct': 0.085,
                'next_funding': 1234567890,
                'timestamp': '2026-05-05T13:24:00',
                'urgency': 'CRITICAL|HIGH|NORMAL'
            },
            ...
        ]
    """
    try:
        rates = []

        for symbol in TOP_SYMBOLS[:limit]:
            trading_pair = f"{symbol}USDT"

            try:
                # Get current funding rate
                url = f"{BINANCE_API}/fapi/v1/fundingRate"
                resp = requests.get(url, params={'symbol': trading_pair, 'limit': 1}, timeout=API_TIMEOUT)

                if resp.status_code != 200:
                    continue

                data_list = resp.json()
                if not data_list or len(data_list) == 0:
                    continue

                # Get latest entry (fundingRate returns array)
                data = data_list[0] if isinstance(data_list, list) else data_list

                # Get next funding time from premium index
                mark_url = f"{BINANCE_API}/fapi/v1/premiumIndex"
                mark_resp = requests.get(mark_url, params={'symbol': trading_pair}, timeout=API_TIMEOUT)
                mark_data = mark_resp.json() if mark_resp.status_code == 200 else {}

                funding_rate = float(data.get('fundingRate', 0))
                next_funding = int(mark_data.get('nextFundingTime', 0))

                # Determine urgency level
                abs_rate = abs(funding_rate)
                if abs_rate > 0.0025:
                    urgency = 'CRITICAL'
                elif abs_rate > 0.0015:
                    urgency = 'HIGH'
                else:
                    urgency = 'NORMAL'

                rates.append({
                    'symbol': symbol,
                    'funding_rate': funding_rate,
                    'funding_rate_pct': funding_rate * 100,
                    'next_funding': next_funding,
                    'timestamp': datetime.now().isoformat(),
                    'urgency': urgency
                })
            except Exception as e:
                print(f"[Funding] {symbol} failed: {e}")
                continue

        # Sort by abs(funding_rate) descending
        rates.sort(key=lambda x: abs(x['funding_rate']), reverse=True)

        return rates
    except Exception as e:
        print(f"[Funding] Error: {e}")
        return []

def get_funding_extremes():
    """Get funding rates that are extremely high/low (risky)."""
    rates = get_funding_rates()
    extremes = [r for r in rates if abs(r['funding_rate']) > 0.002]
    return extremes

def get_funding_status(symbol='BTC'):
    """Get funding rate status for a single symbol."""
    rates = get_funding_rates()
    for r in rates:
        if r['symbol'] == symbol:
            return r
    return None
