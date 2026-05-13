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
    from smart_signals import detect_breakout
    candle_data = {'close': 0.0052, 'high_24h': 0.0048}
    result = detect_breakout(candle_data)
    assert result == True


def test_breakout_no_trigger_below_24h_high():
    """No breakout if close < 24h_high"""
    from smart_signals import detect_breakout
    candle_data = {'close': 0.0047, 'high_24h': 0.0048}
    result = detect_breakout(candle_data)
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
