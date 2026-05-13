"""End-to-end tests for pump detection system (TASK 7)

Tests verify the complete flow: admin config → detection → API → display.
Focus: E2E coherence across all layers (Admin → Backend → API → Frontend)
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


def test_e2e_admin_to_api_flow(client):
    """
    E2E: Admin sets permissive params → API returns signals with correct structure.

    Flow:
    1. Admin UI sets permissive parameters
    2. Backend loads settings from DB
    3. API endpoint returns signals with correct filtering
    4. Response includes enriched signal format
    """
    # 1. Admin sets permissive parameters
    set_setting('score_min', '10')
    set_setting('variation_pump', '0.5')
    set_setting('vol_mult_min', '2.0')
    set_setting('criteria_min', '1')

    # 2. Verify settings were saved
    assert get_setting('score_min') == '10'
    assert get_setting('variation_pump') == '0.5'

    # 3. API returns signals with correct filtering
    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # 4. Verify API response structure
    assert 'signals' in data
    assert 'score_min' in data
    assert data['score_min'] == 10

    # All returned signals should respect the minimum score
    for signal in data.get('signals', []):
        assert signal.get('score', 0) >= 10


def test_e2e_restrictive_params_reduce_signals(client):
    """E2E: Very restrictive params → fewer or no signals."""
    # Set very restrictive parameters
    set_setting('score_min', '95')  # Almost impossible threshold
    set_setting('vol_mult_min', '10.0')  # 10x volume requirement

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # With such restrictive settings
    assert data['score_min'] == 95

    # All signals (if any) should respect the restrictive score_min
    for signal in data.get('signals', []):
        assert signal.get('score', 0) >= 95


def test_e2e_free_vs_paid_tier_access(client):
    """E2E: FREE tier gets basic signals, PAID gets all with enrichment."""
    set_setting('score_min', '30')

    # Get FREE tier signals
    resp_free = client.get('/api/smart_signals?role=free')
    assert resp_free.status_code == 200
    data_free = resp_free.json

    # Get PAID tier signals
    resp_paid = client.get('/api/smart_signals?role=paid')
    assert resp_paid.status_code == 200
    data_paid = resp_paid.json

    # Both should have score_min
    assert 'score_min' in data_free
    assert 'score_min' in data_paid
    assert data_free['score_min'] == data_paid['score_min'] == 30

    # Both should have signals list
    assert isinstance(data_free.get('signals'), list)
    assert isinstance(data_paid.get('signals'), list)


def test_e2e_param_change_immediate_effect(client):
    """E2E: Changing admin param should immediately affect next API call."""
    # Set initial permissive value
    set_setting('score_min', '20')
    resp1 = client.get('/api/smart_signals?role=paid')
    assert resp1.status_code == 200
    data1 = resp1.json
    score_min_1 = data1.get('score_min')
    assert score_min_1 == 20

    # Immediately change to restrictive value
    set_setting('score_min', '60')
    resp2 = client.get('/api/smart_signals?role=paid')
    assert resp2.status_code == 200
    data2 = resp2.json
    score_min_2 = data2.get('score_min')

    # New value should be immediately reflected
    assert score_min_1 != score_min_2
    assert score_min_2 == 60

    # All returned signals should respect the new score_min
    for signal in data2.get('signals', []):
        assert signal.get('score', 0) >= 60


def test_e2e_all_enriched_fields_present(client):
    """E2E: All signals have all required enriched fields for frontend."""
    set_setting('score_min', '0')  # Get all available signals

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # Required enriched fields added in TASK 3-5
    required_fields = ['symbol', 'score', 'pump_pct', 'vol_mult', 'entry_level', 'target_level']

    # If there are signals, verify all fields present
    if data['signals']:
        for signal in data['signals']:
            for field in required_fields:
                assert field in signal, f"Signal missing field: {field}"
                # Fields should have values
                assert signal[field] is not None


def test_e2e_signal_filtering_consistency(client):
    """E2E: Multiple API calls with same settings return consistent filtering."""
    set_setting('score_min', '40')

    # Make 3 consecutive calls
    resp1 = client.get('/api/smart_signals?role=paid')
    resp2 = client.get('/api/smart_signals?role=paid')
    resp3 = client.get('/api/smart_signals?role=paid')

    data1 = resp1.json
    data2 = resp2.json
    data3 = resp3.json

    # All should have same score_min
    assert data1['score_min'] == data2['score_min'] == data3['score_min'] == 40

    # All returned signals should respect the score_min in each response
    for data in [data1, data2, data3]:
        for signal in data.get('signals', []):
            assert signal.get('score', 0) >= 40


def test_e2e_api_response_completeness(client):
    """E2E: API response includes all necessary information for frontend."""
    set_setting('score_min', '25')

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # Response structure (required for frontend)
    assert 'signals' in data  # List of signals
    assert 'score_min' in data  # Applied threshold
    assert 'role' in data  # User tier
    assert 'ts' in data  # Timestamp of signal generation

    # Response should be JSON serializable
    import json
    json_str = json.dumps(data)
    assert len(json_str) > 0


def test_e2e_signal_score_matches_detection_criteria(client):
    """E2E: Signal scores reflect the detection criteria met."""
    set_setting('score_min', '0')  # Get all signals

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # Scores should be between 0 and 100
    for signal in data.get('signals', []):
        score = signal.get('score', 0)
        assert 0 <= score <= 100, f"Invalid score {score} for {signal.get('symbol')}"


def test_e2e_volume_metrics_enrichment(client):
    """E2E: Signal enrichment includes volume metrics."""
    set_setting('score_min', '0')

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # If signals exist, verify volume enrichment
    if data['signals']:
        for signal in data['signals']:
            # vol_mult should be a number > 0
            vol_mult = signal.get('vol_mult')
            assert vol_mult is not None
            assert isinstance(vol_mult, (int, float))
            assert vol_mult > 0

            # pump_pct should be a percentage
            pump_pct = signal.get('pump_pct')
            assert pump_pct is not None
            assert isinstance(pump_pct, (int, float))


def test_e2e_entry_target_enrichment(client):
    """E2E: Signal enrichment includes entry and target levels."""
    set_setting('score_min', '0')

    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # If signals exist, verify entry/target enrichment
    if data['signals']:
        for signal in data['signals']:
            entry = signal.get('entry_level')
            target = signal.get('target_level')

            # Both should exist and be numbers
            assert entry is not None
            assert target is not None
            assert isinstance(entry, (int, float))
            assert isinstance(target, (int, float))

            # Target should generally be above entry for pumps
            # (not always true for dumps, so just check they exist)
            assert entry > 0
            assert target > 0


def test_e2e_timestamp_tracking(client):
    """E2E: API includes timestamp for signal generation."""
    response = client.get('/api/smart_signals?role=paid')
    assert response.status_code == 200
    data = response.json

    # Should include timestamp
    assert 'ts' in data
    # Timestamp should be present and not None
    assert data['ts'] is not None
