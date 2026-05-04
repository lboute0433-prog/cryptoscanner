import pytest
import sys
sys.path.insert(0, '/sessions/loving-gallant-dijkstra/mnt/cryptoscanner/.worktrees/feature-heatmap-oi-volume')

from heatmap_engine import (
    normalize_values,
    calculate_intensity,
    assign_color,
    HeatmapCalculator
)

class TestNormalization:
    def test_normalize_values_basic(self):
        values = [10, 20, 30, 40, 50]
        normalized = normalize_values(values)
        
        assert normalized[0] == 0.0  # min
        assert normalized[-1] == 1.0  # max
        assert all(0 <= v <= 1 for v in normalized)
    
    def test_normalize_values_single_value(self):
        """Edge case: all same values"""
        values = [5, 5, 5, 5]
        normalized = normalize_values(values)
        
        # When all same, return all 0.5 (midpoint)
        assert all(v == 0.5 for v in normalized)
    
    def test_normalize_values_two_values(self):
        values = [10, 20]
        normalized = normalize_values(values)
        
        assert normalized[0] == 0.0
        assert normalized[1] == 1.0

class TestIntensityCalculation:
    def test_intensity_formula(self):
        """intensity = 0.6 * vol_norm + 0.4 * oi_norm"""
        vol_norm = 0.8
        oi_norm = 0.5
        
        intensity = calculate_intensity(vol_norm, oi_norm)
        expected = 0.6 * 0.8 + 0.4 * 0.5  # 0.68
        
        assert intensity == expected
    
    def test_intensity_all_volume(self):
        intensity = calculate_intensity(1.0, 0.0)
        expected = 0.6 * 1.0 + 0.4 * 0.0
        
        assert intensity == expected
    
    def test_intensity_all_oi(self):
        intensity = calculate_intensity(0.0, 1.0)
        expected = 0.6 * 0.0 + 0.4 * 1.0
        
        assert intensity == expected

class TestColorAssignment:
    def test_color_blue(self):
        assert assign_color(0.3) == "blue"
        assert assign_color(0.4) == "orange"  # Boundary
    
    def test_color_orange(self):
        assert assign_color(0.5) == "orange"
        assert assign_color(0.65) == "orange"
    
    def test_color_red(self):
        assert assign_color(0.7) == "red"  # Boundary
        assert assign_color(0.9) == "red"
    
    def test_color_edges(self):
        assert assign_color(0.0) == "blue"
        assert assign_color(1.0) == "red"

class TestHeatmapCalculator:
    def test_calculator_init(self):
        calc = HeatmapCalculator()
        assert calc is not None
    
    def test_calculator_process_cryptos(self):
        """Mock crypto data → intensity calculation"""
        cryptos_data = [
            {"symbol": "BTC", "volume_24h": 28e9, "oi_change_1h": 3.2},
            {"symbol": "ETH", "volume_24h": 15e9, "oi_change_1h": 2.8},
            {"symbol": "DOGE", "volume_24h": 0.9e9, "oi_change_1h": -0.5},
        ]
        
        result = HeatmapCalculator().process_cryptos(cryptos_data)
        
        # Check structure
        assert len(result) == 3
        for crypto in result:
            assert "symbol" in crypto
            assert "intensity" in crypto
            assert "color" in crypto
            assert 0 <= crypto["intensity"] <= 1
            assert crypto["color"] in ["blue", "orange", "red"]
