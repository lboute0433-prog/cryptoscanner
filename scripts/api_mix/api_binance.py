"""
Binance API wrapper
Gratuit illimité, données: prix, orderbook, trades, volumes
"""

import aiohttp
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

BINANCE_BASE = "https://api.binance.com/api/v3"


class BinanceAPI:
    """Wrapper Binance"""

    def __init__(self):
        self.base_url = BINANCE_BASE
        self.timeout = aiohttp.ClientTimeout(total=3)

    async def get_price(self, symbol: str = "BTCUSDT") -> Dict:
        """
        Fetch prix temps réel

        Args:
        - symbol: 'BTCUSDT', 'ETHUSDT', etc.

        Return:
        {
            'symbol': 'BTCUSDT',
            'price': '42000.00'
        }
        """

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/ticker/price"
            query_params = {'symbol': symbol}

            try:
                async with session.get(url, params=query_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Binance price {symbol}: {data['price']}")
                        return data
                    else:
                        raise Exception(f"Binance error: {response.status}")

            except asyncio.TimeoutError:
                raise Exception("Binance timeout")
            except Exception as e:
                logger.error(f"Binance get_price failed: {e}")
                raise

    async def get_orderbook(self, symbol: str = "BTCUSDT", limit: int = 10) -> Dict:
        """
        Fetch orderbook (bids/asks)

        Args:
        - symbol: 'BTCUSDT', etc.
        - limit: 5, 10, 20, 50 (défaut 10)

        Return:
        {
            'bids': [[price, quantity], ...],
            'asks': [[price, quantity], ...],
        }
        """

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/depth"
            query_params = {
                'symbol': symbol,
                'limit': limit,
            }

            try:
                async with session.get(url, params=query_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"Binance orderbook {symbol}: {len(data['bids'])} bids, {len(data['asks'])} asks"
                        )
                        return {
                            'symbol': symbol,
                            'bids': data['bids'],
                            'asks': data['asks'],
                        }
                    else:
                        raise Exception(f"Binance depth error: {response.status}")

            except Exception as e:
                logger.error(f"Binance get_orderbook failed: {e}")
                raise

    async def get_24h_stats(self, symbol: str = "BTCUSDT") -> Dict:
        """
        Fetch stats 24h (prix haut/bas, volume, etc.)
        """

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/ticker/24hr"
            query_params = {'symbol': symbol}

            try:
                async with session.get(url, params=query_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"Binance 24h {symbol}: high={data['highPrice']}, low={data['lowPrice']}"
                        )
                        return {
                            'symbol': symbol,
                            'high': data['highPrice'],
                            'low': data['lowPrice'],
                            'volume': data['volume'],
                            'price_change_24h': data['priceChange'],
                            'price_change_percent': data['priceChangePercent'],
                        }
                    else:
                        raise Exception(f"Binance 24hr error: {response.status}")

            except Exception as e:
                logger.error(f"Binance get_24h_stats failed: {e}")
                raise

    async def get_recent_trades(self, symbol: str = "BTCUSDT", limit: int = 10) -> List:
        """
        Fetch recent trades (volume réel)
        """

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            url = f"{self.base_url}/trades"
            query_params = {
                'symbol': symbol,
                'limit': limit,
            }

            try:
                async with session.get(url, params=query_params) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Binance recent trades {symbol}: {len(data)} trades")
                        return data
                    else:
                        raise Exception(f"Binance trades error: {response.status}")

            except Exception as e:
                logger.error(f"Binance get_recent_trades failed: {e}")
                raise


import asyncio
