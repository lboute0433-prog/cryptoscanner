"""
Unit tests for ccxt_wrapper.py
Tests MultiExchangeManager class with mocked CCXT responses.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ccxt_wrapper import MultiExchangeManager, ExchangeError


class TestMultiExchangeManager(unittest.TestCase):
    """Test suite for MultiExchangeManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock CCXT module before importing
        self.ccxt_patcher = patch('ccxt_wrapper.ccxt')
        self.ccxt_async_patcher = patch('ccxt_wrapper.ccxt_async')

        self.mock_ccxt = self.ccxt_patcher.start()
        self.mock_ccxt_async = self.ccxt_async_patcher.start()

        # Configure mock CCXT
        self.mock_ccxt.exchanges = [
            'binance', 'bybit', 'kraken', 'okx', 'gemini', 'kucoin'
        ]

        # Create mock exchange classes
        self.mock_binance = self._create_mock_exchange('binance')
        self.mock_bybit = self._create_mock_exchange('bybit')
        self.mock_kraken = self._create_mock_exchange('kraken')

        # Set up mock CCXT getattr
        def mock_getattr(obj, name, default=None):
            if name == 'binance':
                return lambda x: self.mock_binance
            elif name == 'bybit':
                return lambda x: self.mock_bybit
            elif name == 'kraken':
                return lambda x: self.mock_kraken
            return default

        self.mock_ccxt.exchanges = self.mock_ccxt.exchanges
        setattr(self.mock_ccxt, 'binance', lambda x: self.mock_binance)
        setattr(self.mock_ccxt, 'bybit', lambda x: self.mock_bybit)
        setattr(self.mock_ccxt, 'kraken', lambda x: self.mock_kraken)

    def tearDown(self):
        """Clean up patches."""
        self.ccxt_patcher.stop()
        self.ccxt_async_patcher.stop()

    def _create_mock_exchange(self, name):
        """Create a mock exchange instance."""
        mock_exchange = MagicMock()
        mock_exchange.id = name
        mock_exchange.has = {
            'fetchOHLCV': True,
            'fetchTicker': True,
            'fetchTickers': False,
            'fetchTrades': True,
            'fetchOrderBook': True,
        }
        return mock_exchange

    def test_initialization_with_default_exchanges(self):
        """Test initialization with default exchanges."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            manager = MultiExchangeManager(enable_async=False)
            self.assertEqual(manager.exchanges, manager.DEFAULT_EXCHANGES)
            self.assertIsNotNone(manager.exchange_instances)

    def test_initialization_with_custom_exchanges(self):
        """Test initialization with custom exchange list."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            custom_exchanges = ['binance', 'bybit']
            manager = MultiExchangeManager(
                exchanges=custom_exchanges,
                enable_async=False
            )
            self.assertEqual(manager.exchanges, custom_exchanges)

    def test_initialization_without_ccxt_raises_error(self):
        """Test that ExchangeError is raised if CCXT not available."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', False):
            with self.assertRaises(ExchangeError):
                MultiExchangeManager()

    def test_fetch_ohlcv_sync(self):
        """Test synchronous OHLCV fetching."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            # Setup mock OHLCV data
            mock_ohlcv = [
                [1609459200000, 29000, 29500, 28900, 29100, 1000],
                [1609462800000, 29100, 29600, 29000, 29200, 1100],
                [1609466400000, 29200, 29700, 29100, 29300, 1200],
            ]

            self.mock_binance.fetch_ohlcv = Mock(return_value=mock_ohlcv)
            self.mock_bybit.fetch_ohlcv = Mock(return_value=mock_ohlcv)

            manager = MultiExchangeManager(
                exchanges=['binance', 'bybit'],
                enable_async=False
            )
            manager.exchange_instances['binance'] = self.mock_binance
            manager.exchange_instances['bybit'] = self.mock_bybit

            result = manager.fetch_ohlcv('BTC/USDT', '1h', 100)

            # Verify result structure
            self.assertIn('binance', result)
            self.assertIn('bybit', result)
            self.assertEqual(len(result['binance']), 3)
            self.assertEqual(result['binance'][0][0], 1609459200000)
            self.assertEqual(result['binance'][0][4], 29100)  # Close price

    def test_fetch_ohlcv_with_error_handling(self):
        """Test error handling during OHLCV fetch."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            mock_ohlcv = [
                [1609459200000, 29000, 29500, 28900, 29100, 1000],
            ]

            self.mock_binance.fetch_ohlcv = Mock(return_value=mock_ohlcv)
            self.mock_bybit.fetch_ohlcv = Mock(
                side_effect=Exception("Rate limit exceeded")
            )

            manager = MultiExchangeManager(
                exchanges=['binance', 'bybit'],
                enable_async=False
            )
            manager.exchange_instances['binance'] = self.mock_binance
            manager.exchange_instances['bybit'] = self.mock_bybit

            result = manager.fetch_ohlcv('BTC/USDT', '1h', 100)

            # Binance should have data, Bybit should have empty list
            self.assertEqual(len(result['binance']), 1)
            self.assertEqual(result['bybit'], [])

    def test_get_available_exchanges(self):
        """Test getting list of available exchanges."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            manager = MultiExchangeManager(
                exchanges=['binance'],
                enable_async=False
            )

            exchanges = manager.get_available_exchanges()

            self.assertIsInstance(exchanges, list)
            self.assertIn('binance', exchanges)

    def test_get_exchange_info(self):
        """Test getting detailed exchange information (Extension)."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            manager = MultiExchangeManager(
                exchanges=['binance'],
                enable_async=False
            )
            manager.exchange_instances['binance'] = self.mock_binance

            exchange_info = manager.get_exchange_info()

            self.assertIsInstance(exchange_info, dict)
            self.assertIn('binance', exchange_info)
            self.assertTrue(exchange_info['binance']['active'])
            self.assertTrue(exchange_info['binance']['has_ohlcv'])

    def test_get_ticker_multi_exchange(self):
        """Test fetching tickers from multiple exchanges."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            # Setup mock ticker data
            mock_ticker_binance = {
                'symbol': 'BTC/USDT',
                'last': 42050.5,
                'bid': 42050.0,
                'ask': 42051.0,
                'baseVolume': 1234567,
                'quoteVolume': 52000000,
                'timestamp': 1609459200000,
                'datetime': '2021-01-01T00:00:00Z',
                'high': 42500,
                'low': 41900,
                'open': 42000,
                'close': 42050.5,
                'change': 50.5,
                'percentage': 0.12,
            }

            mock_ticker_bybit = {
                'symbol': 'BTC/USDT',
                'last': 42055.0,
                'bid': 42054.5,
                'ask': 42055.5,
                'baseVolume': 1200000,
                'quoteVolume': 51500000,
                'timestamp': 1609459200000,
                'datetime': '2021-01-01T00:00:00Z',
                'high': 42505,
                'low': 41905,
                'open': 42005,
                'close': 42055.0,
                'change': 55.0,
                'percentage': 0.13,
            }

            self.mock_binance.fetch_ticker = Mock(return_value=mock_ticker_binance)
            self.mock_bybit.fetch_ticker = Mock(return_value=mock_ticker_bybit)

            manager = MultiExchangeManager(
                exchanges=['binance', 'bybit'],
                enable_async=False
            )
            manager.exchange_instances['binance'] = self.mock_binance
            manager.exchange_instances['bybit'] = self.mock_bybit

            result = manager.get_ticker_multi_exchange('BTC/USDT')

            # Verify result structure
            self.assertIn('binance', result)
            self.assertIn('bybit', result)
            self.assertEqual(result['binance']['price'], 42050.5)
            self.assertEqual(result['bybit']['price'], 42055.0)
            self.assertEqual(result['binance']['bid'], 42050.0)
            self.assertEqual(result['bybit']['ask'], 42055.5)

    def test_test_connection_success(self):
        """Test successful connection to an exchange."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            mock_ticker = {
                'symbol': 'BTC/USDT',
                'last': 42050,
                'timestamp': 1609459200000,
            }
            self.mock_binance.fetch_ticker = Mock(return_value=mock_ticker)

            manager = MultiExchangeManager(
                exchanges=['binance'],
                enable_async=False
            )
            manager.exchange_instances['binance'] = self.mock_binance

            result = manager.test_connection('binance')

            self.assertTrue(result)
            self.mock_binance.fetch_ticker.assert_called_once_with('BTC/USDT')

    def test_test_connection_failure(self):
        """Test failed connection to an exchange."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            self.mock_binance.fetch_ticker = Mock(
                side_effect=Exception("Network error")
            )

            manager = MultiExchangeManager(
                exchanges=['binance'],
                enable_async=False
            )
            manager.exchange_instances['binance'] = self.mock_binance

            result = manager.test_connection('binance')

            self.assertFalse(result)

    def test_test_connection_nonexistent_exchange(self):
        """Test connection test with non-existent exchange."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            manager = MultiExchangeManager(
                exchanges=['binance'],
                enable_async=False
            )

            result = manager.test_connection('nonexistent')

            self.assertFalse(result)

    def test_rate_limit_configuration(self):
        """Test that rate limits are configured correctly."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            manager = MultiExchangeManager(
                exchanges=['binance', 'custom_exchange'],
                enable_async=False
            )

            # Test known exchange rate limit
            binance_limit = manager._get_rate_limit('binance')
            self.assertIsInstance(binance_limit, int)
            self.assertGreater(binance_limit, 0)

            # Test unknown exchange rate limit (should use default)
            custom_limit = manager._get_rate_limit('custom_exchange')
            self.assertIsInstance(custom_limit, int)
            self.assertGreater(custom_limit, 0)

    def test_verbose_logging(self):
        """Test verbose logging configuration."""
        with patch('ccxt_wrapper.CCXT_AVAILABLE', True):
            with patch('ccxt_wrapper.logger') as mock_logger:
                manager = MultiExchangeManager(
                    exchanges=['binance'],
                    enable_async=False,
                    verbose=True
                )

                # Check that verbose mode was enabled
                self.assertTrue(manager.verbose)


class TestCCXTIntegration(unittest.TestCase):
    """Integration tests that require actual CCXT library."""

    @patch('ccxt_wrapper.CCXT_AVAILABLE', True)
    def test_import_from_module(self):
        """Test that MultiExchangeManager can be imported."""
        from ccxt_wrapper import MultiExchangeManager as MEMTest
        self.assertIsNotNone(MEMTest)

    @patch('ccxt_wrapper.CCXT_AVAILABLE', True)
    def test_exception_type(self):
        """Test that ExchangeError is raised properly."""
        from ccxt_wrapper import ExchangeError as EE
        self.assertTrue(issubclass(EE, Exception))


def run_tests():
    """Run all tests and print results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMultiExchangeManager))
    suite.addTests(loader.loadTestsFromTestCase(TestCCXTIntegration))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code based on results
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
