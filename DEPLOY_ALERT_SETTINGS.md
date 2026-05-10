# Deploy Alert Settings Fix

This deployment fixes the issue where `/api/smart_signals` returns `score_min: 85` instead of the configured value.

## Root Cause

The database was missing the JSON-formatted alert settings (`smart_signals`, `retrace_rsi`, `macro_events`). The `load_admin_alert_settings()` function was returning default values instead of reading from the database.

## Changes Made

1. **db.py**: Added `init_alert_settings()` function that creates JSON-formatted alert configuration on app startup
2. **app.py**: 
   - Added import of `init_alert_settings` from db.py
   - Called `init_alert_settings()` during app initialization
   - Added debug logging to `/api/smart_signals` endpoint to trace score_min value

## Deployment Steps

### On Production Server (Hetzner)

```bash
# 1. Navigate to app directory
cd /app

# 2. Pull latest code
git pull

# 3. Restart the service
sudo systemctl restart cryptoscanner

# 4. Verify initialization
sudo journalctl -u cryptoscanner -n 20 | grep "Alert settings"

# 5. Test the API
curl -s https://46.225.234.71/api/smart_signals | jq '.score_min'
# Expected response: 50 (instead of 85)
```

## Verification

After restarting, the service logs should show:
```
[DB] Alert settings initialized: smart_signals, retrace_rsi, macro_events
```

And the API response should include:
```json
{
  "score_min": 50,
  "signals": [...],
  ...
}
```

## Configuration

After deployment, you can modify alert settings via the ADMIN panel:
- **SMART SIGNALS**: Score minimum, max alerts/cycle, cooldown hours
- **RETRACE RSI**: RSI oversold/overbought thresholds, cooldown
- **MACRO EVENTS**: Importance level, enabled status, cooldown

Changes are applied immediately on next cycle (every 2 minutes).

## Debug Logs

To view the debug output from the endpoint:
```bash
sudo journalctl -u cryptoscanner -f | grep "\[DEBUG"
```

This will show:
- When settings are loaded
- What values are returned
- Final score_min value

## Rollback

If needed, rollback to previous version:
```bash
cd /app
git revert HEAD
sudo systemctl restart cryptoscanner
```
