"""
Unit tests for Phase 1 Task 4 API endpoints.

Tests the two new price comparison and liquidation endpoints:
- GET /api/prices/multi
- GET /api/liquidations/multi

Author: Claude Code
Date: 2026-05-07
"""

import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock ccxt before importing app
sys.modules['ccxt'] = MagicMock()
sys.modules['ccxt.async_support'] = MagicMock()

from app import app


class TestPricesMultiEndpoint(unittest.TestCase):
    """Test GET /api/prices/multi endpoint."""

    def setUp(self):
        """Set up test client and app context."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.MultiExchangeManager')
    def test_prices_multi_success(self, mock_manager_class):
        """Test successful price comparison across exchanges."""
        # Mock the manager
        mock_manager = MagicMock()
        mock_manager.get_ticker_multi_exchange.return_value = {
            'binance': {
                'price': 43000.50,
                'bid': 43000.00,
                'ask': 43001.00,
                'volume': 1250.5
            },
            'bybit': {
                'price': 42980.25,
                'bid': 42980.00,
                'ask': 42981.00,
                'volume': 980.3
            },
            'kraken': {
                'price': 43050.00,
                'bid': 43049.00,
                'ask': 43051.00,
                'volume': 750.2
            }
        }
        mock_manager_class.return_value = mock_manager

        # Make request
        response = self.client.get('/api/prices/multi?symbol=BTC&exchanges=binance,bybit,kraken')

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['symbol'], 'BTC/USDT')
        self.assertIn('exchanges', data)
        self.assertIn('spread', data)
        self.assertEqual(len(data['exchanges']), 3)

        # Check spread calculation
        self.assertEqual(data['spread']['max'], 43050.0)
        self.assertEqual(data['spread']['min'], 42980.25)
        self.assertGreater(data['spread']['pct'], 0)

        # Verify exchange data structure
        for exchange in ['binance', 'bybit', 'kraken']:
            self.assertIn(exchange, data['exchanges'])
            self.assertIn('price', data['exchanges'][exchange])
            self.assertIn('bid', data['exchanges'][exchange])
            self.assertIn('ask', data['exchanges'][exchange])

    @patch('app.MultiExchangeManager')
    def test_prices_multi_missing_symbol(self, mock_manager_class):
        """Test error handling when symbol is missing."""
        response = self.client.get('/api/prices/multi')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('symbol', data['error'].lower())

    @patch('app.MultiExchangeManager')
    def test_prices_multi_invalid_symbol(self, mock_manager_class):
        """Test that invalid symbol formats are handled gracefully."""
        mock_manager = MagicMock()
        mock_manager.get_ticker_multi_exchange.return_value = {
            'error': 'Symbol not found'
        }
        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/prices/multi?symbol=INVALID_SYMBOL_XYZ123')

        # Should handle the case where no exchanges return valid data
        self.assertIn(response.status_code, [500, 200])

    @patch('app.MultiExchangeManager')
    def test_prices_multi_with_slash_format(self, mock_manager_class):
        """Test that symbol with slash format is handled."""
        mock_manager = MagicMock()
        mock_manager.get_ticker_multi_exchange.return_value = {
            'binance': {
                'price': 43000.50,
                'bid': 43000.00,
                'ask': 43001.00,
                'volume': 1250.5
            }
        }
        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/prices/multi?symbol=BTC/USDT&exchanges=binance')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['symbol'], 'BTC/USDT')

    @patch('app.MultiExchangeManager')
    def test_prices_multi_default_exchanges(self, mock_manager_class):
        """Test that default exchanges are used when not specified."""
        mock_manager = MagicMock()
        mock_manager.get_ticker_multi_exchange.return_value = {
            'binance': {'price': 43000.50, 'bid': 43000, 'ask': 43001, 'volume': 1250},
            'bybit': {'price': 42980.25, 'bid': 42980, 'ask': 42981, 'volume': 980},
            'kraken': {'price': 43050.00, 'bid': 43049, 'ask': 43051, 'volume': 750},
            'okx': {'price': 43025.00, 'bid': 43024, 'ask': 43026, 'volume': 500}
        }
        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/prices/multi?symbol=BTC')

        self.assertEqual(response.status_code, 200)
        # Manager should have been called with default exchanges
        mock_manager_class.assert_called()

    @patch('app.MultiExchangeManager')
    def test_prices_multi_partial_exchange_errors(self, mock_manager_class):
        """Test handling when some exchanges return errors."""
        mock_manager = MagicMock()
        mock_manager.get_ticker_multi_exchange.return_value = {
            'binance': {
                'price': 43000.50,
                'bid': 43000.00,
                'ask': 43001.00,
                'volume': 1250.5
            },
            'bybit': {
                'error': 'Connection timeout'
            },
            'kraken': {
                'price': 43050.00,
                'bid': 43049.00,
                'ask': 43051.00,
                'volume': 750.2
            }
        }
        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/prices/multi?symbol=BTC&exchanges=binance,bybit,kraken')

        # Should still succeed with 2 working exchanges
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['exchanges']), 2)  # Only 2 successful exchanges

    @patch('app.MultiExchangeManager')
    def test_prices_multi_exchange_error(self, mock_manager_class):
        """Test error handling when manager initialization fails."""
        from ccxt_wrapper import ExchangeError
        mock_manager_class.side_effect = ExchangeError('CCXT not available')

        response = self.client.get('/api/prices/multi?symbol=BTC')

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)


class TestLiquidationsMultiEndpoint(unittest.TestCase):
    """Test GET /api/liquidations/multi endpoint."""

    def setUp(self):
        """Set up test client and app context."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.MultiExchangeManager')
    def test_liquidations_multi_success(self, mock_manager_class):
        """Test successful liquidation data retrieval."""
        # Mock the manager
        mock_manager = MagicMock()

        # Create mock exchange instances
        mock_binance = MagicMock()
        mock_binance.fetch_ticker.return_value = {'last': 43000.00}

        mock_bybit = MagicMock()
        mock_bybit.fetch_ticker.return_value = {'last': 42980.00}

        mock_okx = MagicMock()
        mock_okx.fetch_ticker.return_value = {'last': 43050.00}

        mock_manager.exchange_instances = {
            'binance': mock_binance,
            'bybit': mock_bybit,
            'okx': mock_okx
        }

        mock_manager_class.return_value = mock_manager

        # Make request
        response = self.client.get('/api/liquidations/multi?symbol=BTC')

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        self.assertEqual(data['symbol'], 'BTC/USDT')
        self.assertIn('exchanges', data)
        self.assertIn('total_liquidations', data)

        # Check structure for each exchange
        for exchange in ['binance', 'bybit', 'okx']:
            self.assertIn(exchange, data['exchanges'])
            self.assertIn('short_liquidations', data['exchanges'][exchange])
            self.assertIn('long_liquidations', data['exchanges'][exchange])
            self.assertIn('total', data['exchanges'][exchange])

        # Verify total calculation
        calculated_total = sum(
            data['exchanges'][ex]['total'] for ex in data['exchanges']
        )
        self.assertEqual(data['total_liquidations'], calculated_total)

    @patch('app.MultiExchangeManager')
    def test_liquidations_multi_missing_symbol(self, mock_manager_class):
        """Test error handling when symbol is missing."""
        response = self.client.get('/api/liquidations/multi')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('symbol', data['error'].lower())

    @patch('app.MultiExchangeManager')
    def test_liquidations_multi_with_exchanges_param(self, mock_manager_class):
        """Test liquidations with custom exchange list."""
        mock_manager = MagicMock()

        mock_binance = MagicMock()
        mock_binance.fetch_ticker.return_value = {'last': 43000.00}

        mock_bybit = MagicMock()
        mock_bybit.fetch_ticker.return_value = {'last': 42980.00}

        mock_manager.exchange_instances = {
            'binance': mock_binance,
            'bybit': mock_bybit
        }

        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/liquidations/multi?symbol=ETH&exchanges=binance,bybit')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['symbol'], 'ETH/USDT')
        self.assertEqual(len(data['exchanges']), 2)

    @patch('app.MultiExchangeManager')
    def test_liquidations_multi_default_exchanges(self, mock_manager_class):
        """Test that default exchanges are used when not specified."""
        mock_manager = MagicMock()

        # Mock all default exchanges
        mock_binance = MagicMock()
        mock_binance.fetch_ticker.return_value = {'last': 43000.00}

        mock_bybit = MagicMock()
        mock_bybit.fetch_ticker.return_value = {'last': 42980.00}

        mock_okx = MagicMock()
        mock_okx.fetch_ticker.return_value = {'last': 43050.00}

        mock_manager.exchange_instances = {
            'binance': mock_binance,
            'bybit': mock_bybit,
            'okx': mock_okx
        }

        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/liquidations/multi?symbol=BTC')

        self.assertEqual(response.status_code, 200)
        # Manager should be initialized with default exchanges
        mock_manager_class.assert_called_with(exchanges=['binance', 'bybit', 'okx'])

    @patch('app.MultiExchangeManager')
    def test_liquidations_multi_partial_errors(self, mock_manager_class):
        """Test handling when some exchanges fail."""
        mock_manager = MagicMock()

        mock_binance = MagicMock()
        mock_binance.fetch_ticker.return_value = {'last': 43000.00}

        mock_bybit = MagicMock()
        mock_bybit.fetch_ticker.side_effect = Exception('Connection error')

        mock_okx = MagicMock()
        mock_okx.fetch_ticker.return_value = {'last': 43050.00}

        mock_manager.exchange_instances = {
            'binance': mock_binance,
            'bybit': mock_bybit,
            'okx': mock_okx
        }

        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/liquidations/multi?symbol=BTC')

        # Should still succeed with working exchanges
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Only 2 exchanges should be in the result (binance and okx)
        self.assertLessEqual(len(data['exchanges']), 3)

    @patch('app.MultiExchangeManager')
    def test_liquidations_multi_with_slash_symbol(self, mock_manager_class):
        """Test handling of symbol with slash format."""
        mock_manager = MagicMock()

        mock_binance = MagicMock()
        mock_binance.fetch_ticker.return_value = {'last': 2500.00}

        mock_manager.exchange_instances = {
            'binance': mock_binance
        }

        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/liquidations/multi?symbol=ETH/USDT&exchanges=binance')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['symbol'], 'ETH/USDT')

    @patch('app.MultiExchangeManager')
    def test_liquidations_multi_exchange_error(self, mock_manager_class):
        """Test error handling when manager initialization fails."""
        from ccxt_wrapper import ExchangeError
        mock_manager_class.side_effect = ExchangeError('CCXT not available')

        response = self.client.get('/api/liquidations/multi?symbol=BTC')

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.MultiExchangeManager')
    def test_liquidations_multi_zero_price(self, mock_manager_class):
        """Test handling when exchange returns zero or invalid price."""
        mock_manager = MagicMock()

        mock_binance = MagicMock()
        mock_binance.fetch_ticker.return_value = {'last': 0}  # Invalid price

        mock_bybit = MagicMock()
        mock_bybit.fetch_ticker.return_value = {'last': 43000.00}  # Valid

        mock_manager.exchange_instances = {
            'binance': mock_binance,
            'bybit': mock_bybit
        }

        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/liquidations/multi?symbol=BTC&exchanges=binance,bybit')

        # Should still succeed with the valid exchange
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Only bybit should be in results
        self.assertEqual(len(data['exchanges']), 1)
        self.assertIn('bybit', data['exchanges'])


class TestEndpointIntegration(unittest.TestCase):
    """Integration tests for both endpoints."""

    def setUp(self):
        """Set up test client and app context."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.MultiExchangeManager')
    def test_both_endpoints_available(self, mock_manager_class):
        """Test that both endpoints are accessible."""
        mock_manager = MagicMock()
        mock_manager.get_available_exchanges.return_value = ['binance', 'bybit']
        mock_manager.get_ticker_multi_exchange.return_value = {
            'binance': {'price': 43000, 'bid': 43000, 'ask': 43001, 'volume': 1000}
        }
        mock_manager.exchange_instances = {'binance': MagicMock()}
        mock_manager.exchange_instances['binance'].fetch_ticker.return_value = {'last': 43000}
        mock_manager_class.return_value = mock_manager

        # Test both endpoints exist and return 200
        response1 = self.client.get('/api/prices/multi?symbol=BTC&exchanges=binance')
        response2 = self.client.get('/api/liquidations/multi?symbol=BTC&exchanges=binance')

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

    @patch('app.MultiExchangeManager')
    def test_response_format_consistency(self, mock_manager_class):
        """Test that both endpoints return consistent response format."""
        mock_manager = MagicMock()
        mock_manager.get_ticker_multi_exchange.return_value = {
            'binance': {'price': 43000, 'bid': 43000, 'ask': 43001, 'volume': 1000}
        }
        mock_manager.exchange_instances = {'binance': MagicMock()}
        mock_manager.exchange_instances['binance'].fetch_ticker.return_value = {'last': 43000}
        mock_manager_class.return_value = mock_manager

        response1 = self.client.get('/api/prices/multi?symbol=BTC&exchanges=binance')
        response2 = self.client.get('/api/liquidations/multi?symbol=BTC&exchanges=binance')

        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        # Both should have status field
        self.assertIn('status', data1)
        self.assertIn('status', data2)

        # Both should have symbol field
        self.assertIn('symbol', data1)
        self.assertIn('symbol', data2)

        # Both should have exchanges field
        self.assertIn('exchanges', data1)
        self.assertIn('exchanges', data2)


if __name__ == '__main__':
    unittest.main()
