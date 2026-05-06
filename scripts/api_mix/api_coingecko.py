"""
CoinGecko API wrapper
Gratuit, ~30 req/min, données: prix, market cap, volume, historique
"""

import aiohttp
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"


class CoinGeckoAPI:
    """Wrapper CoinGecko"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = COINGECKO_BASE
        self.timeout = aiohttp.ClientTimeout(total=5)

    async def fetch_price(self, params: Dict = None) -> Dict:
        """
        Fetch prix temps réel

        Params:
        - ids: ['bitcoin', 'ethereum'] (défaut: BTC, ETH)
        - vs_currencies: ['usd'] (défaut)

        Return:
        {
            'bitcoin': {'usd': 42000},
            'ethereum': {'usd': 2200}
        }
        """

        ids = params.get('ids', ['bitcoin', 'ethereum']) if params else ['bitcoin', 'ethereum']
        vs_currencies = params.get('vs_currencies', 'usd') if params else 'usd'

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/simple/price"
            query_params = {
                'ids': ','.join(ids),
                'vs_currencies': vs_currencies,
                'market_cap': 'true',
                'market_cap_change_24h': 'true',
            }

            try:
                async with session.get(url, params=query_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"CoinGecko price fetch: {len(data)} coins")
                        return data
                    elif response.status == 429:
                        raise Exception("CoinGecko rate limit hit")
                    else:
                        raise Exception(f"CoinGecko error: {response.status}")

            except asyncio.TimeoutError:
                raise Exception("CoinGecko timeout")
            except Exception as e:
                logger.error(f"CoinGecko fetch_price failed: {e}")
                raise

    async def fetch_market_data(self, params: Dict = None) -> Dict:
        """
        Fetch données marché globales
        Market cap total, BTC dominance, volume 24h
        """

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/global"

            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("CoinGecko global market data fetched")
                        return data['data']
                    else:
                        raise Exception(f"CoinGecko global error: {response.status}")

            except Exception as e:
                logger.error(f"CoinGecko fetch_market_data failed: {e}")
                raise

    async def fetch_ohlc(self, coin_id: str, days: int = 30) -> List:
        """
        Fetch OHLC (prix ouverture/haut/bas/fermeture)
        """

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/coins/{coin_id}/ohlc"
            query_params = {
                'vs_currency': 'usd',
                'days': days,
            }

            try:
                async with session.get(url, params=query_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"CoinGecko OHLC {coin_id}: {len(data)} candles")
                        return data
                    else:
                        raise Exception(f"CoinGecko OHLC error: {response.status}")

            except Exception as e:
                logger.error(f"CoinGecko fetch_ohlc failed: {e}")
                raise


import asyncio
