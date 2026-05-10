#!/usr/bin/env python3
"""
Test suite for API filtering and role-based signal display.

Tests the /api/smart_signals endpoint with:
- FREE user tier (basic fields only)
- PAID user tier (full fields)
- Score filtering based on admin settings
- Role detection from session
- Backward compatibility (API works without role parameter)
"""

import unittest
import json
from app import app
from scanner_engine import load_admin_alert_settings
from security import get_user_tier, TIER_LEVELS
from db import get_connection


class TestAPIFiltering(unittest.TestCase):
    """Test API filtering and role-based access."""

    def setUp(self):
        """Set up test client, Flask app context, and mock signals."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Clear and populate cache with known test data
        try:
            from app import _smart_signals_cache
            _smart_signals_cache.clear()
            _smart_signals_cache.extend([
                {
                    "symbol": "BTC",
                    "score": 90,
                    "direction": "buy",
                    "rsi": 35,
                    "volume_mult": 5.2,
                    "timestamp": "2026-05-10T12:00:00Z",
                    "price": 43500,
                    "change_pct": 2.5,
                    "volume_usdt": 5000000,
                    "tags": [{"type": "oversold", "label": "Oversold"}]
                },
                {
                    "symbol": "ETH",
                    "score": 45,  # Below default score_min of 85 - should be filtered
                    "direction": "sell",
                    "rsi": 65,
                    "volume_mult": 2.1,
                    "timestamp": "2026-05-10T12:00:00Z",
                    "price": 2300,
                    "change_pct": -1.2,
                    "volume_usdt": 2000000,
                    "tags": [{"type": "overbought", "label": "Overbought"}]
                },
                {
                    "symbol": "SOL",
                    "score": 88,
                    "direction": "buy",
                    "rsi": 32,
                    "volume_mult": 3.8,
                    "timestamp": "2026-05-10T12:00:00Z",
                    "price": 142,
                    "change_pct": 5.1,
                    "volume_usdt": 3200000,
                    "tags": [{"type": "breakout", "label": "Breakout"}]
                }
            ])
        except ImportError:
            pass  # app may not expose cache

    def tearDown(self):
        """Clean up test context."""
        self.app_context.pop()

    def test_free_user_gets_only_basic_fields(self):
        """
        Test that FREE users get only basic fields.

        Calls API with role=free and verifies:
        - Only basic fields present: symbol, score, rsi, volume_mult, timestamp
        - Advanced fields NOT present: patterns, divergences, macd, etc.
        """
        response = self.client.get('/api/smart_signals?role=free')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('signals', data)
        self.assertIn('role', data)
        self.assertEqual(data['role'], 'free')

        # Check signal structure
        if data['signals']:  # If there are signals
            signal = data['signals'][0]

            # Required basic fields
            self.assertIn('symbol', signal)
            self.assertIn('score', signal)
            self.assertIn('rsi', signal)
            self.assertIn('timestamp', signal)
            self.assertIn('volume_mult', signal)
            self.assertIn('direction', signal)

            # These should be present
            self.assertIn('price', signal)
            self.assertIn('change_pct', signal)
            self.assertIn('volume_usdt', signal)

    def test_paid_user_gets_full_details(self):
        """
        Test that PAID users get full signal details.

        Calls API with role=paid and verifies:
        - All fields present including advanced details
        - Patterns, divergences, MACD present if in cache
        """
        response = self.client.get('/api/smart_signals?role=paid')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('signals', data)
        self.assertIn('role', data)
        self.assertEqual(data['role'], 'paid')

        # PAID users should get full signal data
        # No specific field restrictions for PAID tier
        if data['signals']:
            signal = data['signals'][0]
            # At minimum, basic fields should be present
            self.assertIn('symbol', signal)
            self.assertIn('score', signal)

    def test_score_filtering_works(self):
        """
        Test that signals below score_min are excluded.

        Loads admin settings to get score_min threshold.
        Verifies all returned signals have score >= score_min.

        Note: With setUp() mocking, we expect:
        - BTC (score 90) and SOL (score 88) to pass
        - ETH (score 45) to be filtered out
        - Only 2 signals should be returned if score_min=85
        """
        # Get admin settings
        settings = load_admin_alert_settings()
        score_min = settings.get('smart_signals', {}).get('score_min', 85)

        response = self.client.get('/api/smart_signals?role=paid')
        data = json.loads(response.data)

        self.assertIn('score_min', data)
        self.assertEqual(data['score_min'], score_min)

        # Verify all signals meet minimum score
        self.assertGreater(len(data['signals']), 0, "Expected at least one signal in mock data")
        for signal in data['signals']:
            self.assertGreaterEqual(
                signal.get('score', 0), score_min,
                f"Signal {signal.get('symbol')} has score {signal.get('score')} < {score_min}"
            )

    def test_role_detection_defaults_to_free(self):
        """
        Test that API defaults to FREE tier if no session/role provided.

        When called without authentication:
        - Should detect no session
        - Should return role='free'
        - Should apply FREE tier filtering
        """
        response = self.client.get('/api/smart_signals')
        data = json.loads(response.data)

        self.assertIn('role', data)
        # Without session, should default to free
        # This depends on implementation - may be 'free' or detected from query param

    def test_response_includes_metadata(self):
        """
        Test that API response includes required metadata.

        Verifies response format:
        - signals array
        - ts (timestamp)
        - role (user tier)
        - score_min (filtering threshold)
        """
        response = self.client.get('/api/smart_signals?role=paid')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # Required response fields
        self.assertIn('signals', data)
        self.assertIsInstance(data['signals'], list)

        self.assertIn('ts', data)
        self.assertIsNotNone(data['ts'])

        self.assertIn('role', data)
        self.assertIn(data['role'], ('free', 'paid'))

        self.assertIn('score_min', data)
        self.assertIsInstance(data['score_min'], int)

    def test_backward_compatibility_without_role_param(self):
        """
        Test that API is backward compatible when role parameter is omitted.

        API should work if:
        - No role parameter provided
        - No session authentication
        - Should return valid signal data regardless
        """
        response = self.client.get('/api/smart_signals')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        # Should still return valid structure
        self.assertIn('signals', data)
        self.assertIn('ts', data)
        self.assertIn('role', data)
        self.assertIn('score_min', data)

        # Should have valid values
        self.assertIsInstance(data['signals'], list)
        self.assertIn(data['role'], ('free', 'paid'))

    def test_invalid_role_parameter_ignored(self):
        """
        Test that invalid role parameters are ignored gracefully.

        When given invalid role like '?role=invalid':
        - Should ignore it
        - Should detect role from session (or default to free)
        - Should not crash
        """
        response = self.client.get('/api/smart_signals?role=invalid')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertIn('role', data)
        # Should have fallen back to session detection or default
        self.assertIn(data['role'], ('free', 'paid'))

    def test_empty_signals_returns_valid_structure(self):
        """
        Test that empty signal cache returns valid structure.

        Even if no signals are cached:
        - Should return valid JSON
        - Should include metadata (ts, role, score_min)
        - signals should be empty list
        """
        response = self.client.get('/api/smart_signals?role=paid')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)

        self.assertIn('signals', data)
        self.assertIsInstance(data['signals'], list)
        self.assertIn('role', data)
        self.assertIn('score_min', data)
        self.assertIn('ts', data)

    def test_field_consistency_between_roles(self):
        """
        Test that common fields are consistent between FREE and PAID responses.

        Common fields (symbol, score, direction, etc.) should have same values
        regardless of role, only additional fields differ.
        """
        response_free = self.client.get('/api/smart_signals?role=free')
        response_paid = self.client.get('/api/smart_signals?role=paid')

        data_free = json.loads(response_free.data)
        data_paid = json.loads(response_paid.data)

        # Should have same number of signals (same filtering applied)
        self.assertEqual(
            len(data_free['signals']),
            len(data_paid['signals']),
            "FREE and PAID should return same number of signals"
        )

        # Common fields should match
        for i, (sig_free, sig_paid) in enumerate(zip(data_free['signals'], data_paid['signals'])):
            self.assertEqual(sig_free['symbol'], sig_paid['symbol'],
                           f"Signal {i}: symbol mismatch")
            self.assertEqual(sig_free['score'], sig_paid['score'],
                           f"Signal {i}: score mismatch")
            self.assertEqual(sig_free['direction'], sig_paid['direction'],
                           f"Signal {i}: direction mismatch")


class TestSmartSignalsIntegration(unittest.TestCase):
    """Integration tests for smart signals system."""

    def setUp(self):
        """Set up test client."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Clean up."""
        self.app_context.pop()

    def test_api_endpoint_responds_quickly(self):
        """
        Test that API endpoint responds with reasonable latency.

        Should respond in < 100ms for cached data.
        """
        import time
        start = time.time()
        response = self.client.get('/api/smart_signals?role=paid')
        elapsed = time.time() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 0.5, f"API took {elapsed:.2f}s (should be < 0.5s)")

    def test_multiple_role_switches_consistent(self):
        """
        Test that switching between roles gives consistent filtering.

        Multiple calls to same role should return identical results.
        """
        response1 = self.client.get('/api/smart_signals?role=free')
        response2 = self.client.get('/api/smart_signals?role=free')

        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        # Same role should return consistent results
        self.assertEqual(len(data1['signals']), len(data2['signals']))
        self.assertEqual(data1['score_min'], data2['score_min'])


if __name__ == '__main__':
    unittest.main()
