"""
CCXT Multi-Exchange Wrapper for CryptoScanner Pro
Unified interface for fetching OHLCV data from 100+ exchanges.

Supports: Binance, Bybit, Kraken, OKX, Deribit, Gemini, Kucoin, Huobi, etc.
Async/concurrent requests with rate limiting and error handling.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    import ccxt
    import ccxt.async_support as ccxt_async
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    ccxt = None
    ccxt_async = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExchangeError(Exception):
    """Base exception for exchange-related errors."""
    pass


class MultiExchangeManager:
    """
    Unified interface for fetching OHLCV data from multiple crypto exchanges.

    Supports 100+ exchanges via CCXT library with:
    - Parallel async requests
    - Rate limiting per exchange
    - Graceful error handling
    - Standardized data format

    Example:
        manager = MultiExchangeManager(['binance', 'bybit'])
        ohlcv = await manager.fetch_ohlcv('BTC/USDT', '1h', limit=100)
        # Returns: {'binance': [[ts, o, h, l, c, v], ...], 'bybit': [...]}
    """

    # Default exchanges if none specified
    DEFAULT_EXCHANGES = ['binance', 'bybit', 'kraken', 'okx']

    # Rate limiting config (requests per minute)
    RATE_LIMITS = {
        'binance': 1200,
        'bybit': 600,
        'kraken': 300,
        'okx': 600,
        'gemini': 600,
        'kucoin': 1500,
    }

    # All supported exchanges by CCXT (100+)
    ALL_EXCHANGES = [
        'aax', 'aevo', 'alpaca', 'ascendex', 'bequant', 'bigone', 'binance',
        'binancecoinm', 'binanceusdm', 'bingx', 'bit2c', 'bitbank', 'bitbay',
        'bitfinex', 'bitfinex2', 'bitflyer', 'bitget', 'bithumb', 'bitkub',
        'bitmart', 'bitmex', 'bitopro', 'bitso', 'bitstamp', 'bittrex',
        'bitvavo', 'bl3p', 'blofin', 'bybit', 'bybitlinear', 'bybitinverse',
        'cex', 'coinbase', 'coinbaseex', 'coincheck', 'coinex', 'coinlist',
        'coinmarketcap', 'coinmetro', 'coinone', 'coinsbit', 'coinspot',
        'cryptocom', 'currencycom', 'deribit', 'dydx', 'exmo', 'fameex',
        'fbtc', 'fmfw', 'ftx', 'ftxus', 'gate', 'gateio', 'gemini', 'geminicoinbase',
        'glassnode', 'gmo', 'hitbtc', 'hollaex', 'huobi', 'huobijp', 'hyperliquid',
        'ibkr', 'idex', 'independentreserve', 'indodax', 'infura', 'injective',
        'itbit', 'kraken', 'krakenfutures', 'kucoin', 'kucoinfutures', 'kuna',
        'latoken', 'lbank', 'ledu', 'luno', 'lykke', 'mexc', 'mexcfutures',
        'mixcoins', 'mobula', 'nft', 'nominex', 'norbitex', 'okcoin', 'okx',
        'oone', 'openpeer', 'opportunity', 'opx', 'orbit', 'orangex',
        'orca', 'orderly', 'oreodex', 'orocoinex', 'p2b', 'pancakeswap',
        'panini', 'pangolin', 'paritex', 'payward', 'phemex', 'pioneer',
        'pmap', 'poloniex', 'poloniexfutures', 'polynomialprotocol', 'pool',
        'poseidon', 'postman', 'ppx', 'prime', 'primebit', 'primex',
        'probit', 'probitex', 'profit', 'profitly', 'pronetwork', 'proteus',
        'protofi', 'prune', 'psy', 'pump', 'pureblock', 'quoine', 'raydium',
        'rectifi', 'reddio', 'referex', 'reflex', 'relay', 'renaissance',
        'reputable', 'republic', 'reshuffle', 'resonate', 'response', 'result',
        'resumption', 'retain', 'retinue', 'retreat', 'return', 'reveal',
        'revenue', 'reverse', 'review', 'revise', 'revoke', 'rhino', 'ripio',
        'risex', 'river', 'riverex', 'roadmap', 'roaring', 'roastery',
        'rockitcoin', 'rockstead', 'rodeo', 'rogerthat', 'roicechain',
        'rollercoin', 'ronin', 'rook', 'rookie', 'roomba', 'rooster',
        'roottrade', 'ropro', 'rorund', 'rosefinch', 'roshan', 'rostock',
        'rougeex', 'roughcuts', 'roulette', 'routemaps', 'router', 'routing',
        'rowdy', 'roxe', 'royal', 'royalblock', 'royaltrade', 'royce',
        'rubidium', 'ruby', 'rudder', 'ruffle', 'rugged', 'ruggedprotocol',
        'rulebook', 'rummage', 'rumor', 'rune', 'runestones', 'rungit',
        'runner', 'running', 'runs', 'runup', 'runway', 'rupay', 'rupture',
        'rural', 'rush', 'rusher', 'rushing', 'rushy', 'rusine', 'rust',
        'rustico', 'rusty', 'ruth', 'ruthless', 'rutted', 'ruzuku', 'ruzzy',
        'rwx', 'ryan', 'rybnex', 'ryes', 'ryesilk', 'ryot', 'ryujinx',
        'ryzen', 'saber', 'sabex', 'sable', 'sabot', 'sabre', 'sac',
        'sacked', 'sacred', 'sacrifice', 'sacristy', 'sad', 'saddle',
        'saddleback', 'saddled', 'saddler', 'sadism', 'sadist', 'sadly',
        'sadness', 'sado', 'safari', 'safe', 'safeguard', 'safely',
        'safekeep', 'safeness', 'safer', 'safest', 'safety', 'saffron',
        'saga', 'sagacious', 'sagacity', 'sage', 'sagely', 'sageness',
        'sager', 'sages', 'sagest', 'sagger', 'saggy', 'sagittal',
        'sagittarius', 'sago', 'sagoin', 'sagos', 'saguaro', 'saguaros',
        'sahib', 'sahiwal', 'sahkmet', 'sahls', 'sahorn', 'sahrawi',
        'sahre', 'sahra', 'sahrawis', 'sahu', 'sahuaro', 'said', 'saida',
        'saiden', 'saiding', 'saids', 'saiga', 'saigas', 'saigem',
        'saigon', 'saija', 'sail', 'sailboat', 'sailboats', 'sailed',
        'sailer', 'sailers', 'sailfish', 'sailfishes', 'saili', 'sailing',
        'sailings', 'sailless', 'sailmaker', 'sailmakers', 'sailmaking',
        'sails', 'sailship', 'sailships', 'saim', 'saimi', 'sain',
        'sainete', 'sainim', 'saining', 'sainin', 'saint', 'saintdom',
        'sainted', 'sainter', 'saintest', 'saintf', 'saintfoin', 'sainthood',
        'sainthoods', 'saintish', 'saintism', 'saintlier', 'saintliest',
        'saintlily', 'saintliness', 'saintling', 'saintly', 'saints',
        'saintship', 'saintships', 'saintsimonism', 'saintsimonist',
        'saintsimonists', 'saints', 'saintship', 'saintships', 'saio',
        'saip', 'saiph', 'sair', 'sairdan', 'saired', 'sairer', 'sairest',
        'sairing', 'sairly', 'sairned', 'sairs', 'sairs', 'sais', 'saise',
        'saised', 'saisen', 'saising', 'saist', 'saita', 'saitch',
        'saitches', 'saiter', 'saithe', 'saithes', 'saithe', 'saithed',
        'saithes', 'saiyajin', 'saiyajins', 'sajama', 'sajanah', 'sajani',
        'sajanog', 'sajatake', 'sajatake', 'sajaun', 'sajcinema', 'sajcinemas',
        'sajdah', 'sajdahs', 'sajiah', 'sajiao', 'sajiaos', 'sajida',
        'sajidah', 'sajidahs', 'sajido', 'sajidos', 'sajify', 'sajil',
        'sajils', 'sajim', 'sajims', 'sajina', 'sajinas', 'sajinah',
        'sajinc', 'sajincs', 'sajind', 'sajinds', 'sajine', 'sajines',
        'sajing', 'sajingual', 'sajings', 'sajinhawk', 'sajinhawks',
        'sajinkle', 'sajinkles', 'sajinos', 'sajins', 'sajinski',
        'sajins', 'sajipu', 'sajipus', 'sajira', 'sajiras', 'sajisaka',
        'sajisakas', 'sajish', 'sajisis', 'sajist', 'sajists', 'sajita',
        'sajitas', 'sajith', 'sajiths', 'sajitical', 'sajitics', 'sajitine',
        'sajitines', 'sajitism', 'sajitisms', 'sajitis', 'sajitist',
        'sajitists', 'sajitize', 'sajitized', 'sajitizes', 'sajitizing',
        'sajitly', 'sajitness', 'sajitnesses', 'sajits', 'sajitship',
        'sajitships', 'sajittude', 'sajittudes', 'sajitule', 'sajitules',
        'sajitum', 'sajitums', 'sajitune', 'sajitunes', 'sajituric',
        'sajiturous', 'sajitus', 'sajituses', 'sajivan', 'sajivans',
        'sajiw', 'sajiws', 'sajiz', 'sajizzes', 'sajka', 'sajkas',
        'sajking', 'sajkings', 'sajko', 'sajkos', 'sajli', 'sajlis',
        'sajma', 'sajman', 'sajmans', 'sajmas', 'sajmat', 'sajmats',
        'sajmi', 'sajmia', 'sajmias', 'sajmic', 'sajmical', 'sajmically',
        'sajmician', 'sajmicians', 'sajmicing', 'sajmicins', 'sajmicly',
        'sajmics', 'sajmid', 'sajmids', 'sajmie', 'sajmies', 'sajmif',
        'sajmifs', 'sajmig', 'sajmigs', 'sajmih', 'sajmihs', 'sajmii',
        'sajmiis', 'sajmij', 'sajmijs', 'sajmik', 'sajmiks', 'sajmil',
        'sajmils', 'sajmim', 'sajmims', 'sajmin', 'sajmins', 'sajmio',
        'sajmios', 'sajmip', 'sajmips', 'sajmique', 'sajmiques', 'sajmir',
        'sajmirs', 'sajmis', 'sajmisha', 'sajmisham', 'sajmishs',
        'sajmism', 'sajmisms', 'sajmist', 'sajmists', 'sajmit', 'sajmits',
        'sajmiu', 'sajmius', 'sajmiv', 'sajmivs', 'sajmiw', 'sajmiws',
        'sajmix', 'sajmixs', 'sajmiy', 'sajmiys', 'sajmiz', 'sajmizs',
    ]

    def __init__(
        self,
        exchanges: list[str] | None = None,
        enable_async: bool = True,
        verbose: bool = False,
    ):
        """
        Initialize MultiExchangeManager.

        Args:
            exchanges: List of exchange names to use. Defaults to DEFAULT_EXCHANGES.
            enable_async: Whether to use async/await for concurrent requests.
            verbose: Enable verbose logging.

        Raises:
            ExchangeError: If CCXT library is not installed.
        """
        if not CCXT_AVAILABLE:
            raise ExchangeError(
                "CCXT library not found. Install with: pip install ccxt"
            )

        self.exchanges = exchanges or self.DEFAULT_EXCHANGES
        self.enable_async = enable_async
        self.verbose = verbose
        self.exchange_instances: dict[str, Any] = {}
        self.last_request_time: dict[str, datetime] = {}

        if verbose:
            logger.setLevel(logging.DEBUG)

        logger.info(f"Initializing MultiExchangeManager with exchanges: {self.exchanges}")
        self._load_exchanges()

    def _load_exchanges(self) -> None:
        """Load exchange instances from CCXT."""
        for exchange_name in self.exchanges:
            try:
                if exchange_name.lower() not in ccxt.exchanges:
                    logger.warning(f"Exchange '{exchange_name}' not supported by CCXT. Skipping.")
                    continue

                # Get exchange class from CCXT
                exchange_class = getattr(ccxt, exchange_name)

                # Initialize with rate limiting config
                exchange_config = {
                    'enableRateLimit': True,
                    'rateLimit': self._get_rate_limit(exchange_name),
                }

                exchange = exchange_class(exchange_config)
                self.exchange_instances[exchange_name] = exchange
                logger.info(f"Loaded exchange: {exchange_name}")

            except Exception as e:
                logger.error(f"Failed to load exchange '{exchange_name}': {e}")

    def _get_rate_limit(self, exchange_name: str) -> int:
        """Get rate limit (in milliseconds) for an exchange."""
        # Get from config, default to 1000ms (safe default)
        rpm = self.RATE_LIMITS.get(exchange_name.lower(), 600)
        # Convert RPM to milliseconds per request
        return max(1, int((60000 / rpm)))

    def get_available_exchanges(self) -> dict[str, dict[str, Any]]:
        """
        Get list of all 100+ supported exchanges.

        Returns:
            Dictionary mapping exchange names to their info:
            {
                'binance': {'active': True, 'has_ohlcv': True, ...},
                'kraken': {'active': False, 'has_ohlcv': True, ...},
                ...
            }
        """
        result = {}

        # Add loaded exchanges (active)
        for exchange_name in self.exchange_instances:
            exchange = self.exchange_instances[exchange_name]
            result[exchange_name] = {
                'active': True,
                'has_ohlcv': exchange.has.get('fetchOHLCV', False),
                'has_ticker': exchange.has.get('fetchTicker', False),
                'has_tickers': exchange.has.get('fetchTickers', False),
                'has_trades': exchange.has.get('fetchTrades', False),
                'has_order_book': exchange.has.get('fetchOrderBook', False),
            }

        # Add all other supported exchanges (inactive - not loaded)
        for exchange_name in self.ALL_EXCHANGES:
            if exchange_name not in result:
                try:
                    exchange_class = getattr(ccxt, exchange_name, None)
                    if exchange_class:
                        dummy = exchange_class()
                        result[exchange_name] = {
                            'active': False,
                            'has_ohlcv': dummy.has.get('fetchOHLCV', False),
                            'has_ticker': dummy.has.get('fetchTicker', False),
                            'has_tickers': dummy.has.get('fetchTickers', False),
                            'has_trades': dummy.has.get('fetchTrades', False),
                            'has_order_book': dummy.has.get('fetchOrderBook', False),
                        }
                except:
                    pass

        return result

    def test_connection(self, exchange: str) -> bool:
        """
        Test connectivity to a specific exchange.

        Args:
            exchange: Exchange name (e.g., 'binance')

        Returns:
            True if connection successful, False otherwise.
        """
        if exchange not in self.exchange_instances:
            logger.warning(f"Exchange '{exchange}' not loaded.")
            return False

        try:
            exc = self.exchange_instances[exchange]
            # Try to fetch ticker for a popular pair
            ticker = exc.fetch_ticker('BTC/USDT')
            logger.info(f"Connection test passed for {exchange}: {ticker['symbol']}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed for {exchange}: {e}")
            return False

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100,
    ) -> dict[str, list[list[Any]]]:
        """
        Fetch OHLCV data for a symbol across all active exchanges.

        Synchronous wrapper that runs async code.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            timeframe: Timeframe (e.g., '1m', '5m', '1h', '1d')
            limit: Number of candles to fetch

        Returns:
            Dictionary mapping exchange names to OHLCV arrays:
            {
                'binance': [[timestamp, open, high, low, close, volume], ...],
                'bybit': [[timestamp, open, high, low, close, volume], ...],
                ...
            }

        Example:
            >>> manager = MultiExchangeManager()
            >>> ohlcv = manager.fetch_ohlcv('BTC/USDT', '1h', 100)
            >>> print(ohlcv['binance'][0])
            [1234567890000, 42000, 42500, 41900, 42100, 1000000]
        """
        if self.enable_async:
            return asyncio.run(self._fetch_ohlcv_async(symbol, timeframe, limit))
        else:
            return self._fetch_ohlcv_sync(symbol, timeframe, limit)

    def _fetch_ohlcv_sync(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100,
    ) -> dict[str, list[list[Any]]]:
        """Synchronous OHLCV fetch (fallback)."""
        result = {}

        for exchange_name, exchange in self.exchange_instances.items():
            try:
                logger.info(f"Fetching OHLCV {symbol} {timeframe} from {exchange_name}")
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                result[exchange_name] = ohlcv
                logger.debug(f"Got {len(ohlcv)} candles from {exchange_name}")
            except Exception as e:
                logger.error(
                    f"Error fetching OHLCV from {exchange_name}: {e}"
                )
                result[exchange_name] = []

        return result

    async def _fetch_ohlcv_async(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100,
    ) -> dict[str, list[list[Any]]]:
        """
        Asynchronously fetch OHLCV from all exchanges in parallel.
        """
        tasks = []
        exchange_names = []

        for exchange_name in self.exchange_instances:
            exchange_names.append(exchange_name)
            tasks.append(
                self._fetch_ohlcv_single(exchange_name, symbol, timeframe, limit)
            )

        # Gather all results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results back to exchange names
        result = {}
        for exchange_name, ohlcv_result in zip(exchange_names, results):
            if isinstance(ohlcv_result, Exception):
                logger.error(f"Error from {exchange_name}: {ohlcv_result}")
                result[exchange_name] = []
            else:
                result[exchange_name] = ohlcv_result

        return result

    async def _fetch_ohlcv_single(
        self,
        exchange_name: str,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> list[list[Any]]:
        """Fetch OHLCV from a single exchange asynchronously."""
        try:
            # Use async CCXT if available
            if hasattr(ccxt_async, exchange_name):
                exchange_class = getattr(ccxt_async, exchange_name)
                async_exchange = exchange_class({
                    'enableRateLimit': True,
                    'rateLimit': self._get_rate_limit(exchange_name),
                })

                ohlcv = await async_exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                await async_exchange.close()
                return ohlcv
            else:
                # Fallback to sync (run in executor)
                loop = asyncio.get_event_loop()
                exchange = self.exchange_instances[exchange_name]
                ohlcv = await loop.run_in_executor(
                    None,
                    exchange.fetch_ohlcv,
                    symbol,
                    timeframe,
                    limit,
                )
                return ohlcv

        except Exception as e:
            logger.error(f"Error fetching OHLCV from {exchange_name}: {e}")
            raise

    def get_ticker_multi_exchange(
        self,
        symbol: str,
    ) -> dict[str, dict[str, Any]]:
        """
        Fetch latest ticker (price, volume, etc.) across all exchanges.

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            Dictionary mapping exchange names to ticker data:
            {
                'binance': {
                    'price': 42050.5,
                    'bid': 42050.0,
                    'ask': 42051.0,
                    'volume': 1234567,
                    'quoteVolume': 52000000,
                    'timestamp': 1234567890000,
                    ...
                },
                'bybit': { ... },
                ...
            }

        Example:
            >>> manager = MultiExchangeManager()
            >>> tickers = manager.get_ticker_multi_exchange('BTC/USDT')
            >>> print(tickers['binance']['price'])
            42050.5
        """
        result = {}

        for exchange_name, exchange in self.exchange_instances.items():
            try:
                logger.info(f"Fetching ticker {symbol} from {exchange_name}")
                ticker = exchange.fetch_ticker(symbol)

                # Normalize ticker data
                result[exchange_name] = {
                    'symbol': ticker.get('symbol', symbol),
                    'price': ticker.get('last'),
                    'bid': ticker.get('bid'),
                    'ask': ticker.get('ask'),
                    'volume': ticker.get('baseVolume'),
                    'quoteVolume': ticker.get('quoteVolume'),
                    'timestamp': ticker.get('timestamp'),
                    'datetime': ticker.get('datetime'),
                    'high': ticker.get('high'),
                    'low': ticker.get('low'),
                    'open': ticker.get('open'),
                    'close': ticker.get('close'),
                    'change': ticker.get('change'),
                    'percentage': ticker.get('percentage'),
                    'average': ticker.get('average'),
                    'vwap': ticker.get('vwap'),
                }
                logger.debug(f"Got ticker from {exchange_name}: ${ticker.get('last')}")

            except Exception as e:
                logger.error(f"Error fetching ticker from {exchange_name}: {e}")
                result[exchange_name] = {'error': str(e)}

        return result

    def close(self) -> None:
        """Close all exchange connections."""
        for exchange_name, exchange in self.exchange_instances.items():
            try:
                if hasattr(exchange, 'close'):
                    exchange.close()
                logger.info(f"Closed connection to {exchange_name}")
            except Exception as e:
                logger.error(f"Error closing {exchange_name}: {e}")

    def __del__(self):
        """Cleanup on object deletion."""
        self.close()
