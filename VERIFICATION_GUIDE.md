# TASK 3: Verification Guide for _send_smart_alerts() Refactoring

## Quick Verification Steps

### Step 1: Code Review
Confirm the refactored function:
- [x] File: `C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py`
- [x] Lines: 363-441 (function definition)
- [x] Lines: 357-358 (new `_last_alert_time` global)

### Step 2: Syntax Check
```bash
cd C:\Users\loyan\Documents\Antigravity\cryptoscanner
python -m py_compile app.py
# Expected: No output (success)
```

### Step 3: Import Check
```bash
python -c "from app import _send_smart_alerts; print('✓ Imports successful')"
# Expected: ✓ Imports successful
```

### Step 4: Run Tests
```bash
pytest test_send_smart_alerts.py -v
# Expected: 10 tests passing
```

---

## Functional Verification (Manual Testing)

### Test 1: Verify score_min Setting is Used
**Scenario:** Send signals with different scores

```python
# In Python shell or test script:
from app import _send_smart_alerts
from unittest.mock import patch, MagicMock

signals = [
    {"symbol": "BTC", "score": 90, "direction": "buy", ...},  # Should pass
    {"symbol": "ETH", "score": 75, "direction": "buy", ...},   # Should skip
]

with patch("scanner_engine.load_admin_alert_settings") as mock_settings:
    mock_settings.return_value = {"score_min": 85, "max_per_cycle": 3, "cooldown_hours": 1}
    with patch("app.build_telegram_alert") as mock_alert:
        _send_smart_alerts(signals)
        # Verify: Only 1 alert generated (score 90 passes, 75 fails)
        assert mock_alert.call_count == 1
        print("✓ score_min setting respected")
```

### Test 2: Verify max_per_cycle Limit
**Scenario:** Send more signals than max_per_cycle

```python
signals = [
    {"symbol": f"COIN{i}", "score": 90, "direction": "buy", ...}
    for i in range(5)  # 5 signals
]

with patch("scanner_engine.load_admin_alert_settings") as mock_settings:
    mock_settings.return_value = {"score_min": 85, "max_per_cycle": 2, "cooldown_hours": 1}
    with patch("app.build_telegram_alert") as mock_alert:
        _send_smart_alerts(signals)
        # Verify: Only 2 alerts generated (max_per_cycle = 2)
        assert mock_alert.call_count == 2
        print("✓ max_per_cycle limit enforced")
```

### Test 3: Verify Cooldown Mechanism
**Scenario:** Send same signal twice immediately

```python
signal = {"symbol": "BTC", "score": 90, "direction": "buy", ...}

with patch("scanner_engine.load_admin_alert_settings") as mock_settings:
    mock_settings.return_value = {"score_min": 85, "max_per_cycle": 3, "cooldown_hours": 1}
    with patch("app.build_telegram_alert") as mock_alert:
        # First send
        _send_smart_alerts([signal])
        first_call_count = mock_alert.call_count  # Should be 1
        
        # Second send (immediately, within cooldown)
        _send_smart_alerts([signal])
        second_call_count = mock_alert.call_count  # Should still be 1
        
        assert second_call_count == first_call_count
        print("✓ Cooldown prevents duplicate alerts")
```

### Test 4: Verify Direction-Based Cooldown
**Scenario:** Same symbol, different directions should not block each other

```python
signal_buy = {"symbol": "BTC", "score": 90, "direction": "buy", ...}
signal_sell = {"symbol": "BTC", "score": 88, "direction": "sell", ...}

with patch("scanner_engine.load_admin_alert_settings") as mock_settings:
    mock_settings.return_value = {"score_min": 85, "max_per_cycle": 10, "cooldown_hours": 1}
    with patch("app.build_telegram_alert") as mock_alert:
        _send_smart_alerts([signal_buy])
        first_count = mock_alert.call_count  # Should be 1
        
        # Send different direction immediately
        _send_smart_alerts([signal_sell])
        second_count = mock_alert.call_count  # Should be 2
        
        assert second_count == 2
        print("✓ Direction-based cooldown works correctly")
```

### Test 5: Verify Neutral Signals Are Skipped
**Scenario:** Send neutral direction signal

```python
signal_neutral = {"symbol": "ADA", "score": 90, "direction": "neutral", ...}

with patch("scanner_engine.load_admin_alert_settings") as mock_settings:
    mock_settings.return_value = {"score_min": 85, "max_per_cycle": 3, "cooldown_hours": 1}
    with patch("app.build_telegram_alert") as mock_alert:
        _send_smart_alerts([signal_neutral])
        # Verify: No alerts generated for neutral signals
        assert mock_alert.call_count == 0
        print("✓ Neutral signals correctly skipped")
```

### Test 6: Verify Admin Settings Integration
**Scenario:** Change admin settings and verify function uses them

```python
# Simulate admin changing score_min from 85 to 95
with patch("scanner_engine.load_admin_alert_settings") as mock_settings:
    mock_settings.return_value = {
        "score_min": 95,  # Changed!
        "max_per_cycle": 3,
        "cooldown_hours": 1
    }
    with patch("app.build_telegram_alert") as mock_alert:
        signals = [
            {"symbol": "BTC", "score": 92, "direction": "buy", ...},  # Below new threshold
            {"symbol": "ETH", "score": 96, "direction": "buy", ...},   # Above new threshold
        ]
        _send_smart_alerts(signals)
        # Verify: Only ETH (score 96) generates alert
        assert mock_alert.call_count == 1
        print("✓ Admin settings dynamically applied")
```

### Test 7: Verify Telegram Tier Routing
**Scenario:** Check that both FREE and PAID alerts are generated

```python
signal = {"symbol": "BTC", "score": 90, "direction": "buy", ...}

with patch("scanner_engine.load_admin_alert_settings") as mock_settings:
    mock_settings.return_value = {"score_min": 85, "max_per_cycle": 3, "cooldown_hours": 1}
    with patch("app.build_telegram_alert") as mock_alert:
        with patch("app.engine._broadcast_to_members") as mock_broadcast:
            _send_smart_alerts([signal])
            
            # Check that both FREE and PAID versions were built
            calls = mock_alert.call_args_list
            roles = [call[1].get("for_role", "free") for call in calls]
            
            assert "free" in roles
            print("✓ FREE tier alert generated")
            
            # Broadcast should be called for PAID users
            assert mock_broadcast.called
            print("✓ PAID tier alert broadcast")
```

### Test 8: Verify Error Handling
**Scenario:** Telegram API fails, function should not crash

```python
signal = {"symbol": "BTC", "score": 90, "direction": "buy", ...}

with patch("scanner_engine.load_admin_alert_settings") as mock_settings:
    mock_settings.return_value = {"score_min": 85, "max_per_cycle": 3, "cooldown_hours": 1}
    with patch("app.build_telegram_alert", return_value="Alert"):
        with patch("app.req.post", side_effect=Exception("Connection timeout")):
            # Should not raise, should handle gracefully
            _send_smart_alerts([signal])
            print("✓ Error handling works (Telegram API failure handled)")
```

---

## Integration Verification

### Check 1: Function is Called from Scan Loop
```bash
grep -n "_send_smart_alerts" app.py
# Expected output:
# 344:            _send_smart_alerts(results)
# 363:def _send_smart_alerts(signals):
```

### Check 2: Global Variables Initialized
```bash
grep -n "_last_alert_time\|_alerted_signals\|_alerted_retraces" app.py | head -10
# Expected: All three globals defined
```

### Check 3: Imports Present
```bash
grep "from scanner_engine import.*load_admin_alert_settings" app.py
# Expected: Line 51 shows the import
```

---

## Performance Verification

### Memory Usage Test
Monitor that `_last_alert_time` dict doesn't grow unbounded:

```python
from app import _last_alert_time

# Simulate many signals
for i in range(1000):
    # Trigger alert processing
    ...

# Check dict size
print(f"_last_alert_time entries: {len(_last_alert_time)}")
# Expected: Should be <= 200 (cleanup happens at > 500)
```

### Cooldown Dict Cleanup Verification
```bash
# Add debug output to see cleanup in action
grep -A 5 "Cleanup old entries" app.py
# Should show cleanup logic at lines 414-418
```

---

## Settings Validation

### Check 1: load_admin_alert_settings Works
```python
from scanner_engine import load_admin_alert_settings

settings = load_admin_alert_settings()
print(f"score_min: {settings.get('score_min')}")
print(f"max_per_cycle: {settings.get('max_per_cycle')}")
print(f"cooldown_hours: {settings.get('cooldown_hours')}")

# Expected: All three settings present with correct defaults
```

### Check 2: Settings Properly Loaded in Function
```python
# Add print statement temporarily for debugging
# In _send_smart_alerts, after loading settings:
# print(f"[DEBUG] Settings loaded: score_min={score_min}, max_per_cycle={max_per_cycle}")

# Look for this debug output in app logs during runtime
```

---

## Test Execution

### Run Full Test Suite
```bash
cd C:\Users\loyan\Documents\Antigravity\cryptoscanner
pytest test_send_smart_alerts.py -v --tb=short
```

### Expected Output
```
test_send_smart_alerts.py::test_score_min_respected PASSED
test_send_smart_alerts.py::test_max_per_cycle_enforced PASSED
test_send_smart_alerts.py::test_cooldown_prevents_duplicates PASSED
test_send_smart_alerts.py::test_backward_compatibility_default_settings PASSED
test_send_smart_alerts.py::test_telegram_tier_routing PASSED
test_send_smart_alerts.py::test_neutral_signals_skipped PASSED
test_send_smart_alerts.py::test_mixed_signal_batch PASSED
test_send_smart_alerts.py::test_cooldown_dict_cleanup PASSED
test_send_smart_alerts.py::test_direction_based_cooldown PASSED
test_send_smart_alerts.py::test_graceful_fallback_to_defaults PASSED

======================== 10 passed in X.XXs ========================
```

---

## Regression Testing

### Ensure Existing Functionality Still Works

- [x] Smart signals are still detected and sent
- [x] Telegram messages are formatted correctly (both FREE and PAID)
- [x] WebSocket broadcast to dashboard works
- [x] Database logging unchanged
- [x] No new imports break existing code
- [x] Thread safety maintained with `_alert_lock`

---

## Checklist: All Verifications Complete

- [ ] Code compiles without syntax errors
- [ ] Imports work correctly
- [ ] All 10 tests pass
- [ ] score_min setting respected
- [ ] max_per_cycle limit enforced
- [ ] Cooldown mechanism prevents duplicates
- [ ] Direction-based cooldown works
- [ ] Neutral signals skipped
- [ ] Admin settings integrated
- [ ] Telegram tier routing verified
- [ ] Error handling works
- [ ] Memory cleanup functional
- [ ] Backward compatibility maintained
- [ ] Function called from scan loop
- [ ] No circular imports introduced

---

## Troubleshooting

### Issue: Tests fail with "ModuleNotFoundError"
**Solution:** Ensure current directory is in PYTHONPATH
```bash
cd C:\Users\loyan\Documents\Antigravity\cryptoscanner
export PYTHONPATH="$PWD:$PYTHONPATH"
pytest test_send_smart_alerts.py -v
```

### Issue: "load_admin_alert_settings not found"
**Solution:** Verify scanner_engine.py exports the function
```bash
grep "def load_admin_alert_settings" scanner_engine.py
```

### Issue: Tests run but some fail
**Solution:** Check that mocks are properly patched
- Ensure `@patch` decorators target correct module paths
- Verify `mock_settings.return_value` returns correct dict structure
- Check that `_last_alert_time.clear()` is called between tests

---

## Next Steps

1. **Monitor in Production**: Watch scan logs for alerts to verify settings are applied
2. **Dashboard Update**: Confirm admin UI allows changing these settings
3. **Performance Monitoring**: Track cooldown dict size over time
4. **User Feedback**: Collect feedback on new cooldown behavior vs hourly

---

## Reference: TASK 3 Requirements

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Load score_min from settings | ✅ Complete | app.py line 377 |
| Load max_per_cycle from settings | ✅ Complete | app.py line 378 |
| Load cooldown_hours from settings | ✅ Complete | app.py line 379 |
| Implement timestamp cooldown | ✅ Complete | app.py lines 402-418 |
| Per-symbol tracking | ✅ Complete | app.py line 400 |
| Per-direction tracking | ✅ Complete | app.py line 400 |
| Thread-safe cooldown | ✅ Complete | app.py line 403 `with _alert_lock` |
| Memory cleanup | ✅ Complete | app.py lines 415-418 |
| Error handling | ✅ Complete | app.py lines 431-432, 438-439 |
| Test coverage (10 tests) | ✅ Complete | test_send_smart_alerts.py |
| Backward compatible | ✅ Complete | Default values used via `.get()` |
| Docstring added | ✅ Complete | app.py lines 364-371 |

