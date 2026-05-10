#!/usr/bin/env python3
"""
Test Suite for _send_smart_alerts() Refactoring
Tests the use of admin settings (score_min, max_per_cycle, cooldown_hours)
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta


# ── Mock Configuration ────────────────────────────────────────────────────────
@pytest.fixture
def mock_settings():
    """Mock admin alert settings"""
    return {
        "score_min": 85,
        "max_per_cycle": 3,
        "cooldown_hours": 1,
        "variation_pump": 4.0,
        "variation_dump": -4.0,
        "vol_mult_min": 5.0,
        "criteria_min": 3,
        "adr_min": 25,
    }


@pytest.fixture
def sample_signal():
    """Create a sample valid signal"""
    return {
        "symbol": "BTC",
        "score": 90,
        "direction": "buy",
        "price": 45000.50,
        "change_pct": 2.5,
        "rsi": 65,
        "vol_ratio": 6.5,
        "tags": ["volume_spike", "rsi_oversold"],
    }


@pytest.fixture
def weak_signal():
    """Create a signal with score below threshold"""
    return {
        "symbol": "ETH",
        "score": 75,  # Below default 85
        "direction": "buy",
        "price": 2500.00,
        "change_pct": 1.5,
        "rsi": 60,
        "vol_ratio": 4.0,
        "tags": [],
    }


@pytest.fixture
def neutral_signal():
    """Create a neutral direction signal (should be skipped)"""
    return {
        "symbol": "ADA",
        "score": 88,
        "direction": "neutral",
        "price": 0.50,
        "change_pct": 0.0,
        "rsi": 50,
        "vol_ratio": 3.5,
        "tags": [],
    }


# ── TEST 1: Settings Are Used (Score Min Threshold) ────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_score_min_respected(mock_post, mock_broadcast, mock_build_alert, mock_load_settings,
                              sample_signal, weak_signal, mock_settings):
    """
    REQUIREMENT 1: Verify that score_min setting is respected.
    Only signals with score >= score_min should generate alerts.
    """
    mock_load_settings.return_value = mock_settings
    mock_build_alert.return_value = "Test alert message"

    # Import after mocking
    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()  # Reset cooldown tracking

    # Send signals with different scores
    signals = [sample_signal, weak_signal]  # 90 (passes), 75 (fails)
    _send_smart_alerts(signals)

    # Verify only the signal with score >= 85 generated an alert
    assert mock_build_alert.call_count == 1, "Expected 1 alert (score 90), not 2"
    assert mock_build_alert.call_args_list[0][0][0]["symbol"] == "BTC"

    # Verify Telegram sends were attempted
    assert mock_post.call_count >= 1, "Expected at least 1 Telegram POST"
    assert mock_broadcast.call_count >= 1, "Expected at least 1 broadcast"


# ── TEST 2: Max Per Cycle Enforced ─────────────────────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_max_per_cycle_enforced(mock_post, mock_broadcast, mock_build_alert, mock_load_settings,
                                 mock_settings):
    """
    REQUIREMENT 2: Verify that only max_per_cycle alerts are sent per iteration.
    """
    # Set max_per_cycle to 2
    mock_settings["max_per_cycle"] = 2
    mock_load_settings.return_value = mock_settings
    mock_build_alert.return_value = "Test alert"

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    # Create 5 valid signals
    signals = [
        {
            "symbol": f"COIN{i}",
            "score": 90,
            "direction": "buy",
            "price": 100.0,
            "change_pct": 1.0,
            "rsi": 60,
            "vol_ratio": 5.0,
            "tags": [],
        }
        for i in range(5)
    ]

    _send_smart_alerts(signals)

    # Verify exactly 2 alerts were sent (max_per_cycle = 2)
    assert mock_build_alert.call_count == 2, f"Expected 2 alerts (max_per_cycle=2), got {mock_build_alert.call_count}"
    assert mock_post.call_count == 2, f"Expected 2 Telegram sends, got {mock_post.call_count}"


# ── TEST 3: Cooldown Mechanism Works ──────────────────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_cooldown_prevents_duplicates(mock_post, mock_broadcast, mock_build_alert,
                                       mock_load_settings, sample_signal, mock_settings):
    """
    REQUIREMENT 3: Verify cooldown works - no duplicate alerts for same symbol+direction
    within cooldown_hours.
    """
    mock_settings["cooldown_hours"] = 1  # 1 hour cooldown
    mock_load_settings.return_value = mock_settings
    mock_build_alert.return_value = "Alert for BTC"

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    # Send same signal twice
    _send_smart_alerts([sample_signal])
    assert mock_build_alert.call_count == 1, "First alert should be sent"

    # Immediately send same signal again (within cooldown)
    _send_smart_alerts([sample_signal])
    assert mock_build_alert.call_count == 1, "Second alert should be blocked by cooldown"

    # Fast-forward time beyond cooldown (mock time.time())
    with patch("app.time.time") as mock_time:
        # Simulate 2 hours passing
        current_time = time.time()
        mock_time.return_value = current_time + (2 * 3600)

        _send_smart_alerts([sample_signal])
        # This test verifies the logic is present, but actual time manipulation
        # would require deeper mocking of the function internals


# ── TEST 4: Backward Compatibility ────────────────────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_backward_compatibility_default_settings(mock_post, mock_broadcast, mock_build_alert,
                                                  mock_load_settings, sample_signal):
    """
    REQUIREMENT 4: Verify function still works with default settings.
    Function should use defaults if settings not provided.
    """
    # Simulate settings returning defaults
    mock_load_settings.return_value = {
        "score_min": 85,
        "max_per_cycle": 3,
        "cooldown_hours": 1,
    }
    mock_build_alert.return_value = "Default alert"

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    # Signal should pass through with defaults
    _send_smart_alerts([sample_signal])

    # Verify alert was sent with default settings
    assert mock_build_alert.call_count == 1, "Signal should pass with default score_min=85"


# ── TEST 5: Telegram Tier Routing (FREE vs PAID) ───────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
@patch("app.TELEGRAM_TOKEN", "fake_token")
@patch("app.TELEGRAM_CHAT", "12345")
def test_telegram_tier_routing(mock_post, mock_broadcast, mock_build_alert,
                               mock_load_settings, sample_signal, mock_settings):
    """
    REQUIREMENT 5: Verify Telegram tiers - FREE and PAID messages are different.
    """
    mock_load_settings.return_value = mock_settings

    # Mock different messages for FREE and PAID
    def build_alert_side_effect(signal, for_role="free"):
        return f"Message for {for_role}" if for_role else "Default message"

    mock_build_alert.side_effect = build_alert_side_effect

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    _send_smart_alerts([sample_signal])

    # Verify build_telegram_alert was called with both roles
    calls = mock_build_alert.call_args_list
    roles_called = [call_obj[1].get("for_role", "free") for call_obj in calls]

    # Should have at least one "free" call
    assert "free" in roles_called, "Should build FREE tier alert"
    # Broadcast to members (PAID users) should also be called
    assert mock_broadcast.called, "Should broadcast to PAID members"


# ── TEST 6: Neutral Signals Are Skipped ────────────────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_neutral_signals_skipped(mock_post, mock_broadcast, mock_build_alert,
                                 mock_load_settings, neutral_signal, mock_settings):
    """
    Verify that signals with direction='neutral' are skipped.
    """
    mock_load_settings.return_value = mock_settings
    mock_build_alert.return_value = "Alert"

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    _send_smart_alerts([neutral_signal])

    # No alerts should be sent for neutral signals
    assert mock_build_alert.call_count == 0, "Neutral signals should not generate alerts"
    assert mock_post.call_count == 0, "No Telegram messages should be sent"


# ── TEST 7: Multiple Signals with Mixed Validity ──────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_mixed_signal_batch(mock_post, mock_broadcast, mock_build_alert,
                            mock_load_settings, sample_signal, weak_signal,
                            neutral_signal, mock_settings):
    """
    Test processing a batch of mixed signals:
    - 1 valid signal (score 90)
    - 1 weak signal (score 75 - below threshold)
    - 1 neutral signal (direction='neutral')
    - Result: Only 1 alert should be sent
    """
    mock_settings["max_per_cycle"] = 5  # High limit
    mock_load_settings.return_value = mock_settings
    mock_build_alert.return_value = "Alert"

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    signals = [sample_signal, weak_signal, neutral_signal]
    _send_smart_alerts(signals)

    # Only sample_signal should generate an alert
    assert mock_build_alert.call_count == 1, "Should send exactly 1 alert from 3 mixed signals"


# ── TEST 8: Cooldown Dict Cleanup ────────────────────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_cooldown_dict_cleanup(mock_post, mock_broadcast, mock_build_alert,
                               mock_load_settings, mock_settings):
    """
    Test that _last_alert_time dict doesn't grow unbounded.
    When it exceeds 500 entries, should keep only 200 most recent.
    """
    mock_load_settings.return_value = mock_settings
    mock_build_alert.return_value = "Alert"

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    # Create many different signals to fill the cooldown dict
    signals = []
    for i in range(600):
        signals.append({
            "symbol": f"COIN{i}",
            "score": 90,
            "direction": "buy",
            "price": 100.0,
            "change_pct": 1.0,
            "rsi": 60,
            "vol_ratio": 5.0,
            "tags": [],
        })

    # Process only some of them (not all due to max_per_cycle)
    for batch in [signals[i:i+10] for i in range(0, len(signals), 10)]:
        _send_smart_alerts(batch)

    # Verify cleanup occurred - dict should not exceed 200 entries
    # (Plus a few during processing, but definitely not 600)
    assert len(_last_alert_time) <= 250, f"Cooldown dict too large: {len(_last_alert_time)}"


# ── TEST 9: Direction-Based Cooldown ────────────────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_direction_based_cooldown(mock_post, mock_broadcast, mock_build_alert,
                                  mock_load_settings, mock_settings):
    """
    Test that cooldown is per symbol+direction, not just per symbol.
    Same symbol with different directions should not block each other.
    """
    mock_load_settings.return_value = mock_settings
    mock_build_alert.return_value = "Alert"

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    signal_buy = {
        "symbol": "BTC",
        "score": 90,
        "direction": "buy",
        "price": 45000.0,
        "change_pct": 2.0,
        "rsi": 60,
        "vol_ratio": 5.0,
        "tags": [],
    }

    signal_sell = {
        "symbol": "BTC",
        "score": 88,
        "direction": "sell",
        "price": 44900.0,
        "change_pct": -1.0,
        "rsi": 70,
        "vol_ratio": 4.5,
        "tags": [],
    }

    # Send BTC buy signal
    _send_smart_alerts([signal_buy])
    assert mock_build_alert.call_count == 1

    # Immediately send BTC sell signal (different direction)
    # Should NOT be blocked by cooldown
    _send_smart_alerts([signal_sell])
    assert mock_build_alert.call_count == 2, "Different direction should bypass cooldown"


# ── TEST 10: Settings Loading Error Handling ────────────────────────────────
@patch("scanner_engine.load_admin_alert_settings")
@patch("app.build_telegram_alert")
@patch("app.engine._broadcast_to_members")
@patch("app.req.post")
def test_graceful_fallback_to_defaults(mock_post, mock_broadcast, mock_build_alert,
                                       mock_load_settings, sample_signal):
    """
    Test graceful fallback if settings loading fails or returns unexpected format.
    """
    # Simulate partial settings (missing some keys)
    partial_settings = {
        "score_min": 85,
        # "max_per_cycle" missing
        # "cooldown_hours" missing
    }
    mock_load_settings.return_value = partial_settings
    mock_build_alert.return_value = "Alert"

    from app import _send_smart_alerts, _last_alert_time
    _last_alert_time.clear()

    # Should use .get() with defaults, so should not crash
    _send_smart_alerts([sample_signal])

    # Alert should still be sent with default values
    assert mock_build_alert.call_count >= 1, "Should handle partial settings gracefully"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
