# CryptoScanner Pro — VIP Features Setup Guide

**Date:** 2026-05-05  
**Version:** Phase 2

This guide covers setting up and configuring VIP features for local development and production.

---

## Quick Start (Local Development)

### 1. Verify Python Environment

```bash
python3 --version  # Should be 3.12+
pip list | grep -E "Flask|requests|numpy"
```

### 2. Initialize Databases

```bash
cd /path/to/cryptoscanner

# Start Python shell
python3

# Initialize setups tables
from setups_engine import init_setups_tables
init_setups_tables()

# Seed sample setups
from setups_engine import create_setup, add_setup_example

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

# Add example trades
add_setup_example(setup_id_1, "BTC", 42500, 46875, 40375, 2375, 4.2, "win")
add_setup_example(setup_id_1, "BTC", 43200, 40960, 41040, -1200, 2.1, "loss")
add_setup_example(setup_id_1, "BTC", 44100, 48510, 41895, 3410, 6.8, "win")

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

add_setup_example(setup_id_2, "ETH", 2200, 2420, 2156, 220, 8.5, "win")
add_setup_example(setup_id_2, "ETH", 2350, 2100, 2401.5, -301.5, 5.2, "loss")

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

add_setup_example(setup_id_3, "SOL", 135, 143.5, 132.975, 8.5, 2.0, "win")
add_setup_example(setup_id_3, "SOL", 142, 125, 145.05, -20, 1.5, "loss")

print("Setups created successfully!")
exit()
```

### 3. Create Test User with VIP Tier

```bash
sqlite3 cryptoscanner.db << 'EOF'
-- Check if users table has subscription_tier column
PRAGMA table_info(users);

-- If subscription_tier is missing, add it
-- ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free';

-- Insert or update test VIP user
INSERT OR REPLACE INTO users (
    id, email, password_hash, username, subscription_tier, subscription_expires
) VALUES (
    999,
    'vip-test@example.com',
    'test_hash_placeholder',
    'vip_tester',
    'vip',
    datetime('now', '+1 year')
);

-- Verify
SELECT id, email, subscription_tier, subscription_expires FROM users WHERE id = 999;
EOF
```

### 4. Start Flask Development Server

```bash
# Set environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1
export REPORT_TIMEZONE="Europe/Paris"

# Run Flask
python3 app.py

# Should output:
# * Running on http://localhost:5000
# * WARNING in werkzeug ... (normal)
```

### 5. Test VIP Endpoints Locally

```bash
# In another terminal:

# Test correlations endpoint (no auth needed, but try with VIP user for full response)
curl -s http://localhost:5000/api/correlations/matrix?symbols=BTC,ETH,SOL | jq .

# Test setups endpoint
curl -s http://localhost:5000/api/setups/all | jq .

# Test VIP morning brief (requires auth)
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"vip-test@example.com","password":"test"}' | jq -r '.token // empty')

if [ -n "$TOKEN" ]; then
  curl -s -H "Authorization: Bearer $TOKEN" \
    http://localhost:5000/api/morning-brief/vip | jq .
else
  echo "Login failed or token empty"
fi
```

### 6. Open Browser & Test Frontend

```
http://localhost:5000
```

**Expected:**
1. Home page loads (Morning Brief, Scanner sections visible)
2. Login with `vip-test@example.com`
3. Navigate to **ANALYSE** section
4. See new buttons: **👑 VIP BRIEF**, **👑 SETUPS**
5. Click VIP BRIEF → Risk score, insights, calendar, news load
6. Click SETUPS → Setup cards, statistics, detail modal work

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Flask
FLASK_ENV=production  # or 'development' for local
FLASK_DEBUG=0
SECRET_KEY=your_secret_key_here

# Database
DATABASE_PATH=./cryptoscanner.db
DATABASE_BACKUP_PATH=./backups/

# Timezone (for geopolitical_engine reports)
REPORT_TIMEZONE=Europe/Paris

# API Timeouts
BINANCE_API_TIMEOUT=10  # seconds
ECONOMIC_CALENDAR_TIMEOUT=8

# Caching
CORRELATION_MATRIX_CACHE_MINUTES=10
ECONOMIC_CALENDAR_CACHE_MINUTES=60
REGULATORY_NEWS_CACHE_MINUTES=60

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/cryptoscanner.log
```

### Database Schema Verification

Ensure all tables exist:

```bash
sqlite3 cryptoscanner.db << 'EOF'
-- Check all required tables
.tables

-- Verify users table has subscription_tier
PRAGMA table_info(users);

-- Verify trading_setups exists
SELECT COUNT(*) as setup_count FROM trading_setups;
SELECT COUNT(*) as example_count FROM setup_examples;

-- Check for any orphaned examples
SELECT COUNT(*) FROM setup_examples WHERE setup_id NOT IN (SELECT id FROM trading_setups);
EOF
```

### Authentication Setup

VIP feature access requires:

1. **User must be logged in** (`_role_guard()` checks session)
2. **subscription_tier = 'vip'** (in users table)
3. **subscription_expires > NOW()** (active subscription)

**Test user creation:**

```python
from security import hash_password

# In Python shell
from app import app
from db import get_connection

with app.app_context():
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO users 
        (email, password_hash, username, subscription_tier, subscription_expires)
        VALUES (?, ?, ?, ?, datetime('now', '+1 year'))
    """, (
        'test@vip.com',
        hash_password('testpass123'),
        'testvip',
        'vip'
    ))
    conn.commit()
    conn.close()
    print("VIP user created")
```

---

## Module Configuration

### geopolitical_engine.py

**Purpose:** Macro analysis, economic calendar, regulatory news

**Configuration:**

```python
# In geopolitical_engine.py, line 10:
GEOPOL_TZ = ZoneInfo(os.environ.get("REPORT_TIMEZONE", "Europe/Paris"))
```

**Dependencies:**
- `news_macro.py` — Must be in same directory, exports `fetch_economic_calendar()`, `get_news_from_db()`
- External APIs via news_macro (handles timeouts gracefully)

**Graceful Degradation:**
- If news API unavailable → returns empty news arrays (no error)
- If economic calendar unavailable → returns empty events (no error)
- Risk score defaults to 5 (neutral) if data missing

### correlations_engine.py

**Purpose:** Asset correlation matrix, clustering

**Configuration:**

```python
# In correlations_engine.py:
CORRELATION_THRESHOLD = 0.7  # High correlation threshold
CLUSTER_COUNT = 3  # K-means clusters
BINANCE_API_TIMEOUT = 10  # seconds
```

**Dependencies:**
- `requests` library (for Binance API calls)
- `numpy` library (for correlation calculations)
- Binance public API (no auth required)

**Performance:**
- 9x9 matrix: ~2-3 seconds
- Binance rate limit: 1200 req/min (safe for on-demand)
- Recommend caching 10 minutes in production

### setups_engine.py

**Purpose:** Trading setups database, CRUD operations

**Configuration:**

```python
# Database connection via db.py
from db import get_connection

# Tables auto-created on import:
init_setups_tables()  # Called at module load (line 254)
```

**Dependencies:**
- SQLite3 (built-in)
- `db.py` — Must export `get_connection()` function

**Database Growth:**
- Initial: 3 sample setups, 7-10 examples
- Monthly: +5-10 new setups, +20-30 new examples
- Yearly: ~500 setups, ~2000 examples (estimate)
- Maintenance: Periodic table optimization (`VACUUM`)

### liquidation_engine.py & funding_engine.py

**Purpose:** Institutional flows data

**Configuration:**

```python
# In liquidation_engine.py:
LIQUIDATION_FETCH_LIMIT = 500  # Max records per symbol
LIQUIDATION_PRICE_STEP = 100  # Price level granularity ($)

# In funding_engine.py:
FUNDING_RATE_CACHE_MINUTES = 5  # Update frequency
```

**Dependencies:**
- Binance public API (`/fapi/v1/openInterest`, `/fapi/v1/fundingRate`)
- No authentication required
- Rate limits: 1200 requests/min (safe)

---

## Testing Checklist

### Unit Tests

```bash
# Test correlations engine
pytest tests/test_correlations.py -v

# Test setups engine
pytest tests/test_setups.py -v
```

### Integration Tests (Local)

```bash
# Start Flask server in background
python3 app.py &
sleep 2

# Test correlations endpoint
curl -s http://localhost:5000/api/correlations/matrix?symbols=BTC,ETH,SOL | jq .

# Test setups endpoint
curl -s http://localhost:5000/api/setups/all | jq . | head -30

# Test VIP brief with auth
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@vip.com","password":"testpass123"}' | jq -r '.token')

curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:5000/api/morning-brief/vip | jq .

# Kill Flask
pkill -f "python3 app.py"
```

### Frontend Tests (Browser)

1. **Login Flow:**
   - Open http://localhost:5000
   - Enter VIP credentials
   - Verify "Connecté" status

2. **VIP Brief Tab:**
   - Click ANALYSE → VIP BRIEF
   - Wait 2-3 seconds for data
   - Verify all sections load:
     - Risk score gauge
     - VIP insights
     - Economic calendar
     - Regulatory news

3. **Setups Tab:**
   - Click ANALYSE → SETUPS
   - Verify statistics cards show:
     - Total setups: 3
     - High probability: 2 (ETH 62%, SOL 65% > 60%)
     - Average win rate: ~65%
   - Click a setup card
   - Detail modal shows entry/exit rules + trade history

4. **Non-VIP Access:**
   - Logout
   - Try visiting endpoints (browser console):
     ```javascript
     fetch('/api/morning-brief/vip')
       .then(r => r.json())
       .then(d => console.log(d));
     // Should return 401 Unauthorized
     ```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'geopolitical_engine'"

**Cause:** File not in project root, or Python path not set correctly

**Solution:**
```bash
# Verify file exists
ls -la geopolitical_engine.py

# Verify import path in app.py
grep "from geopolitical_engine import" app.py

# Verify Python can find it
python3 -c "import geopolitical_engine; print(geopolitical_engine.__file__)"
```

### Issue: "KeyError: 'subscription_tier' on VIP endpoints"

**Cause:** Users table missing column, or SELECT query doesn't include it

**Solution:**
```bash
# Check column exists
sqlite3 cryptoscanner.db "PRAGMA table_info(users);" | grep subscription_tier

# If missing, add it:
sqlite3 cryptoscanner.db "ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT 'free';"

# Verify scanner_engine.py SELECT includes it (line ~419)
grep "subscription_tier" scanner_engine.py
```

### Issue: "Correlations endpoint returns [NaN, NaN, ...]"

**Cause:** Binance API down or empty price history

**Solution:**
```python
# Test Binance connectivity
import requests
r = requests.get("https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT", timeout=5)
print(r.status_code)  # Should be 200

# Test price history fetch
from correlations_engine import get_price_history
prices = get_price_history('BTC', interval='1h', limit=24)
print(len(prices), prices[-3:])  # Should have 24 prices
```

### Issue: "403 Forbidden" on VIP endpoints when logged in

**Cause:** subscription_tier not 'vip' for user

**Solution:**
```bash
# Check user subscription
sqlite3 cryptoscanner.db \
  "SELECT id, email, subscription_tier, subscription_expires FROM users LIMIT 5;"

# Update if needed
sqlite3 cryptoscanner.db \
  "UPDATE users SET subscription_tier = 'vip' WHERE email = 'your@email.com';"
```

### Issue: Flask not reloading after code changes

**Cause:** Python modules cached in __pycache__

**Solution:**
```bash
# Clear cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
rm -rf *.pyc

# Kill Flask
pkill -f "flask run"
pkill -f "python3 app.py"

# Restart
python3 app.py
```

---

## Deployment to Hetzner

See **DEPLOYMENT.md** for full production setup.

Quick checklist:
- [ ] Backup current database
- [ ] Pull latest code (`git pull origin main`)
- [ ] Verify `geopolitical_engine.py`, `setups_engine.py` present
- [ ] Run migrations (`python3 -c "from setups_engine import init_setups_tables; init_setups_tables()"`)
- [ ] Set environment variables (`.env` or systemd)
- [ ] Restart Flask service (`systemctl restart cryptoscanner`)
- [ ] Test VIP endpoints with curl
- [ ] Test frontend in browser
- [ ] Monitor logs for first hour

---

## Maintenance Tasks

### Weekly
- Check VIP endpoint response times
- Verify news data freshness (not >2h old)
- Inspect error logs for API timeouts

### Monthly
- Add new trading setups (if any)
- Add new trade examples to existing setups
- Review correlation matrix quality (compare to TradingView)
- Update economic calendar filters if needed

### Quarterly
- Backup trading setups database separately
- Review setups win rates (remove underperforming ones)
- Update geopolitical risk scoring thresholds if market regime changed

---

**Last Updated:** 2026-05-05  
**Next Maintenance:** 2026-05-12
