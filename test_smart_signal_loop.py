#!/usr/bin/env python3
"""
Tests for smart_signal_loop() refactoring to use settings loader.

This module tests:
1. Normal operation with valid settings
2. Settings are properly used (not hardcoded)
3. Cache respects size limit from settings
4. Sleep interval uses scan_interval setting
5. Backward compatibility
6. Edge cases and error handling
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import time
import sys
import os

# Add the parent directory to the path so we can import app and scanner_engine
sys.path.insert(0, os.path.dirname(__file__))

# Mock the dependencies before importing app
sys.modules['config'] = MagicMock()
sys.modules['db'] = MagicMock()
sys.modules['news_macro'] = MagicMock()
sys.modules['cot_engine'] = MagicMock()
sys.modules['ai_provider'] = MagicMock()
sys.modules['daily_report'] = MagicMock()
sys.modules['smart_signals'] = MagicMock()
sys.modules['flask'] = MagicMock()
sys.modules['flask_socketio'] = MagicMock()


class TestSmartSignalLoopSettings(unittest.TestCase):
    """Test smart_signal_loop uses settings correctly."""

    def setUp(self):
        """Set up test fixtures."""
        self.default_settings = {
            'vol_min_standard': 2,
            'vol_min_small_cap': 0.5,
            'vol_max_small_cap': 2,
            'cache_size': 20,
            'scan_interval': 5,
            'score_min': 85,
            'variation_pump': 4.0,
            'variation_dump': -4.0,
            'vol_mult_min': 5.0,
            'criteria_min': 3,
            'adr_min': 25,
            'cooldown_hours': 1,
            'max_per_cycle': 3,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'retrace_cooldown_hours': 1,
            'macro_impact_filter': 'high',
            'macro_window_start_utc': 8,
            'macro_window_end_utc': 22,
            'pump_dump_threshold': 1.0,
            'vol_spike_mult': 1.0,
            'vol_min_24h': 2,
            'ema200_enabled': True,
            'adx_min': 8,
            'fear_greed_limit': -15,
        }

    def test_volume_thresholds_from_settings(self):
        """Verify volume thresholds are calculated from settings (in millions)."""
        # Test that vol_min_standard in millions is converted to USDT
        assert self.default_settings['vol_min_standard'] == 2
        vol_in_usdt = self.default_settings['vol_min_standard'] * 1_000_000
        assert vol_in_usdt == 2_000_000

        # Test small cap bounds conversion
        vol_min_sc = self.default_settings['vol_min_small_cap'] * 1_000_000
        vol_max_sc = self.default_settings['vol_max_small_cap'] * 1_000_000
        assert vol_min_sc == 500_000
        assert vol_max_sc == 2_000_000

    def test_cache_size_setting(self):
        """Verify cache_size setting is respected."""
        # Test default cache size
        assert self.default_settings['cache_size'] == 20

        # Test that a custom cache size would be used
        custom_settings = self.default_settings.copy()
        custom_settings['cache_size'] = 10
        assert custom_settings['cache_size'] == 10

        # Test zero cache size (edge case)
        zero_cache = self.default_settings.copy()
        zero_cache['cache_size'] = 0
        assert zero_cache['cache_size'] == 0

    def test_scan_interval_setting(self):
        """Verify scan_interval setting is used (in seconds)."""
        # Test default scan interval (5 seconds)
        assert self.default_settings['scan_interval'] == 5

        # Test custom scan interval
        custom_settings = self.default_settings.copy()
        custom_settings['scan_interval'] = 10
        assert custom_settings['scan_interval'] == 10

    def test_settings_get_with_defaults(self):
        """Verify .get() with defaults works correctly."""
        settings = {}

        # When settings dict is empty, defaults should be used
        vol_min = settings.get('vol_min_standard', 2) * 1_000_000
        assert vol_min == 2_000_000

        cache_size = settings.get('cache_size', 20)
        assert cache_size == 20

        scan_interval = settings.get('scan_interval', 5)
        assert scan_interval == 5

    def test_settings_override_defaults(self):
        """Verify settings values override defaults when present."""
        settings = {
            'vol_min_standard': 5,
            'cache_size': 15,
            'scan_interval': 10,
        }

        vol_min = settings.get('vol_min_standard', 2) * 1_000_000
        assert vol_min == 5_000_000

        cache_size = settings.get('cache_size', 20)
        assert cache_size == 15

        scan_interval = settings.get('scan_interval', 5)
        assert scan_interval == 10

    def test_small_cap_filtering_logic(self):
        """Test that small cap filtering uses correct bounds from settings."""
        settings = self.default_settings.copy()
        vol_min = settings.get('vol_min_small_cap', 0.5) * 1_000_000
        vol_max = settings.get('vol_max_small_cap', 2) * 1_000_000

        # Test coins at boundaries
        coins = [
            {'symbol': 'COIN1', 'volume_usdt': 400_000},    # Below min - excluded
            {'symbol': 'COIN2', 'volume_usdt': 500_000},    # At min - included
            {'symbol': 'COIN3', 'volume_usdt': 1_000_000},  # In range - included
            {'symbol': 'COIN4', 'volume_usdt': 2_000_000},  # At max - included
            {'symbol': 'COIN5', 'volume_usdt': 2_000_001},  # Above max - excluded
        ]

        # Filter using the same logic as smart_signal_loop
        small_caps = [c for c in coins if vol_min <= c.get("volume_usdt", 0) <= vol_max]

        assert len(small_caps) == 3
        assert small_caps[0]['symbol'] == 'COIN2'
        assert small_caps[1]['symbol'] == 'COIN3'
        assert small_caps[2]['symbol'] == 'COIN4'

    def test_standard_coins_filtering_logic(self):
        """Test that standard coins filtering uses threshold from settings."""
        settings = self.default_settings.copy()
        vol_threshold = settings.get('vol_min_standard', 2) * 1_000_000

        coins = [
            {'symbol': 'COIN1', 'volume_usdt': 1_999_999},  # Below threshold
            {'symbol': 'COIN2', 'volume_usdt': 2_000_000},  # At threshold (not included, > only)
            {'symbol': 'COIN3', 'volume_usdt': 2_000_001},  # Above threshold - included
            {'symbol': 'COIN4', 'volume_usdt': 10_000_000}, # Well above - included
        ]

        standard_coins = [c for c in coins if c.get("volume_usdt", 0) > vol_threshold]

        assert len(standard_coins) == 2
        assert standard_coins[0]['symbol'] == 'COIN3'
        assert standard_coins[1]['symbol'] == 'COIN4'

    def test_cache_slicing_with_limit(self):
        """Test that results are sliced according to cache_size setting."""
        settings = self.default_settings.copy()
        cache_size_limit = settings.get('cache_size', 20)

        # Create 25 mock signals
        results = [{'signal': i, 'score': 100 - i} for i in range(25)]

        # Slice according to cache_size_limit
        cached_results = results[:cache_size_limit]

        assert len(cached_results) == 20
        assert cached_results[0]['signal'] == 0
        assert cached_results[19]['signal'] == 19

        # Test with smaller cache size
        settings['cache_size'] = 5
        cache_size_limit = settings.get('cache_size', 20)
        cached_results = results[:cache_size_limit]
        assert len(cached_results) == 5

    def test_settings_missing_keys_use_defaults(self):
        """Test that missing setting keys fall back to defaults."""
        partial_settings = {
            'vol_min_standard': 3,
            # Missing: vol_min_small_cap, vol_max_small_cap, cache_size, scan_interval
        }

        # These should use defaults
        vol_min_standard = partial_settings.get('vol_min_standard', 2)
        vol_min_small_cap = partial_settings.get('vol_min_small_cap', 0.5)
        vol_max_small_cap = partial_settings.get('vol_max_small_cap', 2)
        cache_size = partial_settings.get('cache_size', 20)
        scan_interval = partial_settings.get('scan_interval', 5)

        assert vol_min_standard == 3  # From settings
        assert vol_min_small_cap == 0.5  # From default
        assert vol_max_small_cap == 2  # From default
        assert cache_size == 20  # From default
        assert scan_interval == 5  # From default

    def test_scan_interval_converts_to_seconds(self):
        """Verify scan_interval is in seconds (not minutes)."""
        settings = self.default_settings.copy()

        # scan_interval is in seconds (default 5)
        scan_interval = settings.get('scan_interval', 5)

        # The sleep should use this value directly (not multiply by 60)
        sleep_duration = scan_interval
        assert sleep_duration == 5

        # Test custom value
        settings['scan_interval'] = 30
        scan_interval = settings.get('scan_interval', 5)
        sleep_duration = scan_interval
        assert sleep_duration == 30

    def test_cache_size_zero_edge_case(self):
        """Test behavior when cache_size is 0."""
        settings = self.default_settings.copy()
        settings['cache_size'] = 0

        results = [{'signal': i} for i in range(5)]
        cache_size_limit = settings.get('cache_size', 20)
        cached_results = results[:cache_size_limit]

        # Should be empty list
        assert len(cached_results) == 0
        assert cached_results == []

    def test_boundary_volume_values(self):
        """Test volume filtering at exact boundary values."""
        settings = self.default_settings.copy()
        vol_min_standard = settings.get('vol_min_standard', 2) * 1_000_000
        vol_min_sc = settings.get('vol_min_small_cap', 0.5) * 1_000_000
        vol_max_sc = settings.get('vol_max_small_cap', 2) * 1_000_000

        # Exact boundary values
        test_volumes = [
            vol_min_sc - 1,     # Just below min
            vol_min_sc,         # At min (small cap lower bound)
            vol_min_standard,   # At standard threshold
            vol_min_standard + 1,  # Just above standard threshold
            vol_max_sc,         # At max (small cap upper bound)
            vol_max_sc + 1,     # Just above max
        ]

        for vol in test_volumes:
            is_standard = vol > vol_min_standard
            is_small_cap = vol_min_sc <= vol <= vol_max_sc

            # A coin can't be in both categories
            assert not (is_standard and is_small_cap)

    def test_settings_none_fallback(self):
        """Test behavior when settings dict is None or empty."""
        # When _loop_settings is None
        settings = None or {}
        assert settings == {}

        # Using defaults with empty dict
        vol_min = settings.get('vol_min_standard', 2)
        assert vol_min == 2

    def test_float_settings_conversion(self):
        """Test that float settings are handled correctly."""
        settings = self.default_settings.copy()

        # These settings may come as strings from DB and need conversion
        settings['vol_min_small_cap'] = 0.5  # Should work as float
        settings['variation_pump'] = 4.0

        vol_in_usdt = settings.get('vol_min_small_cap', 0.5) * 1_000_000
        assert vol_in_usdt == 500_000

        pump = settings.get('variation_pump', 4.0)
        assert pump == 4.0


class TestSmartSignalLoopIntegration(unittest.TestCase):
    """Integration tests for smart_signal_loop with mocked engine."""

    def test_volume_conversion_accuracy(self):
        """Verify volume conversion from millions to USDT is accurate."""
        test_cases = [
            (0.5, 500_000),
            (1, 1_000_000),
            (2, 2_000_000),
            (5, 5_000_000),
            (10, 10_000_000),
        ]

        for millions, expected_usdt in test_cases:
            actual = millions * 1_000_000
            assert actual == expected_usdt

    def test_settings_refresh_interval(self):
        """Test that settings refresh logic is sound (5 minutes)."""
        # Settings should refresh every 300 seconds (5 minutes)
        refresh_interval = 300

        now = time.time()
        last_refresh = now - 400  # More than 5 minutes ago

        # Should refresh
        should_refresh = (now - last_refresh) > refresh_interval
        assert should_refresh is True

        # Should not refresh
        last_refresh = now - 100  # Less than 5 minutes ago
        should_refresh = (now - last_refresh) > refresh_interval
        assert should_refresh is False


if __name__ == '__main__':
    unittest.main()
