# test_pump_detection.py
import pytest
from smart_signals import detect_volume_spike

def test_volume_spike_detection_triggers_on_2x_volume():
    """Volume spike detected when vol > 2x MA20"""
    candle_data = {
        'volume': 525000000,  # 525M
        'volume_ma20': 50000000  # 50M MA
    }
    result = detect_volume_spike(candle_data, threshold=2.0)
    assert bool(result) == True
    assert result.multiplier == 10.5

def test_volume_spike_no_trigger_below_threshold():
    """No spike if vol < threshold"""
    candle_data = {'volume': 75000000, 'volume_ma20': 50000000}
    result = detect_volume_spike(candle_data, threshold=2.0)
    assert bool(result) == False


def test_breakout_detection_triggers_above_24h_high():
    """Breakout detected when close > 24h_high"""
    from smart_signals import detect_breakout_price
    candle_data = {'close': 0.0052, 'high_24h': 0.0048}
    result = detect_breakout_price(candle_data)
    assert result == True


def test_breakout_no_trigger_below_24h_high():
    """No breakout if close < 24h_high"""
    from smart_signals import detect_breakout_price
    candle_data = {'close': 0.0047, 'high_24h': 0.0048}
    result = detect_breakout_price(candle_data)
    assert result == False


def test_momentum_detection_triggers_above_threshold():
    """Momentum detected when RSI > 60"""
    from smart_signals import detect_momentum
    candle_data = {'rsi': 75}
    result = detect_momentum(candle_data, threshold=60.0)
    assert result == True


def test_momentum_no_trigger_below_threshold():
    """No momentum if RSI < 60"""
    from smart_signals import detect_momentum
    candle_data = {'rsi': 45}
    result = detect_momentum(candle_data, threshold=60.0)
    assert result == False


def test_volume_spike_rejects_negative_volumes():
    """Negative volumes should not trigger detection"""
    candle_data = {'volume': -100000000, 'volume_ma20': 50000000}
    result = detect_volume_spike(candle_data, threshold=2.0)
    assert bool(result) == False


def test_volume_spike_handles_missing_volume_ma20():
    """Missing volume_ma20 should not trigger detection"""
    candle_data = {'volume': 100000000}  # missing volume_ma20
    result = detect_volume_spike(candle_data, threshold=2.0)
    assert bool(result) == False


def test_composite_pump_score_calculation():
    """Score = (criteria_met / 3) * 100"""
    from smart_signals import calculate_pump_score

    # All 3 criteria met
    criteria = {'volume_spike': True, 'breakout': True, 'momentum': True}
    score = calculate_pump_score(criteria)
    assert score == 100.0

    # 2 criteria met
    criteria = {'volume_spike': True, 'breakout': True, 'momentum': False}
    score = calculate_pump_score(criteria)
    assert score == 66.67

    # 1 criteria met
    criteria = {'volume_spike': True, 'breakout': False, 'momentum': False}
    score = calculate_pump_score(criteria)
    assert score == 33.33

    # No criteria met
    criteria = {'volume_spike': False, 'breakout': False, 'momentum': False}
    score = calculate_pump_score(criteria)
    assert score == 0.0


def test_api_smart_signals_enriched_response():
    """API returns pump %, vol_mult, score, entry/target"""
    from app import app

    client = app.test_client()
    response = client.get('/api/smart_signals?role=paid')

    assert response.status_code == 200
    data = response.json

    # Check response structure
    assert 'signals' in data
    assert 'score_min' in data

    # Check signal structure (if signals exist)
    if data['signals']:
        signal = data['signals'][0]
        assert 'symbol' in signal
        assert 'score' in signal
        assert 'pump_pct' in signal  # NEW
        assert 'vol_mult' in signal  # NEW
        assert 'entry_level' in signal  # NEW
        assert 'target_level' in signal  # NEW
