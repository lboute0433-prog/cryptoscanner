import sys
import os
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_liquidation_parser():
    """Test that we can parse liquidation data from Binance."""
    from liquidation_engine import get_liquidations_24h

    result = get_liquidations_24h('BTC')

    # Should return dict with keys
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'symbol' in result
    assert 'total_long' in result
    assert 'total_short' in result
    assert 'net_liquidations' in result
    assert 'price_levels' in result
    print(f"[OK] Liquidation test passed: {result}")

if __name__ == '__main__':
    test_liquidation_parser()
