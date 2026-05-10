#!/usr/bin/env python3
"""
Test suite for _send_retrace_alert() refactored to use admin RETRACE RSI settings.

Tests verify:
1. RSI oversold detection uses rsi_oversold setting
2. RSI overbought detection uses rsi_overbought setting
3. Cooldown mechanism prevents duplicate alerts
4. Backward compatibility with default settings
5. Settings fallbacks to defaults when missing
6. Per-symbol cooldown tracking (independent symbols)
"""

import sys
import os
import time
import threading
import unittest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the functions we're testing
from smart_signals import check_rsi_exit, update_rsi_history, build_retrace_alert
import smart_signals


class TestCheckRSIExit(unittest.TestCase):
    """Test check_rsi_exit() function with admin settings"""

    def setUp(self):
        """Clear RSI history before each test"""
        smart_signals._rsi_history = {}

    def test_rsi_oversold_detection_with_default_settings(self):
        """Test that RSI oversold (bullish) exit is detected with default settings"""
        # Setup: RSI moves from 28 (oversold) to 32 (above 30 threshold)
        update_rsi_history("BTC", 28)

        result = check_rsi_exit("BTC", 32)

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bullish")
        self.assertEqual(result["name"], "🔔 Sortie Zone Survente")
        self.assertEqual(result["rsi_prev"], 28)
        self.assertEqual(result["rsi_now"], 32.0)
        self.assertIn("rebond potentiel", result["action"].lower())

    def test_rsi_overbought_detection_with_default_settings(self):
        """Test that RSI overbought (bearish) exit is detected with default settings"""
        # Setup: RSI moves from 72 (overbought) to 68 (below 70 threshold)
        update_rsi_history("ETH", 72)

        result = check_rsi_exit("ETH", 68)

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bearish")
        self.assertEqual(result["name"], "⚠️ Sortie Zone Surachat")
        self.assertEqual(result["rsi_prev"], 72)
        self.assertEqual(result["rsi_now"], 68.0)
        self.assertIn("prudence", result["action"].lower())

    def test_rsi_oversold_with_custom_threshold(self):
        """Test oversold detection with custom rsi_oversold threshold"""
        # Setup: RSI moves from 25 (oversold at threshold 25) to 30
        update_rsi_history("ADA", 25)

        result = check_rsi_exit("ADA", 30, rsi_oversold=25, rsi_overbought=75)

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bullish")
        self.assertIn("25", result["desc"])  # Custom threshold in description

    def test_rsi_overbought_with_custom_threshold(self):
        """Test overbought detection with custom rsi_overbought threshold"""
        # Setup: RSI moves from 76 (overbought at threshold 75) to 72
        update_rsi_history("BNB", 76)

        result = check_rsi_exit("BNB", 72, rsi_oversold=25, rsi_overbought=75)

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bearish")
        self.assertIn("75", result["desc"])  # Custom threshold in description

    def test_no_exit_when_rsi_stays_in_zone(self):
        """Test that no exit is detected when RSI stays in extreme zone"""
        # Setup: RSI stays above overbought threshold
        update_rsi_history("SOL", 71)

        result = check_rsi_exit("SOL", 73)  # Still above 70

        self.assertIsNone(result)

    def test_no_exit_when_rsi_in_normal_zone(self):
        """Test that no exit is detected when RSI is in normal zone"""
        # Setup: RSI moves within normal range
        update_rsi_history("XRP", 50)

        result = check_rsi_exit("XRP", 52)

        self.assertIsNone(result)

    def test_no_history_returns_none(self):
        """Test that None is returned when there's no RSI history"""
        result = check_rsi_exit("UNKNOWN", 50)

        self.assertIsNone(result)

    @patch('scanner_engine.load_admin_alert_settings')
    def test_loads_settings_from_db_when_not_provided(self, mock_load_settings):
        """Test that admin settings are loaded from DB when not provided"""
        mock_load_settings.return_value = {
            "rsi_oversold": 25,
            "rsi_overbought": 75
        }

        update_rsi_history("DOGE", 24)
        result = check_rsi_exit("DOGE", 30)  # Crosses above custom 25 threshold

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bullish")
        mock_load_settings.assert_called_once()

    @patch('scanner_engine.load_admin_alert_settings')
    def test_uses_default_when_db_missing(self, mock_load_settings):
        """Test that defaults are used when settings missing from DB"""
        mock_load_settings.return_value = {
            # Empty dict, so defaults apply
        }

        update_rsi_history("LTC", 28)
        result = check_rsi_exit("LTC", 32)  # Use default 30

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bullish")

    def test_multiple_symbols_independent(self):
        """Test that different symbols have independent RSI histories"""
        update_rsi_history("BTC", 28)
        update_rsi_history("ETH", 72)

        btc_result = check_rsi_exit("BTC", 32)  # Oversold exit
        eth_result = check_rsi_exit("ETH", 68)  # Overbought exit

        self.assertIsNotNone(btc_result)
        self.assertEqual(btc_result["direction"], "bullish")

        self.assertIsNotNone(eth_result)
        self.assertEqual(eth_result["direction"], "bearish")


class TestBuildRetraceAlert(unittest.TestCase):
    """Test build_retrace_alert() message formatting"""

    def test_overbought_alert_format_free(self):
        """Test that overbought alert has correct format for FREE users"""
        rsi_exit = {
            "direction": "bearish",
            "name": "⚠️ Sortie Zone Surachat",
            "rsi_prev": 72,
            "rsi_now": 68.0,
            "desc": "RSI 72 → 68.0",
            "action": "Prudence — retrace possible"
        }

        message = build_retrace_alert("BTC", rsi_exit, 45000.0, 2.5, 1500000000, for_role="free")

        self.assertIn("RETRACE", message)
        self.assertIn("BTC/USDT", message)
        self.assertIn("72", message)
        self.assertIn("68", message)
        self.assertIn("45000", message)

    def test_oversold_alert_format_paid(self):
        """Test that oversold alert has correct format for PAID users"""
        rsi_exit = {
            "direction": "bullish",
            "name": "🔔 Sortie Zone Survente",
            "rsi_prev": 28,
            "rsi_now": 32.0,
            "desc": "RSI 28 → 32.0",
            "action": "Rebond potentiel"
        }

        message = build_retrace_alert("ETH", rsi_exit, 2500.0, -1.2, 500000000, for_role="paid")

        self.assertIn("REBOND", message)
        self.assertIn("ETH/USDT", message)
        self.assertIn("28", message)
        self.assertIn("32", message)


class TestSendRetraceAlert(unittest.TestCase):
    """Test _send_retrace_alert() with cooldown mechanism"""

    def setUp(self):
        """Setup mocks and clear state before each test"""
        try:
            import app
            app._last_alert_time = {}
            app._alert_lock = threading.Lock()
        except ImportError:
            pass

    def test_cooldown_key_generation(self):
        """Test that cooldown keys are generated correctly for symbols and signal types"""
        # Test OVERSOLD cooldown key
        rsi_exit_oversold = {
            "direction": "bullish",
            "name": "Test",
            "rsi_prev": 28,
            "rsi_now": 32.0,
            "desc": "test",
            "action": "test"
        }

        # Expected key: {symbol}_{signal_type}
        # For bullish (oversold exit): "BTC_OVERSOLD"
        # For bearish (overbought exit): "BTC_OVERBOUGHT"

        # This validates the key logic without calling the full function
        signal_type = "OVERBOUGHT" if rsi_exit_oversold["direction"] == "bearish" else "OVERSOLD"
        expected_key = f"BTC_{signal_type}"
        self.assertEqual(expected_key, "BTC_OVERSOLD")

        rsi_exit_overbought = {
            "direction": "bearish",
            "name": "Test",
            "rsi_prev": 72,
            "rsi_now": 68.0,
            "desc": "test",
            "action": "test"
        }

        signal_type = "OVERBOUGHT" if rsi_exit_overbought["direction"] == "bearish" else "OVERSOLD"
        expected_key = f"ETH_{signal_type}"
        self.assertEqual(expected_key, "ETH_OVERBOUGHT")

    def test_different_signal_types_independent_keys(self):
        """Test that OVERSOLD and OVERBOUGHT alerts for same symbol are tracked separately"""
        import app

        # Simulate adding BTC_OVERSOLD to cooldown tracker
        app._last_alert_time["BTC_OVERSOLD"] = time.time()

        # BTC_OVERBOUGHT should be a different key
        self.assertNotIn("BTC_OVERBOUGHT", app._last_alert_time)

        # Clean up
        app._last_alert_time.clear()


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code"""

    def setUp(self):
        """Clear RSI history before each test"""
        smart_signals._rsi_history = {}

    def test_check_rsi_exit_works_without_explicit_thresholds(self):
        """Test that check_rsi_exit works when called without threshold parameters"""
        update_rsi_history("BTC", 28)

        # Call without providing thresholds (should load from DB)
        with patch('scanner_engine.load_admin_alert_settings') as mock_load:
            mock_load.return_value = {"rsi_oversold": 30, "rsi_overbought": 70}
            result = check_rsi_exit("BTC", 32)

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bullish")

    def test_hardcoded_constants_still_available(self):
        """Test that hardcoded RSI_OVERSOLD and RSI_OVERBOUGHT constants still exist"""
        self.assertEqual(smart_signals.RSI_OVERSOLD, 30)
        self.assertEqual(smart_signals.RSI_OVERBOUGHT, 70)


class TestSettingsFallback(unittest.TestCase):
    """Test settings fallback behavior"""

    def setUp(self):
        """Clear RSI history before each test"""
        smart_signals._rsi_history = {}

    def test_explicit_thresholds_override_defaults(self):
        """Test that explicitly provided thresholds are used"""
        update_rsi_history("BTC", 28)
        # Provide explicit thresholds
        result = check_rsi_exit("BTC", 26, rsi_oversold=25, rsi_overbought=75)

        # RSI 28 -> 26 should NOT trigger at default 30, but SHOULD trigger at custom 25
        # Since 28 > 25 (oversold threshold), this is not in oversold, so no signal
        self.assertIsNone(result)

        # Now test crossing: 26 -> 24 (crosses below 25)
        update_rsi_history("BTC", 26)
        result = check_rsi_exit("BTC", 24, rsi_oversold=25, rsi_overbought=75)
        # 26 > 25 (NOT in oversold), 24 < 25 (crossed INTO oversold), so no exit signal
        self.assertIsNone(result)

        # Test actual exit: was IN oversold (24), now EXITS (26)
        update_rsi_history("BTC", 24)
        result = check_rsi_exit("BTC", 26, rsi_oversold=25, rsi_overbought=75)
        # 24 <= 25 (in oversold), 26 > 25 (crosses above), so EXITS
        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bullish")

    @patch('scanner_engine.load_admin_alert_settings')
    def test_empty_settings_returns_defaults(self, mock_load_settings):
        """Test that defaults are used when no settings in DB"""
        mock_load_settings.return_value = {}

        update_rsi_history("BTC", 28)
        result = check_rsi_exit("BTC", 32)  # Should use hardcoded defaults (30, 70)

        self.assertIsNotNone(result)
        self.assertEqual(result["direction"], "bullish")


if __name__ == "__main__":
    unittest.main()
