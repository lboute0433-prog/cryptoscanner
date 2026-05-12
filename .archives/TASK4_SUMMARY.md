# TASK 4: Refactor _send_retrace_alert() to Use Admin RETRACE RSI Settings

## Summary

Successfully refactored `_send_retrace_alert()` in app.py and `check_rsi_exit()` in smart_signals.py to use admin-configured RETRACE RSI block parameters instead of hardcoded values.

## Files Modified

### 1. `C:\Users\loyan\Documents\Antigravity\cryptoscanner\app.py`
- **Function**: `_send_retrace_alert()` (lines 444-519)
- **Changes**:
  - Loads admin settings via `load_admin_alert_settings()`
  - Extracts `rsi_oversold`, `rsi_overbought`, and `retrace_cooldown_hours` from settings
  - Uses timestamp-based cooldown mechanism (per-symbol+signal-type tracking)
  - Key format: `{symbol}_{SIGNAL_TYPE}` (e.g., "BTC_OVERSOLD", "BTC_OVERBOUGHT")
  - Implements global `_last_alert_time` dict to track last alert timestamp for each symbol+signal
  - Adds automatic dict cleanup to prevent unbounded growth (keeps 200 most recent entries)
  - Includes error handling for both Telegram and WebSocket broadcast failures
  - Logs RSI thresholds for debugging

### 2. `C:\Users\loyan\Documents\Antigravity\cryptoscanner\smart_signals.py`
- **Function**: `check_rsi_exit()` (lines 492-546)
- **Changes**:
  - Added optional parameters: `rsi_oversold` and `rsi_overbought`
  - Auto-loads admin settings from database when parameters are None
  - Falls back to hardcoded constants if DB lookup fails
  - Updated descriptions to include custom threshold values
  - Maintains backward compatibility (can be called without threshold parameters)

### 3. `C:\Users\loyan\Documents\Antigravity\cryptoscanner\test_send_retrace_alert.py` (NEW)
- Comprehensive test suite with 18 tests covering:
  - **RSI Detection Tests**: Verify both oversold and overbought detection with default and custom thresholds
  - **Cooldown Mechanism Tests**: Validate per-symbol+signal-type tracking
  - **Settings Fallback Tests**: Ensure defaults are used when DB is empty
  - **Backward Compatibility Tests**: Confirm existing code still works
  - **Signal Type Independence**: Test that OVERSOLD and OVERBOUGHT alerts for same symbol have separate cooldowns

## Technical Implementation

### Admin Settings Integration
```python
settings = load_admin_alert_settings()
rsi_oversold = settings.get("rsi_oversold", 30)       # Default: 30
rsi_overbought = settings.get("rsi_overbought", 70)   # Default: 70
cooldown_hours = settings.get("retrace_cooldown_hours", 1)  # Default: 1 hour
```

### Cooldown Tracking
- **Structure**: Global dict `_last_alert_time = {}`
- **Key Format**: `f"{symbol}_{SIGNAL_TYPE}"`  
  - "BTC_OVERSOLD" for bullish exit (RSI crossing above oversold threshold)
  - "BTC_OVERBOUGHT" for bearish exit (RSI crossing below overbought threshold)
- **Validation**: Checks `time_since_last = current_time - _last_alert_time[key]`
- **Auto-cleanup**: Keeps only 200 most recent entries when dict exceeds 500 entries

### Per-Symbol Independence
- BTC oversold alerts have separate cooldown from BTC overbought alerts
- BTC alerts are completely independent from ETH alerts
- Different signal types for same symbol are NOT blocked by each other

## Test Results

All 18 tests pass:
```
test_send_retrace_alert.py::TestCheckRSIExit::test_loads_settings_from_db_when_not_provided PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_multiple_symbols_independent PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_no_exit_when_rsi_in_normal_zone PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_no_exit_when_rsi_stays_in_zone PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_no_history_returns_none PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_rsi_overbought_detection_with_default_settings PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_rsi_overbought_with_custom_threshold PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_rsi_oversold_detection_with_default_settings PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_rsi_oversold_with_custom_threshold PASSED
test_send_retrace_alert.py::TestCheckRSIExit::test_uses_default_when_db_missing PASSED
test_send_retrace_alert.py::TestBuildRetraceAlert::test_overbought_alert_format_free PASSED
test_send_retrace_alert.py::TestBuildRetraceAlert::test_oversold_alert_format_paid PASSED
test_send_retrace_alert.py::TestSendRetraceAlert::test_cooldown_key_generation PASSED
test_send_retrace_alert.py::TestSendRetraceAlert::test_different_signal_types_independent_keys PASSED
test_send_retrace_alert.py::TestBackwardCompatibility::test_check_rsi_exit_works_without_explicit_thresholds PASSED
test_send_retrace_alert.py::TestBackwardCompatibility::test_hardcoded_constants_still_available PASSED
test_send_retrace_alert.py::TestSettingsFallback::test_empty_settings_returns_defaults PASSED
test_send_retrace_alert.py::TestSettingsFallback::test_explicit_thresholds_override_defaults PASSED
```

## Key Features

1. **Admin-Controlled Thresholds**: RETRACE RSI alerts now respect admin dashboard settings
2. **Per-Symbol Cooldown**: Each symbol+signal-type combination has independent cooldown tracking
3. **Backward Compatible**: Existing code continues to work without changes
4. **Fallback to Defaults**: If settings not in DB, uses hardcoded defaults (30/70/1 hour)
5. **Settings Precedence**:
   - DB settings (admin dashboard) > hardcoded constants > function defaults
6. **Memory Safe**: Auto-cleanup of old cooldown entries prevents dict from growing unbounded
7. **Error Handling**: Catches and logs failures in both Telegram and WebSocket broadcast
8. **Extensible**: Optional parameters in `check_rsi_exit()` allow for future customization

## Alerts Broadcast To

RETRACE RSI alerts are sent to BOTH users (not differentiated by tier):
- **FREE users**: Public Telegram channel via `req.post()` to Telegram API
- **PAID users**: Dashboard via `engine._broadcast_to_members(min_role="paid")`

This matches the requirement that RETRACE RSI is included in both FREE and PAID channels.

## Consistency with TASK 3

Implementation follows the same pattern established in TASK 3 (`_send_smart_alerts()`):
- Timestamp-based cooldown mechanism (not hour-based deduplication)
- Per-key tracking in global dict with thread-safe locking
- Automatic dict cleanup with retention of 200 most recent entries
- Settings loaded at function start, not globally

## No Changes to

- RSI calculation logic (still using `calc_rsi()` with 14-period)
- WebSocket message format
- Database logging
- Telegram message building (`build_retrace_alert()`)
- Hardcoded RSI constants (still defined in smart_signals.py for backward compat)
