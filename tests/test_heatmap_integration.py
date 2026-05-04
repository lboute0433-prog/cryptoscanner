import pytest
import sys
sys.path.insert(0, '/sessions/loving-gallant-dijkstra/mnt/cryptoscanner/.worktrees/feature-heatmap-oi-volume')

from heatmap_engine import HeatmapCalculator

class TestHeatmapIntegration:
    def test_full_heatmap_cycle(self):
        """Test end-to-end: fetch → calculate → cache → retrieve"""
        calc = HeatmapCalculator()
        
        # Mock data
        cryptos_data = [
            {"symbol": "BTC", "volume_24h": 28e9, "oi_change_1h": 3.2},
            {"symbol": "ETH", "volume_24h": 15e9, "oi_change_1h": 2.8},
            {"symbol": "SOL", "volume_24h": 2.3e9, "oi_change_1h": 1.1},
        ]
        
        # Process
        result = calc.process_cryptos(cryptos_data)
        
        # Verify
        assert len(result) == 3
        assert all(c["symbol"] in ["BTC", "ETH", "SOL"] for c in result)
        assert all(0 <= c["intensity"] <= 1 for c in result)
        
    def test_cache_operations(self):
        """Test cache update and retrieval"""
        calc = HeatmapCalculator()
        
        cryptos_data = [
            {"symbol": "BTC", "intensity": 0.82, "color": "red", "volume_24h": 28e9, "oi_variation_1h": 3.2},
        ]
        
        # Update cache
        calc.update_cache(cryptos_data)
        
        # Retrieve
        cached = calc.get_all_from_cache()
        
        # Verify
        assert len(cached) > 0
