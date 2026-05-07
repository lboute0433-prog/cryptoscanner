"""
Unit tests for Phase 1 Task 3 API endpoints.

Tests the three new exchange management endpoints:
- GET /api/exchanges/list
- GET /api/exchanges/status
- POST /api/exchanges/toggle

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


class TestExchangeListEndpoint(unittest.TestCase):
    """Test GET /api/exchanges/list endpoint."""

    def setUp(self):
        """Set up test client and app context."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.MultiExchangeManager')
    def test_list_exchanges_success(self, mock_manager_class):
        """Test successful retrieval of exchange list."""
        # Mock the manager
        mock_manager = MagicMock()
        mock_manager.get_available_exchanges.return_value = [
            'binance', 'bybit', 'kraken', 'okx', 'deribit'
        ]
        mock_manager_class.return_value = mock_manager

        # Make request
        response = self.client.get('/api/exchanges/list')

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('exchanges', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 5)
        self.assertEqual(len(data['exchanges']), 5)

    @patch('app.MultiExchangeManager')
    def test_list_exchanges_empty(self, mock_manager_class):
        """Test handling of empty exchange list."""
        mock_manager = MagicMock()
        mock_manager.get_available_exchanges.return_value = []
        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/exchanges/list')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['count'], 0)

    @patch('app.MultiExchangeManager')
    def test_list_exchanges_error(self, mock_manager_class):
        """Test error handling when manager fails."""
        mock_manager_class.side_effect = Exception('CCXT not available')

        response = self.client.get('/api/exchanges/list')

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)


class TestExchangeStatusEndpoint(unittest.TestCase):
    """Test GET /api/exchanges/status endpoint."""

    def setUp(self):
        """Set up test client and app context."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.MultiExchangeManager')
    def test_status_all_online(self, mock_manager_class):
        """Test status when all exchanges are online."""
        mock_manager = MagicMock()
        mock_manager.test_connection.return_value = True
        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/exchanges/status')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('exchanges', data)
        exchanges = data['exchanges']

        # Check at least one exchange
        self.assertGreater(len(exchanges), 0)
        # Check structure
        for exchange_name, status in exchanges.items():
            self.assertIn('online', status)
            self.assertIn('last_checked', status)

    @patch('app.MultiExchangeManager')
    def test_status_some_offline(self, mock_manager_class):
        """Test status when some exchanges are offline."""
        mock_manager = MagicMock()

        # Mock alternating online/offline
        def test_connection_side_effect(exc):
            return exc.lower() in ['binance', 'okx']

        mock_manager.test_connection.side_effect = test_connection_side_effect
        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/exchanges/status')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        exchanges = data['exchanges']

        # Verify we have status for test exchanges
        if 'binance' in exchanges:
            self.assertTrue(exchanges['binance']['online'])
        if 'bybit' in exchanges:
            self.assertFalse(exchanges['bybit']['online'])

    @patch('app.MultiExchangeManager')
    def test_status_error_handling(self, mock_manager_class):
        """Test error handling in status check."""
        mock_manager = MagicMock()
        mock_manager.test_connection.side_effect = Exception('Connection error')
        mock_manager_class.return_value = mock_manager

        response = self.client.get('/api/exchanges/status')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Should still return status structure, but with error details
        for exchange_name, status in data['exchanges'].items():
            self.assertFalse(status['online'])


class TestExchangeToggleEndpoint(unittest.TestCase):
    """Test POST /api/exchanges/toggle endpoint."""

    def setUp(self):
        """Set up test client and app context."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.get_session')
    @patch('app.toggle_user_exchange_setting')
    @patch('app.MultiExchangeManager')
    def test_toggle_enable_success(self, mock_manager_class, mock_toggle, mock_session):
        """Test successfully enabling an exchange."""
        # Mock session
        mock_session.return_value = {'user_id': 1, 'email': 'test@test.com'}

        # Mock manager
        mock_manager = MagicMock()
        mock_manager.get_available_exchanges.return_value = ['binance', 'bybit', 'kraken']
        mock_manager_class.return_value = mock_manager

        # Mock database toggle
        mock_toggle.return_value = True

        # Make request
        response = self.client.post(
            '/api/exchanges/toggle',
            data=json.dumps({'exchange': 'binance', 'enabled': True}),
            content_type='application/json'
        )

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['exchange'], 'binance')
        self.assertTrue(data['enabled'])

        # Verify toggle was called
        mock_toggle.assert_called_once()

    @patch('app.get_session')
    @patch('app.MultiExchangeManager')
    def test_toggle_not_authenticated(self, mock_manager_class, mock_session):
        """Test toggle without authentication."""
        mock_session.return_value = None

        response = self.client.post(
            '/api/exchanges/toggle',
            data=json.dumps({'exchange': 'binance', 'enabled': True}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.get_session')
    @patch('app.MultiExchangeManager')
    def test_toggle_missing_exchange(self, mock_manager_class, mock_session):
        """Test toggle with missing exchange parameter."""
        mock_session.return_value = {'user_id': 1}

        response = self.client.post(
            '/api/exchanges/toggle',
            data=json.dumps({'enabled': True}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.get_session')
    @patch('app.MultiExchangeManager')
    def test_toggle_missing_enabled_flag(self, mock_manager_class, mock_session):
        """Test toggle with missing enabled flag."""
        mock_session.return_value = {'user_id': 1}

        response = self.client.post(
            '/api/exchanges/toggle',
            data=json.dumps({'exchange': 'binance'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.get_session')
    @patch('app.MultiExchangeManager')
    def test_toggle_invalid_exchange(self, mock_manager_class, mock_session):
        """Test toggle with unknown exchange."""
        mock_session.return_value = {'user_id': 1}

        # Mock manager with limited exchanges
        mock_manager = MagicMock()
        mock_manager.get_available_exchanges.return_value = ['binance', 'bybit']
        mock_manager_class.return_value = mock_manager

        response = self.client.post(
            '/api/exchanges/toggle',
            data=json.dumps({'exchange': 'fake_exchange', 'enabled': True}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 422)
        data = json.loads(response.data)
        self.assertIn('error', data)

    @patch('app.get_session')
    @patch('app.toggle_user_exchange_setting')
    @patch('app.MultiExchangeManager')
    def test_toggle_database_error(self, mock_manager_class, mock_toggle, mock_session):
        """Test toggle when database update fails."""
        mock_session.return_value = {'user_id': 1}

        mock_manager = MagicMock()
        mock_manager.get_available_exchanges.return_value = ['binance', 'bybit']
        mock_manager_class.return_value = mock_manager

        # Mock toggle failure
        mock_toggle.return_value = False

        response = self.client.post(
            '/api/exchanges/toggle',
            data=json.dumps({'exchange': 'binance', 'enabled': True}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)

    @patch('app.get_session')
    @patch('app.toggle_user_exchange_setting')
    @patch('app.MultiExchangeManager')
    def test_toggle_disable_success(self, mock_manager_class, mock_toggle, mock_session):
        """Test successfully disabling an exchange."""
        mock_session.return_value = {'user_id': 1}

        mock_manager = MagicMock()
        mock_manager.get_available_exchanges.return_value = ['binance', 'bybit']
        mock_manager_class.return_value = mock_manager

        mock_toggle.return_value = True

        response = self.client.post(
            '/api/exchanges/toggle',
            data=json.dumps({'exchange': 'BINANCE', 'enabled': False}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['exchange'], 'binance')  # Should be lowercase
        self.assertFalse(data['enabled'])


class TestDatabaseFunctions(unittest.TestCase):
    """Test database functions for user exchange settings."""

    @patch('db.get_connection')
    def test_toggle_user_exchange_setting(self, mock_get_connection):
        """Test toggle_user_exchange_setting database function."""
        from db import toggle_user_exchange_setting

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_conn

        # Test success
        result = toggle_user_exchange_setting(1, 'binance', True)

        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch('db.get_connection')
    def test_get_user_enabled_exchanges(self, mock_get_connection):
        """Test get_user_enabled_exchanges database function."""
        from db import get_user_enabled_exchanges

        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn

        # Mock execute to return exchanges
        mock_conn.execute.return_value.fetchall.return_value = [
            ('binance',),
            ('bybit',),
            ('kraken',)
        ]

        result = get_user_enabled_exchanges(1)

        self.assertEqual(len(result), 3)
        self.assertIn('binance', result)
        self.assertIn('bybit', result)
        self.assertIn('kraken', result)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
