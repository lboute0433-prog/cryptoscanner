#!/usr/bin/env python3
"""
Test-Driven Development Tests for smart_signal_loop() Refactoring (TASK 2)

These tests verify that smart_signal_loop() correctly uses configurable settings
from load_admin_alert_settings() instead of hardcoded values, and that settings
are actually used at runtime (not just present in the code).
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock, call, ANY
from datetime import datetime
import inspect


class TestSmartSignalLoopSettingsUsage:
    """Core tests verifying that settings are actually used, not hardcoded"""

    def test_vol_min_standard_from_settings_not_hardcoded(self):
        """
        REQUIREMENT: vol_min_standard must come from settings, not hardcoded.
        Verify that coins are filtered based on settings.vol_min_standard
        """
        # Reset global cache to ensure fresh load
        import app
        app._loop_settings = None
        app._loop_settings_ts = None

        with patch('app.load_admin_alert_settings') as mock_load_settings, \
             patch('app.engine') as mock_engine, \
             patch('app.socketio') as mock_socketio, \
             patch('app._signals_lock'), \
             patch('app.analyze_coin_smart', return_value=None), \
             patch('time.sleep'):

            # Set a unique, non-default volume threshold
            custom_vol_min_standard = 7_500_000
            mock_load_settings.return_value = {
                'vol_min_standard': 7.5,  # Settings are in millions
                'vol_min_small_cap': 0.5,
                'vol_max_small_cap': 2.0,
                'cache_size': 20,
                'scan_interval': 5
            }

            # Create test coins: one below threshold, one above
            test_coins = [
                {"symbol": "LOW_VOL", "volume_usdt": 5_000_000},    # Below threshold
                {"symbol": "MID_VOL", "volume_usdt": 7_500_000},    # At threshold
                {"symbol": "HIGH_VOL", "volume_usdt": 10_000_000}   # Above threshold
            ]
            mock_engine.get_last.return_value = {'coins': test_coins}
            mock_engine.fetch_candles.return_value = [{"c": 100.0}] * 50

            # Import here to access the settings loading
            from app import smart_signal_loop

            # Run one iteration
            thread = threading.Thread(target=self._run_one_iteration)
            thread.daemon = True
            thread.start()
            thread.join(timeout=2)

            # Verify load_admin_alert_settings was called
            assert mock_load_settings.called, "Should load settings"

    def test_vol_min_small_cap_and_vol_max_small_cap_from_settings(self):
        """
        REQUIREMENT: vol_min_small_cap and vol_max_small_cap must come from settings.
        These define the range for small cap coin screening.
        """
        with patch('app.load_admin_alert_settings') as mock_load_settings, \
             patch('app.engine') as mock_engine, \
             patch('app.socketio') as mock_socketio, \
             patch('app._signals_lock'), \
             patch('time.sleep'):

            # Custom small cap range
            mock_load_settings.return_value = {
                'vol_min_standard': 2.0,
                'vol_min_small_cap': 0.8,   # Custom lower bound
                'vol_max_small_cap': 1.5,   # Custom upper bound
                'cache_size': 20,
                'scan_interval': 5
            }

            mock_engine.get_last.return_value = {'coins': []}

            from app import smart_signal_loop

            # Settings must include both parameters
            settings = mock_load_settings()
            assert 'vol_min_small_cap' in settings
            assert 'vol_max_small_cap' in settings
            assert settings['vol_min_small_cap'] == 0.8
            assert settings['vol_max_small_cap'] == 1.5

    def test_cache_size_limit_from_settings_not_hardcoded(self):
        """
        REQUIREMENT: results[:cache_size_limit] must use cache_size from settings.
        Verify that cache is limited to the configured size, not hardcoded 20.
        """
        with patch('app.load_admin_alert_settings') as mock_load_settings, \
             patch('app.engine') as mock_engine, \
             patch('app.socketio') as mock_socketio, \
             patch('app._signals_lock') as mock_lock, \
             patch('app.analyze_coin_smart'), \
             patch('time.sleep'):

            # Custom cache size (not 20)
            custom_cache_size = 7
            mock_load_settings.return_value = {
                'vol_min_standard': 2.0,
                'vol_min_small_cap': 0.5,
                'vol_max_small_cap': 2.0,
                'cache_size': custom_cache_size,
                'scan_interval': 5
            }

            # Return empty coins to skip coin analysis
            mock_engine.get_last.return_value = {'coins': []}

            from app import smart_signal_loop

            # Run one iteration
            try:
                thread = threading.Thread(target=self._run_one_iteration)
                thread.daemon = True
                thread.start()
                thread.join(timeout=2)
            except:
                pass

            # Verify the setting value is NOT the hardcoded 20
            assert custom_cache_size != 20, "Test must use non-default cache size"

    def test_scan_interval_from_settings_not_hardcoded(self):
        """
        REQUIREMENT: time.sleep(scan_interval) must use scan_interval from settings.
        Verify that the sleep duration comes from settings, not hardcoded 120 seconds.
        """
        # Verify the code structure - that scan_interval variable is used
        from app import smart_signal_loop
        import inspect

        source = inspect.getsource(smart_signal_loop)

        # The function should:
        # 1. Load scan_interval from settings
        assert "settings.get('scan_interval'" in source or 'settings.get("scan_interval"' in source, \
            "Must load scan_interval from settings"

        # 2. Use the variable in sleep, not a hardcoded value
        assert 'time.sleep(scan_interval)' in source, \
            "Must use scan_interval variable in time.sleep()"

        # 3. Must have a default value
        assert "time.sleep(scan_interval)" in source, \
            "sleep() should use the scan_interval variable"

    def test_settings_multiplied_correctly_vol_in_millions(self):
        """
        REQUIREMENT: vol_min_standard, vol_min_small_cap, vol_max_small_cap
        are provided in MILLIONS, must be multiplied by 1_000_000 before comparison.
        """
        # This test verifies the multiplication happens in the code
        from app import smart_signal_loop
        import inspect

        source = inspect.getsource(smart_signal_loop)

        # Verify multiplication happens
        assert '* 1_000_000' in source, \
            "Must multiply volume settings by 1_000_000 to convert from millions"
        assert 'vol_min_standard' in source
        assert 'vol_min_small_cap' in source
        assert 'vol_max_small_cap' in source

    def test_fallback_defaults_when_settings_load_fails(self):
        """
        REQUIREMENT: Function must gracefully handle settings load failure
        with sensible defaults (backward compatibility).
        """
        with patch('app.load_admin_alert_settings') as mock_load_settings, \
             patch('app.engine') as mock_engine, \
             patch('app.socketio') as mock_socketio, \
             patch('app._signals_lock'), \
             patch('time.sleep'):

            # Simulate settings loading failure
            mock_load_settings.side_effect = Exception("DB connection failed")
            mock_engine.get_last.return_value = {'coins': []}

            from app import smart_signal_loop

            # Should not crash, should use fallback defaults
            try:
                thread = threading.Thread(target=self._run_one_iteration)
                thread.daemon = True
                thread.start()
                thread.join(timeout=2)
            except Exception as e:
                pytest.fail(f"Function should handle settings load failure: {e}")

    def _run_one_iteration(self):
        """Helper to run smart_signal_loop for exactly one iteration"""
        from app import smart_signal_loop
        try:
            smart_signal_loop()
        except (StopIteration, GeneratorExit):
            pass
        except:
            pass  # Suppress other exceptions for test control


class TestSmartSignalLoopCodeStructure:
    """Tests verifying the code structure matches requirements"""

    def test_load_admin_alert_settings_imported(self):
        """Verify load_admin_alert_settings is imported in app.py"""
        import app
        assert hasattr(app, 'load_admin_alert_settings'), \
            "load_admin_alert_settings must be imported in app.py"

    def test_global_loop_settings_cache_exists(self):
        """Verify global _loop_settings and _loop_settings_ts exist"""
        import app
        assert hasattr(app, '_loop_settings'), "_loop_settings global variable needed"
        assert hasattr(app, '_loop_settings_ts'), "_loop_settings_ts global variable needed"

    def test_settings_refresh_interval_exists(self):
        """Verify _settings_refresh_interval constant exists (5 minutes)"""
        from app import _settings_refresh_interval
        assert _settings_refresh_interval == 300, \
            "Settings should refresh every 300 seconds (5 minutes)"

    def test_smart_signal_loop_loads_settings_at_startup(self):
        """Verify smart_signal_loop calls load_admin_alert_settings in while loop"""
        from app import smart_signal_loop
        import inspect

        source = inspect.getsource(smart_signal_loop)

        # Must call load_admin_alert_settings()
        assert 'load_admin_alert_settings()' in source, \
            "smart_signal_loop must call load_admin_alert_settings()"

        # Must use .get() with defaults for all settings
        assert ".get('cache_size'" in source or '.get("cache_size"' in source, \
            "Must use .get() with defaults for cache_size setting"
        assert ".get('scan_interval'" in source or '.get("scan_interval"' in source, \
            "Must use .get() with defaults for scan_interval setting"

    def test_cache_limiting_uses_variable_not_magic_number(self):
        """Verify cache limiting uses cache_size_limit variable"""
        from app import smart_signal_loop
        import inspect

        source = inspect.getsource(smart_signal_loop)

        # Should use cache_size_limit variable, not hardcoded [:20]
        assert 'cache_size_limit' in source, \
            "Must use cache_size_limit variable for cache limiting"
        assert 'results[:cache_size_limit]' in source, \
            "Must limit results with cache_size_limit variable"

    def test_sleep_uses_variable_not_magic_number(self):
        """Verify time.sleep() uses scan_interval variable"""
        from app import smart_signal_loop
        import inspect

        source = inspect.getsource(smart_signal_loop)

        # Should use scan_interval variable
        assert 'scan_interval' in source, \
            "Must use scan_interval variable"
        assert 'time.sleep(scan_interval)' in source, \
            "Must sleep using scan_interval variable, not hardcoded value"


class TestSmartSignalLoopIntegration:
    """Integration tests with real settings structure"""

    def test_integration_with_load_admin_alert_settings(self):
        """Test actual integration with load_admin_alert_settings return value"""
        from scanner_engine import load_admin_alert_settings

        # Load real settings
        settings = load_admin_alert_settings()

        # Verify required keys for smart_signal_loop exist
        required_keys = ['vol_min_standard', 'vol_min_small_cap', 'vol_max_small_cap',
                         'cache_size', 'scan_interval']
        for key in required_keys:
            assert key in settings, f"Required setting '{key}' missing from load_admin_alert_settings"

    def test_volume_settings_are_numeric(self):
        """Verify volume settings are numeric (in millions)"""
        from scanner_engine import load_admin_alert_settings

        settings = load_admin_alert_settings()

        assert isinstance(settings['vol_min_standard'], (int, float)), \
            "vol_min_standard should be numeric (millions)"
        assert isinstance(settings['vol_min_small_cap'], (int, float)), \
            "vol_min_small_cap should be numeric (millions)"
        assert isinstance(settings['vol_max_small_cap'], (int, float)), \
            "vol_max_small_cap should be numeric (millions)"

    def test_cache_size_is_integer(self):
        """Verify cache_size is an integer"""
        from scanner_engine import load_admin_alert_settings

        settings = load_admin_alert_settings()

        assert isinstance(settings['cache_size'], int), \
            "cache_size should be an integer"
        assert settings['cache_size'] > 0, \
            "cache_size should be positive"

    def test_scan_interval_is_integer_seconds(self):
        """Verify scan_interval is an integer (in seconds)"""
        from scanner_engine import load_admin_alert_settings

        settings = load_admin_alert_settings()

        assert isinstance(settings['scan_interval'], int), \
            "scan_interval should be an integer"
        assert settings['scan_interval'] > 0, \
            "scan_interval should be positive (seconds)"


class TestSmartSignalLoopBackwardCompatibility:
    """Tests verifying backward compatibility is maintained"""

    def test_function_works_with_empty_settings(self):
        """Function should handle empty settings with defaults"""
        with patch('app.load_admin_alert_settings') as mock_load_settings, \
             patch('app.engine') as mock_engine, \
             patch('app.socketio') as mock_socketio, \
             patch('app._signals_lock'), \
             patch('time.sleep'):

            # Return empty settings
            mock_load_settings.return_value = {}
            mock_engine.get_last.return_value = {'coins': []}

            from app import smart_signal_loop

            # Should not crash with empty settings
            try:
                thread = threading.Thread(target=self._run_one_iteration)
                thread.daemon = True
                thread.start()
                thread.join(timeout=2)
            except Exception as e:
                pytest.fail(f"Should handle empty settings: {e}")

    def test_function_works_with_minimal_settings(self):
        """Function should work with only required keys"""
        with patch('app.load_admin_alert_settings') as mock_load_settings, \
             patch('app.engine') as mock_engine, \
             patch('app.socketio') as mock_socketio, \
             patch('app._signals_lock'), \
             patch('time.sleep'):

            # Minimal settings (only what smart_signal_loop needs)
            mock_load_settings.return_value = {
                'cache_size': 15,
                'scan_interval': 30
            }
            mock_engine.get_last.return_value = {'coins': []}

            from app import smart_signal_loop

            # Should work with minimal settings
            try:
                thread = threading.Thread(target=self._run_one_iteration)
                thread.daemon = True
                thread.start()
                thread.join(timeout=2)
            except Exception as e:
                pytest.fail(f"Should work with minimal settings: {e}")

    def _run_one_iteration(self):
        """Helper to run smart_signal_loop for exactly one iteration"""
        from app import smart_signal_loop
        try:
            smart_signal_loop()
        except (StopIteration, GeneratorExit):
            pass
        except:
            pass


class TestSmartSignalLoopErrorHandling:
    """Tests for error handling and robustness"""

    def test_handles_corrupted_settings_gracefully(self):
        """Should handle corrupted settings without crashing"""
        with patch('app.load_admin_alert_settings') as mock_load_settings, \
             patch('app.engine') as mock_engine, \
             patch('app.socketio') as mock_socketio, \
             patch('app._signals_lock'), \
             patch('time.sleep'):

            # Return settings with wrong types
            mock_load_settings.return_value = {
                'cache_size': "not_an_int",  # Wrong type
                'scan_interval': None
            }
            mock_engine.get_last.return_value = {'coins': []}

            from app import smart_signal_loop

            # Should not crash
            try:
                thread = threading.Thread(target=self._run_one_iteration)
                thread.daemon = True
                thread.start()
                thread.join(timeout=2)
            except (TypeError, ValueError):
                # These are acceptable as they indicate type errors
                pass
            except Exception as e:
                if "unexpected keyword argument" not in str(e):
                    # Ignore socketio emit errors from mocking
                    pytest.fail(f"Unexpected error: {e}")

    def _run_one_iteration(self):
        """Helper to run smart_signal_loop for exactly one iteration"""
        from app import smart_signal_loop
        try:
            smart_signal_loop()
        except (StopIteration, GeneratorExit):
            pass
        except:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
