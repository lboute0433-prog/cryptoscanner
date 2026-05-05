"""Tests for correlations engine."""
import pytest
from correlations_engine import (
    get_price_history,
    calculate_correlation_matrix,
    get_asset_clusters
)


def test_price_history():
    """Test fetching price history for BTC."""
    prices = get_price_history('BTC', interval='1h', limit=24)
    assert isinstance(prices, list)
    assert len(prices) > 0
    assert all(isinstance(p, float) for p in prices)
    print(f"BTC prices (last 3): {prices[-3:]}")


def test_correlation_matrix():
    """Test correlation matrix calculation."""
    corr_data = calculate_correlation_matrix(
        symbols=['BTC', 'ETH', 'BNB'],
        period_hours=24
    )

    assert 'correlation_matrix' in corr_data
    assert 'symbols' in corr_data
    assert 'timestamp' in corr_data
    assert len(corr_data['symbols']) == 3

    matrix = corr_data['correlation_matrix']
    assert len(matrix) == 3
    assert len(matrix[0]) == 3

    # Diagonal should be 1.0
    assert matrix[0][0] == 1.0
    assert matrix[1][1] == 1.0
    assert matrix[2][2] == 1.0

    print(f"Correlation matrix: {matrix}")
    print(f"Strong correlations: {corr_data.get('strong_correlations', [])[:3]}")


def test_asset_clusters():
    """Test asset clustering."""
    clusters_data = get_asset_clusters(symbols=['BTC', 'ETH', 'BNB', 'SOL'])

    assert 'clusters' in clusters_data
    assert 'ungrouped' in clusters_data
    assert 'timestamp' in clusters_data

    print(f"Clusters: {clusters_data['clusters']}")
    print(f"Ungrouped: {clusters_data['ungrouped']}")
