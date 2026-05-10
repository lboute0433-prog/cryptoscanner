"""
Test-Driven Development for load_admin_alert_settings()
Tests the centralized function that loads ADMIN parameters from database.
"""

import pytest
import sqlite3
from unittest.mock import patch, MagicMock
from scanner_engine import load_admin_alert_settings


class TestLoadAdminAlertSettings:
    """Test suite for load_admin_alert_settings() function"""

    def test_returns_dict_with_all_required_keys(self):
        """Function should return a dict containing all required configuration keys"""
        result = load_admin_alert_settings()

        # SMART SIGNALS Block
        assert "score_min" in result
        assert "variation_pump" in result
        assert "variation_dump" in result
        assert "vol_mult_min" in result
        assert "criteria_min" in result
        assert "adr_min" in result
        assert "cooldown_hours" in result
        assert "max_per_cycle" in result

        # RETRACE RSI Block
        assert "rsi_oversold" in result
        assert "rsi_overbought" in result
        assert "retrace_cooldown_hours" in result

        # MACRO EVENTS Block
        assert "macro_impact_filter" in result
        assert "macro_window_start_utc" in result
        assert "macro_window_end_utc" in result

        # PLATEFORME Block
        assert "pump_dump_threshold" in result
        assert "scan_interval" in result
        assert "vol_spike_mult" in result
        assert "vol_min_24h" in result
        assert "ema200_enabled" in result
        assert "adx_min" in result
        assert "fear_greed_limit" in result
        assert "cache_size" in result

    def test_returns_defaults_when_db_empty(self):
        """Function should return default values when database has no settings"""
        with patch('scanner_engine.get_setting') as mock_get:
            # All DB calls return empty string (no value set)
            mock_get.return_value = ""

            result = load_admin_alert_settings()

            # Verify defaults for SMART SIGNALS
            assert result["score_min"] == 85
            assert result["variation_pump"] == 4.0
            assert result["variation_dump"] == -4.0
            assert result["vol_mult_min"] == 5.0
            assert result["criteria_min"] == 3
            assert result["adr_min"] == 25
            assert result["cooldown_hours"] == 1
            assert result["max_per_cycle"] == 3

            # Verify defaults for RETRACE RSI
            assert result["rsi_oversold"] == 30
            assert result["rsi_overbought"] == 70
            assert result["retrace_cooldown_hours"] == 1

            # Verify defaults for MACRO EVENTS
            assert result["macro_impact_filter"] == "high"
            assert result["macro_window_start_utc"] == 8
            assert result["macro_window_end_utc"] == 22

            # Verify defaults for PLATEFORME
            assert result["pump_dump_threshold"] == 1.0
            assert result["scan_interval"] == 5
            assert result["vol_spike_mult"] == 1.0
            assert result["vol_min_24h"] == 2
            assert result["ema200_enabled"] is True
            assert result["adx_min"] == 8
            assert result["fear_greed_limit"] == -15
            assert result["cache_size"] == 20

    def test_handles_db_connection_error_gracefully(self):
        """Function should return defaults if database connection fails"""
        with patch('scanner_engine.get_setting') as mock_get:
            # Simulate database error
            mock_get.side_effect = Exception("Database connection failed")

            result = load_admin_alert_settings()

            # Should still return defaults, not crash
            assert isinstance(result, dict)
            assert len(result) > 0
            assert result["score_min"] == 85

    def test_loads_custom_values_from_database(self):
        """Function should load and use custom values from database when available"""
        custom_values = {
            "score_min": "95",
            "variation_pump": "5.5",
            "rsi_oversold": "25",
            "pump_dump_threshold": "2.5"
        }

        def mock_get_setting(key, default):
            return custom_values.get(key, default)

        with patch('scanner_engine.get_setting', side_effect=mock_get_setting):
            result = load_admin_alert_settings()

            # Verify custom values are loaded
            assert result["score_min"] == 95
            assert result["variation_pump"] == 5.5
            assert result["rsi_oversold"] == 25
            assert result["pump_dump_threshold"] == 2.5

    def test_type_conversion_for_numeric_values(self):
        """Function should properly convert string values from DB to appropriate types"""
        with patch('scanner_engine.get_setting') as mock_get:
            def side_effect(key, default):
                values = {
                    "score_min": "100",
                    "vol_mult_min": "7.5",
                    "criteria_min": "5",
                    "retrace_cooldown_hours": "2"
                }
                return values.get(key, default)

            mock_get.side_effect = side_effect
            result = load_admin_alert_settings()

            # Verify types
            assert isinstance(result["score_min"], (int, float))
            assert isinstance(result["vol_mult_min"], float)
            assert isinstance(result["criteria_min"], int)
            assert isinstance(result["retrace_cooldown_hours"], int)

    def test_type_conversion_for_boolean_values(self):
        """Function should properly convert string values to booleans"""
        with patch('scanner_engine.get_setting') as mock_get:
            def side_effect(key, default):
                values = {
                    "ema200_enabled": "False",
                }
                return values.get(key, default)

            mock_get.side_effect = side_effect
            result = load_admin_alert_settings()

            assert isinstance(result["ema200_enabled"], bool)
            assert result["ema200_enabled"] is False

    def test_handles_invalid_numeric_values(self):
        """Function should fall back to defaults for invalid numeric conversions"""
        with patch('scanner_engine.get_setting') as mock_get:
            def side_effect(key, default):
                values = {
                    "score_min": "invalid_number",
                    "vol_mult_min": "not_a_float"
                }
                return values.get(key, default)

            mock_get.side_effect = side_effect
            result = load_admin_alert_settings()

            # Should fall back to defaults
            assert result["score_min"] == 85
            assert result["vol_mult_min"] == 5.0

    def test_function_is_importable(self):
        """Function should be importable from scanner_engine module"""
        from scanner_engine import load_admin_alert_settings as func
        assert callable(func)

    def test_all_values_are_proper_types(self):
        """All returned values should be correct types (int, float, str, bool)"""
        result = load_admin_alert_settings()

        for key, value in result.items():
            assert isinstance(value, (int, float, str, bool)), \
                f"Key '{key}' has unexpected type: {type(value)}"

    def test_function_has_docstring(self):
        """Function should have a comprehensive docstring"""
        assert load_admin_alert_settings.__doc__ is not None
        assert len(load_admin_alert_settings.__doc__) > 50

    def test_function_has_type_hints(self):
        """Function should have type hints"""
        import inspect
        sig = inspect.signature(load_admin_alert_settings)
        # Check return annotation exists
        assert sig.return_annotation != inspect.Signature.empty


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
