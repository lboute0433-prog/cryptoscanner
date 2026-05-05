import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_funding_rates():
    """Test funding rate fetcher."""
    from funding_engine import get_funding_rates

    result = get_funding_rates()

    assert isinstance(result, list), f"Expected list, got {type(result)}"
    assert len(result) > 0, "No funding rates returned"

    first = result[0]
    assert 'symbol' in first
    assert 'funding_rate' in first
    assert 'timestamp' in first
    assert isinstance(first['funding_rate'], float)

    print(f"[PASS] Funding rates test passed: {len(result)} assets")

if __name__ == '__main__':
    test_funding_rates()
