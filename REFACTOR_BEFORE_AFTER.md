# _send_smart_alerts() — Before & After Comparison

## BEFORE (Hardcoded Values)

```python
def _send_smart_alerts(signals):
    global _alerted_signals
    hour = datetime.now().strftime('%H')  # Cooldown 1h par symbole (was 30min)

    sent_this_cycle = 0
    MAX_PER_CYCLE = 3  # Anti-spam : max 3 alertes par cycle de scan

    for s in signals:
        if sent_this_cycle >= MAX_PER_CYCLE: break
        if s["score"] < 85: continue        # Score min relevé à 85 (was 80)
        if s["direction"] == "neutral": continue

        key = f"{s['symbol']}_{s['direction']}_{hour}"

        with _alert_lock:
            if key in _alerted_signals: continue
            _alerted_signals.add(key)
            if len(_alerted_signals) > 500:
                _alerted_signals = set(list(_alerted_signals)[-200:])

        # Envoyer version FREE sur le canal public Telegram
        msg_free = build_telegram_alert(s, for_role="free")
        _tk = TELEGRAM_TOKEN
        _ch = TELEGRAM_CHAT
        if _tk and _ch:
            try:
                req.post(f"https://api.telegram.org/bot{_tk}/sendMessage", json={"chat_id":_ch,"text":msg_free,"parse_mode":"HTML"},timeout=5)
            except: pass

        # Envoyer version PAID aux membres payants (via dashboard websocket)
        msg_paid = build_telegram_alert(s, for_role="paid")
        engine._broadcast_to_members(msg_paid, min_role="paid")
        sent_this_cycle += 1
```

### Issues with BEFORE:
1. ❌ **Hardcoded score threshold**: Line 369 uses `< 85` (not configurable)
2. ❌ **Hardcoded max per cycle**: Line 365 has `MAX_PER_CYCLE = 3` (not configurable)
3. ❌ **Hourly cooldown only**: Line 362/372 uses hour string key (granularity issue)
4. ❌ **No error handling**: Line 387 has bare `except: pass`
5. ❌ **No docstring**: Function purpose not documented
6. ❌ **Memory inefficient**: Stores entire hour strings in set

---

## AFTER (Admin Settings Based)

```python
# ── Cooldown tracking (timestamp-based per symbol+direction) ──────────────────
_last_alert_time = {}  # Format: {f"{symbol}_{direction}": timestamp}

def _send_smart_alerts(signals):
    """
    Send smart signal alerts to Telegram (FREE on public channel, PAID on dashboard).
    Uses admin settings for score_min, max_per_cycle, and cooldown_hours.
    Implements per-symbol cooldown tracking to prevent duplicate alerts.

    Args:
        signals: List of signal dicts with keys: symbol, score, direction, price, etc.
    """
    global _last_alert_time

    # ── Load settings from admin config ──────────────────────────────────────
    from scanner_engine import load_admin_alert_settings
    settings = load_admin_alert_settings()
    score_min = settings.get("score_min", 85)
    max_per_cycle = settings.get("max_per_cycle", 3)
    cooldown_hours = settings.get("cooldown_hours", 1)
    cooldown_seconds = cooldown_hours * 3600

    sent_this_cycle = 0
    current_time = time.time()

    for s in signals:
        # ── Check max per cycle limit ────────────────────────────────────────
        if sent_this_cycle >= max_per_cycle:
            break

        # ── Check score threshold ────────────────────────────────────────────
        if s["score"] < score_min:
            continue

        # ── Skip neutral signals ─────────────────────────────────────────────
        if s["direction"] == "neutral":
            continue

        symbol = s["symbol"]
        direction = s["direction"]
        cooldown_key = f"{symbol}_{direction}"

        # ── Check cooldown: has enough time passed since last alert? ─────────
        with _alert_lock:
            last_time = _last_alert_time.get(cooldown_key, 0)
            time_since_last = current_time - last_time

            # If within cooldown window, skip this signal
            if time_since_last < cooldown_seconds:
                continue

            # Update last alert time for this symbol+direction
            _last_alert_time[cooldown_key] = current_time

            # ── Cleanup old entries to prevent dict from growing unbounded ───
            if len(_last_alert_time) > 500:
                # Keep only the 200 most recent entries
                sorted_entries = sorted(_last_alert_time.items(), key=lambda x: x[1], reverse=True)
                _last_alert_time = dict(sorted_entries[:200])

        # ── Send FREE version to public Telegram channel ──────────────────────
        msg_free = build_telegram_alert(s, for_role="free")
        _tk = TELEGRAM_TOKEN
        _ch = TELEGRAM_CHAT
        if _tk and _ch:
            try:
                req.post(
                    f"https://api.telegram.org/bot{_tk}/sendMessage",
                    json={"chat_id": _ch, "text": msg_free, "parse_mode": "HTML"},
                    timeout=5
                )
            except Exception as e:
                print(f"[Alert] Failed to send FREE alert for {symbol}: {e}")

        # ── Send PAID version to members via dashboard WebSocket ──────────────
        msg_paid = build_telegram_alert(s, for_role="paid")
        try:
            engine._broadcast_to_members(msg_paid, min_role="paid")
        except Exception as e:
            print(f"[Alert] Failed to broadcast PAID alert for {symbol}: {e}")

        sent_this_cycle += 1
```

### Improvements in AFTER:
1. ✅ **Configurable score threshold**: Uses `settings.get("score_min", 85)`
2. ✅ **Configurable max per cycle**: Uses `settings.get("max_per_cycle", 3)`
3. ✅ **Precise timestamp-based cooldown**: Uses `time.time()` for second precision
4. ✅ **Robust error handling**: Named exceptions with logging
5. ✅ **Full documentation**: Docstring explaining purpose and args
6. ✅ **Memory efficient**: Uses timestamp dict instead of hour strings
7. ✅ **Better code clarity**: Section markers and inline comments
8. ✅ **Admin control**: All thresholds configured via database, not code

---

## Configuration Comparison

| Parameter | Before | After | Notes |
|-----------|--------|-------|-------|
| **score_min** | Hardcoded `85` | Admin setting (default 85) | Now configurable |
| **max_per_cycle** | Hardcoded `3` | Admin setting (default 3) | Now configurable |
| **cooldown** | Hourly granularity | Time-based seconds | Much more precise |
| **cooldown_hours** | Fixed 1 hour | Admin setting (default 1) | Now configurable |
| **Dedup mechanism** | Set with hour keys | Dict with timestamps | More efficient |
| **Error handling** | Silent failures | Logged failures | Better debugging |

---

## Behavior Differences

### Cooldown Scenario Example

**Before (HOURLY):**
- Signal at 14:30:00 → Alerted (key: `BTC_buy_14`)
- Signal at 14:59:59 → **BLOCKED** (same hour key)
- Signal at 15:00:00 → **ALERTED** (new hour, so no dupe protection across hour boundary!)
- **Problem**: Allows duplicate alerts right at hour boundary

**After (TIMESTAMP):**
- Signal at 14:30:00 → Alerted (timestamp: 1234567800)
- Signal at 14:59:59 → **BLOCKED** (only 29m 59s elapsed, < 1 hour)
- Signal at 15:30:01 → **ALERTED** (exactly 1 hour elapsed)
- **Benefit**: Precise cooldown enforcement, no boundary issues

---

## Admin Panel Integration

When admin updates settings via dashboard:

**Before:** Change requires code edit + redeploy
```
❌ Line 365: MAX_PER_CYCLE = 5  # Hard to change
❌ Line 369: if s["score"] < 90:  # Requires restart
```

**After:** Change takes effect immediately
```
✅ Admin UI → Database → load_admin_alert_settings() → Function uses it
✅ No restart needed, change applies to next scan cycle
```

---

## Testing Coverage

| Scenario | Before | After |
|----------|--------|-------|
| **Settings loaded** | N/A | ✅ Test 1 |
| **Max per cycle enforced** | N/A | ✅ Test 2 |
| **Cooldown works** | N/A | ✅ Test 3 |
| **Backward compatible** | N/A | ✅ Test 4 |
| **Telegram tiers differ** | N/A | ✅ Test 5 |
| **Neutral signals skipped** | ✅ Implicit | ✅ Test 6 |
| **Mixed batches** | ✅ Implicit | ✅ Test 7 |
| **Memory cleanup** | N/A | ✅ Test 8 |
| **Direction-based cooldown** | N/A | ✅ Test 9 |
| **Error resilience** | N/A | ✅ Test 10 |

Total: **10 comprehensive test cases**
