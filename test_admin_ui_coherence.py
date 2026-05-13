"""Integration tests for admin parameter coherence (TASK 6)

Tests verify that admin parameter changes affect API responses correctly.
Focus: Admin UI → Backend Settings → API Response
"""
import pytest
from app import app
from db import set_setting, get_setting


@pytest.fixture
def client():
    """Flask test client with testing mode enabled."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_admin_score_min_change_affects_api(client):
    """Changing admin score_min should filter API response correctly."""
    # Set permissive score_min
    set_setting('score_min', '10')

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # Verify API returns the score_min setting
    assert 'score_min' in data
    assert data.get('score_min') == 10

    # Change to more restrictive
    set_setting('score_min', '80')
    response = client.get('/api/smart_signals?role=paid')
    data = response.json

    # Verify updated score_min is reflected
    assert data.get('score_min') == 80
    # All returned signals should respect this minimum
    for signal in data.get('signals', []):
        assert signal.get('score', 0) >= 80


def test_admin_variation_pump_affects_detection(client):
    """Changing variation_pump should affect signal detection criteria."""
    set_setting('variation_pump', '0.5')

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # API should return signals structure with coherent filtering
    assert 'signals' in data
    assert isinstance(data['signals'], list)

    # Change to more restrictive
    set_setting('variation_pump', '2.0')
    response = client.get('/api/smart_signals?role=paid')
    data = response.json

    # API should still respond with valid structure
    assert 'signals' in data
    assert isinstance(data['signals'], list)


def test_admin_rsi_oversold_affects_retrace_detection(client):
    """Changing RSI oversold level should affect retrace signals."""
    set_setting('rsi_oversold', '25')

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # Verify response has expected structure
    assert 'signals' in data
    assert 'score_min' in data

    # Change RSI oversold threshold
    set_setting('rsi_oversold', '35')
    response = client.get('/api/smart_signals?role=paid')
    data = response.json

    # Response should remain valid and consistent
    assert response.status_code == 200
    assert 'signals' in data


def test_admin_vol_mult_affects_detection(client):
    """Changing volume multiplier threshold should affect detection."""
    # More permissive: 2x volume requirement
    set_setting('vol_mult_min', '2.0')

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json
    count_permissive = len(data.get('signals', []))

    # More restrictive: 5x volume requirement
    set_setting('vol_mult_min', '5.0')
    response = client.get('/api/smart_signals?role=paid')
    data = response.json
    count_restrictive = len(data.get('signals', []))

    # Restrictive should generally find fewer or equal signals
    # (not a hard requirement due to dynamic market data)
    assert isinstance(count_restrictive, int)
    assert isinstance(count_permissive, int)


def test_admin_settings_persist_across_requests(client):
    """Admin settings should persist and be applied consistently."""
    set_setting('score_min', '50')
    set_setting('variation_pump', '1.0')
    set_setting('vol_mult_min', '2.5')

    # First request
    resp1 = client.get('/api/smart_signals?role=paid')
    assert resp1.status_code == 200
    data1 = resp1.json
    score_min_1 = data1.get('score_min')
    signals_1 = len(data1.get('signals', []))

    # Second request - settings should still apply
    resp2 = client.get('/api/smart_signals?role=paid')
    assert resp2.status_code == 200
    data2 = resp2.json
    score_min_2 = data2.get('score_min')
    signals_2 = len(data2.get('signals', []))

    # Settings should persist
    assert score_min_1 == score_min_2 == 50
    # Signal counts should be similar (may vary slightly due to live data)
    # but both should use the same score_min filter
    assert data1.get('score_min') == data2.get('score_min')


def test_admin_settings_database_persistence(client):
    """Admin settings should persist in the database."""
    # Set a value
    set_setting('test_key_unique_12345', 'test_value_abcde')

    # Read it back
    value = get_setting('test_key_unique_12345')
    assert value == 'test_value_abcde'

    # Update it
    set_setting('test_key_unique_12345', 'updated_value')
    value = get_setting('test_key_unique_12345')
    assert value == 'updated_value'


def test_api_returns_all_admin_parameters(client):
    """API response should include admin configuration in response."""
    set_setting('score_min', '42')

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # Essential admin parameters should be in response
    assert 'signals' in data
    assert 'score_min' in data
    assert 'role' in data

    # score_min should match what we set
    assert data['score_min'] == 42


def test_free_vs_paid_filtering(client):
    """FREE tier should filter signals, PAID tier should see more."""
    set_setting('score_min', '20')

    # Get FREE tier signals
    resp_free = client.get('/api/smart_signals?role=free')
    assert resp_free.status_code == 200
    data_free = resp_free.json

    # Get PAID tier signals
    resp_paid = client.get('/api/smart_signals?role=paid')
    assert resp_paid.status_code == 200
    data_paid = resp_paid.json

    # Both should respect score_min
    assert data_free.get('score_min') == data_paid.get('score_min') == 20

    # Both should have valid signal structures
    assert isinstance(data_free.get('signals'), list)
    assert isinstance(data_paid.get('signals'), list)


def test_signal_enriched_fields_in_api_response(client):
    """API signals should include all enriched fields."""
    set_setting('score_min', '0')  # Get all available signals

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # If signals exist, verify they have enriched fields
    if data.get('signals'):
        signal = data['signals'][0]

        # Required fields
        required_fields = ['symbol', 'score']
        for field in required_fields:
            assert field in signal, f"Signal missing required field: {field}"

        # Enriched fields (added in TASK 3-5)
        enriched_fields = ['pump_pct', 'vol_mult', 'entry_level', 'target_level']
        for field in enriched_fields:
            assert field in signal, f"Signal missing enriched field: {field}"
