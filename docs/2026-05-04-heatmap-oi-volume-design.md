# Heatmap OI+Volume — Design Document

**Date:** 2026-05-04  
**Status:** ✅ APPROVED  
**Feature:** Interactive heatmap showing Open Interest + Volume intensity for all Binance Futures cryptos  
**Owner:** CryptoScanner Pro Development

---

## 1. Overview

Create an interactive heatmap dashboard that displays the combined intensity of Open Interest (OI) + Volume across all Binance Futures cryptos. Clicking a crypto updates the entire dashboard: TradingView chart symbol changes, detailed price-level heatmap overlay appears, and market scores refresh.

**Key Constraints:**
- Paid members only (subscription_tier ≥ 2)
- Real-time updates via WebSocket (max 10s refresh)
- Dynamic crypto list from Binance (zero hardcoding)
- Modular backend (heatmap_engine.py)

---

## 2. Architecture Decisions

### 2.1 File Structure
```
cryptoscanner/
├── heatmap_engine.py           # NEW: Intensity calculations + Binance integration
├── app.py                      # MODIFY: Add 3 endpoints + WebSocket event
├── templates/index.html        # MODIFY: Add GlobalHeatmap + DetailHeatmap + TradingView integration
└── schema.sql                  # MODIFY: Add crypto_heatmap table
```

### 2.2 Technology Choices

| Component | Choice | Reason |
|-----------|--------|--------|
| Real-time UI | WebSocket + SocketIO | Already in app.py, instant updates |
| Cache | SQLite `crypto_heatmap` table | Fast reads, persistent across restarts |
| TradingView | Lightweight Charts API | Free, open-source, custom overlays |
| Data Source | Binance Futures REST + WebSocket | Official API, high reliability |
| Auth | session + subscription_tier check | Existing pattern in CryptoScanner |

---

## 3. Database Schema

### Table: `crypto_heatmap`
```sql
CREATE TABLE crypto_heatmap (
  id INTEGER PRIMARY KEY,
  symbol TEXT UNIQUE NOT NULL,      -- BTC, ETH, SOL, etc.
  intensity REAL NOT NULL,           -- 0.0 to 1.0
  color TEXT NOT NULL,               -- 'blue', 'orange', 'red'
  volume_24h REAL,                   -- in USDT
  oi_variation_1h REAL,              -- percent change
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table: `oi_history` (for OI tracking)
```sql
CREATE TABLE oi_history (
  id INTEGER PRIMARY KEY,
  symbol TEXT NOT NULL,
  oi_value REAL NOT NULL,
  snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (symbol) REFERENCES crypto_heatmap(symbol)
);
```

---

## 4. Intensity Calculation Formula

**Step 1: Normalize Volume**
```
volume_normalized = (crypto_volume_24h - min_volume) / (max_volume - min_volume)
```

**Step 2: Normalize OI Variation (1h change)**
```
oi_variation_1h = ((current_oi - oi_1h_ago) / oi_1h_ago) * 100
oi_normalized = (oi_change_1h - min_change) / (max_change - min_change)
```

**Step 3: Weighted Blend**
```
intensity = (0.60 * volume_normalized) + (0.40 * oi_normalized)
```

**Step 4: Color Assignment**
```
if intensity < 0.4:   color = "blue"
if 0.4 ≤ intensity < 0.7:  color = "orange"
if intensity ≥ 0.7:   color = "red"
```

**Environment Variables (configurable):**
```
HEATMAP_VOLUME_WEIGHT=0.6
HEATMAP_OI_WEIGHT=0.4
HEATMAP_THRESHOLD_LOW=0.4
HEATMAP_THRESHOLD_HIGH=0.7
```

---

## 5. API Endpoints

### 5.1 GET /api/heatmap/all
**Purpose:** Fetch global heatmap (all cryptos)  
**Auth:** Paid members only (subscription_tier ≥ 2)  
**Response:**
```json
{
  "timestamp": "2026-05-04T10:30:00Z",
  "cryptos": [
    { "symbol": "BTC", "intensity": 0.82, "color": "red", "volume_24h": 28500000000, "oi_change_1h": 3.2 },
    { "symbol": "ETH", "intensity": 0.76, "color": "red", "volume_24h": 15200000000, "oi_change_1h": 2.8 },
    ...
  ]
}
```

### 5.2 GET /api/heatmap/{symbol}
**Purpose:** Fetch detailed heatmap by price level  
**Auth:** Paid members only  
**Response:**
```json
{
  "symbol": "BTC",
  "timestamp": "2026-05-04T10:30:00Z",
  "price_levels": [
    { "price": 70000, "intensity": 0.25, "color": "blue" },
    { "price": 68000, "intensity": 0.45, "color": "blue" },
    { "price": 66000, "intensity": 0.65, "color": "orange" },
    { "price": 64000, "intensity": 0.92, "color": "red" },
    ...
  ]
}
```

---

## 6. WebSocket Events

### Event: `heatmap_update`
**Frequency:** Every 10 seconds (max)  
**Scope:** Paid members only  
**Payload:**
```json
{
  "timestamp": "2026-05-04T10:30:00Z",
  "deltas": [
    { "symbol": "BTC", "intensity": 0.82, "color": "red" },
    { "symbol": "ETH", "intensity": 0.76, "color": "red" }
  ]
}
```

**Frontend Behavior:**
1. Receive event
2. Update corresponding rows in GlobalHeatmap table
3. Update TradingView overlay if selected crypto affected

---

## 7. Real-Time Data Flow

### Background Thread (10s cycle)
1. Fetch volume_24h from `GET /fapi/v1/ticker/24hr`
2. Fetch current OI from `GET /fapi/v1/openInterest`
3. Retrieve OI snapshot from 1h ago in `oi_history`
4. Calculate OI variation: `(current_oi - oi_1h_ago) / oi_1h_ago * 100`
5. Normalize volume & OI across all cryptos
6. Calculate intensity for each crypto
7. Update `crypto_heatmap` table
8. Compare with previous state → extract deltas
9. Emit `heatmap_update` to WebSocket (paid members only)
10. Store new OI snapshot in `oi_history`
11. Sleep 10s → repeat

### Frontend Real-Time Loop
1. On page load: fetch `GET /api/heatmap/all`
2. Render GlobalHeatmap table
3. Listen for `heatmap_update` WebSocket events
4. Update table rows + TradingView overlay instantly

---

## 8. Frontend Components

### GlobalHeatmap (Clickable Table)
- Displays all cryptos with symbol, intensity, color, volume_24h, oi_change_1h
- On row click: emit `selectCrypto(symbol)` event
- On WebSocket update: re-render affected rows
- Highlight currently selected crypto

### DetailHeatmap (TradingView Overlay)
- Rendered using **TradingView Lightweight Charts** (free API)
- Fetch detailed data from `GET /api/heatmap/{symbol}`
- Draw horizontal price-level bands with color-coded intensity
- Band width = proportional to intensity value
- Price labels on left side
- Update on crypto select or WebSocket `heatmap_update`

### TradingView Integration
- Change chart symbol dynamically when crypto selected
- Overlay DetailHeatmap bands on candlestick chart
- Support multiple timeframes (user preference)

### Scores & Market Structure Panel
- Display: Trend score, Volatility, Liquidity, Momentum (each 0-100)
- Display: Market structure (HH/HL, Break of Structure, Change of Character)
- Display: Liquidity zones (support/resistance)
- Refresh on crypto select

---

## 9. Authentication & Authorization

### HTTP Endpoints
```python
@app.route('/api/heatmap/all', methods=['GET'])
def get_heatmap_all():
    user_id = session.get('user_id')
    if not user_id:
        return {"error": "Unauthorized"}, 401
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.subscription_tier < 2:  # tier 2 = paid
        return {"error": "Forbidden - paid members only"}, 403
    
    # ... return data
```

### WebSocket Events
```python
# Before emitting heatmap_update, filter paid users
paid_users = db.query(User).filter(User.subscription_tier >= 2).all()
paid_sids = [user.socket_sid for user in paid_users]
socketio.emit('heatmap_update', data, to=paid_sids)
```

---

## 10. Edge Cases & Error Handling

| Scenario | Handling |
|----------|----------|
| Binance API down | Serve stale cache from SQLite + log error |
| New crypto added | Auto-detect on next fetch (dynamic list) |
| Crypto delisted | Remove from table on next fetch |
| WebSocket disconnect | Client reconnects → fetch full state from GET |
| Division by zero | Edge case: all volumes identical → skip normalization |
| User loses subscription | Stop WebSocket updates immediately |
| Empty SQLite cache | Fetch from Binance on startup |

---

## 11. Performance Considerations

- **Cache Strategy:** SQLite reduces API calls to Binance (only 10s interval instead of per-request)
- **Delta Emission:** WebSocket only sends changed values (reduces payload)
- **Lazy Loading:** Load DetailHeatmap only when crypto selected
- **Normalization:** Recalculate only every 10s, not per-request

---

## 12. Testing Strategy

### Unit Tests
- Intensity calculation formula (edge cases)
- Normalization logic
- Color assignment thresholds

### Integration Tests
- GET /api/heatmap/all response structure
- GET /api/heatmap/{symbol} response structure
- WebSocket `heatmap_update` event payload
- Auth checks (paid vs non-paid users)

### Manual Testing
- Global heatmap renders correctly
- Clicking crypto updates all panels (TradingView, overlay, scores)
- Real-time updates via WebSocket work
- Non-paid members get 403 Forbidden
- Binance API failure gracefully degrades to cache

---

## 13. Deliverables Checklist

- [ ] heatmap_engine.py — Complete module
- [ ] app.py — 3 endpoints + WebSocket event added
- [ ] schema.sql — crypto_heatmap + oi_history tables created
- [ ] templates/index.html — GlobalHeatmap + DetailHeatmap components
- [ ] TradingView Lightweight Charts integration
- [ ] README updated with setup instructions
- [ ] Unit + integration tests
- [ ] Deployment to production (Hetzner)

---

## 14. Success Criteria

✅ Global heatmap displays all cryptos with intensity colors  
✅ Clicking crypto updates TradingView symbol dynamically  
✅ DetailHeatmap overlay shows price-level bands  
✅ Real-time updates via WebSocket (max 10s)  
✅ Only paid members see the feature  
✅ Scores + market structure panel refreshes on select  
✅ Zero hardcoded symbols (fully dynamic)  
✅ Graceful error handling (Binance down → use cache)  

---

**Document Status:** ✅ Ready for Implementation Plan  
**Last Updated:** 2026-05-04 by Orchestrateur ICA
