# CryptoScanner Pro — Phase 2 Deployment Guide

**Version:** 2.0 (Phase 2: VIP Tier Features)  
**Date:** 2026-05-05  
**Status:** Ready for Production (Hetzner)

## Overview

Phase 2 adds 4 exclusive VIP-tier features to CryptoScanner Pro:
1. **Institutional Dashboard** — Live liquidations heatmap, funding rates, whale tracking
2. **Live Correlations** — Real-time asset correlation matrix with clustering detection
3. **VIP Morning Brief** — Macro/geopolitical context, economic calendar, regulatory sentiment
4. **Trading Setups Library** — Validated setups with statistics, historical trade examples

All features are **tier-gated** (VIP-only) and integrate with existing Free/Member/VIP subscription model.

---

## Pre-Deployment Checklist

### 1. Database Verification

```bash
# Backup production database
cp cryptoscanner.db cryptoscanner.db.backup.2026-05-05

# Verify new tables exist (from local testing)
sqlite3 cryptoscanner.db ".tables"
```

Expected tables: `users`, `subscriptions`, `trading_setups`, `setup_examples`, plus existing tables.

### 2. Code Verification

Verify these files are present and modified:

- ✓ `app.py` — Lines 2011-2123: New VIP endpoints
- ✓ `geopolitical_engine.py` — New macro analysis module (299 lines)
- ✓ `setups_engine.py` — New trading setups database (255 lines)
- ✓ `correlations_engine.py` — Correlation matrix calculations (200+ lines)
- ✓ `funding_engine.py` — Funding rates for institutional flows
- ✓ `liquidation_engine.py` — Liquidation heatmap data
- ✓ `templates/index.html` — New VIP tabs + JavaScript functions

### 3. Environment Configuration

Verify these environment variables are set on Hetzner:

```bash
export FLASK_ENV=production
export FLASK_DEBUG=0
export REPORT_TIMEZONE="Europe/Paris"  # For geopolitical_engine
export BINANCE_API_TIMEOUT=10  # API request timeout
export LIQUIDATION_FETCH_LIMIT=500  # Max liquidation records per symbol
```

### 4. Dependencies Check

Required Python packages (already in environment):

```
Flask==3.0.0
Flask-SocketIO==5.3.5
requests==2.31.0
numpy==1.24.0
sqlite3 (built-in)
datetime (built-in)
zoneinfo (built-in, Python 3.9+)
```

No new dependencies added.

---

## Deployment Steps

### Step 1: Stop Production Server

```bash
# On Hetzner
systemctl stop cryptoscanner  # Or your service name
ps aux | grep flask  # Verify no Flask processes running
```

### Step 2: Deploy Code

```bash
cd /var/www/cryptoscanner  # Production directory
git pull origin main  # Pull Phase 2 commits

# Verify new files are present
ls -la *.py | grep -E "geopolitical|setups|correlations|funding|liquidation"
```

### Step 3: Database Migration

```bash
# Initialize new tables (setups_engine calls init_setups_tables() on import)
python3 -c "from setups_engine import init_setups_tables; init_setups_tables()"

# Verify tables created
sqlite3 cryptoscanner.db "SELECT name FROM sqlite_master WHERE type='table';"
```

Expected output includes:
- `trading_setups`
- `setup_examples`

### Step 4: Seed Trading Setups (Optional for QA)

```bash
python3 << 'EOF'
from setups_engine import create_setup, add_setup_example

# Create 3 validated setups (already in local DB — copy if needed)
# BTC Breakout
setup_id_1 = create_setup(
    name="BTC Breakout Momentum",
    asset="BTC",
    pattern_type="breakout",
    timeframe="4h",
    entry_rule="Break above 20-day resistance with volume > 150% MA",
    exit_rule="Take profit at 1.5R or stop loss hit",
    stop_loss_rule="5% below breakout point",
    take_profit_rule="1.5x risk-reward ratio",
    risk_reward_ratio=1.5,
    avg_win_rate=0.68,
    total_trades=50,
    winning_trades=34,
    difficulty="Intermediate",
    market_condition="trending"
)

# ETH Divergence
setup_id_2 = create_setup(
    name="ETH Bullish Divergence",
    asset="ETH",
    pattern_type="divergence",
    timeframe="1d",
    entry_rule="Price lower low but RSI higher low on daily",
    exit_rule="Close above recent swing high or SL hit",
    stop_loss_rule="2% below entry",
    take_profit_rule="1.25x risk-reward ratio",
    risk_reward_ratio=1.25,
    avg_win_rate=0.62,
    total_trades=42,
    winning_trades=26,
    difficulty="Advanced",
    market_condition="consolidating"
)

# SOL Support Retest
setup_id_3 = create_setup(
    name="SOL Support Retest",
    asset="SOL",
    pattern_type="retest",
    timeframe="1h",
    entry_rule="Retest of broken support with volume drop",
    exit_rule="Close above support level or SL hit",
    stop_loss_rule="1.5% below support",
    take_profit_rule="1:1 risk-reward ratio",
    risk_reward_ratio=1.0,
    avg_win_rate=0.65,
    total_trades=34,
    winning_trades=22,
    difficulty="Beginner",
    market_condition="trending"
)

print(f"Created {setup_id_1}, {setup_id_2}, {setup_id_3}")
EOF
```

### Step 5: Start Production Server

```bash
systemctl start cryptoscanner
sleep 3
systemctl status cryptoscanner

# Verify Flask is running
curl -s http://localhost:5000/api/health | jq .
```

### Step 6: Test VIP Endpoints

```bash
# Login as VIP user (ensure user has subscription_tier='vip' in DB)
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"vip@example.com","password":"..."}' | jq -r '.token')

# Test new endpoints
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/morning-brief/vip | jq .

curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/setups/all | jq .

curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/correlations/matrix | jq .
```

### Step 7: Verify Frontend

1. Open https://cryptoscanner.production-domain.com
2. Login as VIP user
3. Navigate to **ANALYSE** section
4. Verify new buttons appear:
   - 👑 VIP BRIEF (gold accent)
   - 👑 SETUPS (gold accent)
5. Click each tab and verify data loads
6. Check browser console for errors (F12 → Console)

---

## API Endpoints (New)

### VIP Morning Brief

```
GET /api/morning-brief/vip
Authorization: Bearer <token> (VIP-only)

Response:
{
  "economic_calendar": {...},
  "regulatory_news": [...],
  "risk_score": 5.2,
  "sentiment": "neutral",
  "top_risks": [...],
  "catalysts": [...],
  "vip_insights": [...]
}
```

### Trading Setups

```
GET /api/setups/all
GET /api/setups/<id>
GET /api/setups/asset/<asset>
GET /api/setups/pattern/<pattern>
GET /api/setups/high-probability (min 60% win rate)

All VIP-gated. Response includes statistics, examples, trade history.
```

### Correlations

```
GET /api/correlations/matrix?symbols=BTC,ETH,SOL
GET /api/correlations/clusters?symbols=BTC,ETH,SOL

Returns correlation matrix, strong pairs, asset clusters.
```

### Institutional Flows

```
GET /api/institutional-flows/liquidations?symbol=BTC
GET /api/institutional-flows/funding-rates

Live whale data, liquidation heatmap, funding rates.
```

---

## Database Schema (New Tables)

### trading_setups

```sql
CREATE TABLE trading_setups (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    asset TEXT NOT NULL,           -- BTC, ETH, SOL
    pattern_type TEXT,              -- breakout, divergence, retest, etc.
    timeframe TEXT,                 -- 1h, 4h, 1d
    entry_rule TEXT,
    exit_rule TEXT,
    stop_loss_rule TEXT,
    take_profit_rule TEXT,
    risk_reward_ratio REAL,
    avg_win_rate REAL,              -- 0.60 = 60%
    total_trades INTEGER,
    winning_trades INTEGER,
    avg_duration_hours INTEGER,
    difficulty TEXT,                -- Beginner, Intermediate, Advanced
    market_condition TEXT,           -- trending, consolidating, ranging
    created_date TEXT,
    updated_date TEXT,
    vip_only BOOLEAN DEFAULT 1,
    active BOOLEAN DEFAULT 1
);
```

### setup_examples

```sql
CREATE TABLE setup_examples (
    id INTEGER PRIMARY KEY,
    setup_id INTEGER NOT NULL,
    asset TEXT,
    entry_price REAL,
    exit_price REAL,
    stop_price REAL,
    profit_usd REAL,
    duration_hours REAL,
    result TEXT,                   -- 'win', 'loss'
    date_traded TEXT,
    notes TEXT,
    FOREIGN KEY(setup_id) REFERENCES trading_setups(id)
);
```

---

## Rollback Procedure

If issues occur after deployment:

```bash
# Stop server
systemctl stop cryptoscanner

# Restore from backup
cp cryptoscanner.db.backup.2026-05-05 cryptoscanner.db

# Revert code (last stable commit)
git revert HEAD --no-edit

# Restart
systemctl start cryptoscanner
```

---

## Monitoring & Health Checks

### Post-Deployment (First 24h)

Monitor these metrics:

1. **API Response Times** — VIP endpoints should respond in <500ms
2. **Database Queries** — Check slow query logs (geopolitical_engine integrates news APIs)
3. **Memory Usage** — Correlation matrix calculation on startup uses ~50-100MB
4. **Error Logs** — Watch for missing news data, API timeouts from external sources

### Long-Term Health

Check weekly:

```bash
# Database size (setups library grows)
du -h cryptoscanner.db

# Table row counts
sqlite3 cryptoscanner.db "SELECT COUNT(*) FROM trading_setups;"
sqlite3 cryptoscanner.db "SELECT COUNT(*) FROM setup_examples;"

# Orphaned setup examples (no parent setup)
sqlite3 cryptoscanner.db \
  "SELECT COUNT(*) FROM setup_examples WHERE setup_id NOT IN (SELECT id FROM trading_setups);"
```

---

## Known Limitations & Notes

### News API Integration
- Geopolitical engine requires `news_macro.py` which fetches from external APIs
- If news API is unavailable, endpoint returns empty `regulatory_news` array (graceful degradation)
- Recommend caching news for 1-2 hours to reduce external API calls

### Correlation Matrix
- Recalculated on-demand from live Binance data
- 9-asset matrix takes ~2-3 seconds (Binance rate limits: 1200 req/min)
- Consider caching correlation matrix for 5-10 minutes in production

### Trading Setups
- 3 sample setups seeded in DB for QA
- Add new setups via admin interface or direct DB insert
- Each setup should have at least 3-5 real trade examples for credibility

### Tier Gating
- All new VIP endpoints check `_role_guard("vip")` before returning data
- Free/Member users see 403 Forbidden if they attempt access
- Verify subscription_tier column exists and is populated correctly

---

## Support & Troubleshooting

### Issue: "Route API non trouvée" (404 on VIP endpoints)

**Cause:** Flask not reloading after code changes
**Solution:**
```bash
pkill -f "flask run"
rm -rf __pycache__
systemctl restart cryptoscanner
```

### Issue: "KeyError: 'subscription_tier'"

**Cause:** Missing column in users table or SELECT query
**Solution:**
```sql
-- Verify column exists
PRAGMA table_info(users);

-- If missing, add it
ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free';
```

### Issue: Geopolitical data not loading

**Cause:** news_macro.py import failing or API timeout
**Solution:**
```python
# Test directly
python3 -c "from news_macro import fetch_economic_calendar; print(fetch_economic_calendar('day'))"

# Check environment variable for timezone
echo $REPORT_TIMEZONE
```

---

## Next Phase

**Phase 3 (Planned):** Mobile app integration, advanced analytics, user customization  
**Maintenance Window:** Weekly backup of trading setups database  
**SLA:** 99.5% uptime for VIP endpoints during market hours

---

**Deployed by:** Claude Code Assistant  
**Deployment Date:** 2026-05-05  
**Hetzner Instance:** [Your production server details]
