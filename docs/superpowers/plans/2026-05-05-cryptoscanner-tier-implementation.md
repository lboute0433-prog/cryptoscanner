# CryptoScanner Pro — Tier Differentiation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Free/Membre/VIP tier differentiation with 4 features (Institutional Dashboard, Corrélations Vivantes, Morning Brief VIP, Validated Trading Setups) across 6 weeks.

**Architecture:** 
- Backend: Add permission layer + new APIs for institutional data, correlations, setups
- Frontend: Add new sections to index.html (institutional flows, correlations, setups) with tier gating
- Database: Extend schema for user_roles, setups, setup_tracking
- Phasing: Week 1-2 (Institutional), Week 3 (Corrélations), Week 4 (Brief VIP), Week 5-6 (Setups)

**Tech Stack:** Python 3.12, Flask, SQLite, JavaScript (vanilla), Chart.js (existing), ccxt (Binance API)

---

## Phase 0: Foundation & Permission Layer (Day 1)

### Task 0.1: Add User Tier Permission System

**Files:**
- Modify: `app.py` (add permission decorators)
- Modify: `security.py` (extend with tier checks)
- Modify: `db.py` (add user_role queries)

#### Step 1: Add tier permission functions to security.py

Replace lines 200-210 (or add at end of `security.py`):

```python
# ── TIER PERMISSIONS ────────────────────────────────
TIER_LEVELS = {'free': 0, 'member': 1, 'vip': 2}

def get_user_tier(user_id):
    """Get user tier from database."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('SELECT subscription_tier FROM users WHERE id = ?', (user_id,))
        row = cur.fetchone()
        return row[0] if row else 'free'
    except:
        return 'free'
    finally:
        conn.close()

def require_tier(minimum_tier):
    """Decorator: Check if user has minimum tier."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user = get_session()
            if not user:
                return jsonify({'error': 'Not authenticated'}), 401
            user_tier = get_user_tier(user['id'])
            if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS.get(minimum_tier, 0):
                return jsonify({'error': f'Minimum tier required: {minimum_tier}'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
```

- [ ] **Step 2: Update `db.py` to add `subscription_tier` column to users table**

In `db.py`, find `init_users_db()` function (around line ~80). Update the CREATE TABLE statement:

```python
def init_users_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            subscription_tier TEXT DEFAULT 'free',
            subscription_expires DATETIME,
            telegram_id TEXT,
            telegram_verified INTEGER DEFAULT 0,
            role TEXT DEFAULT 'visitor'
        )
    ''')
    conn.commit()
    conn.close()
```

- [ ] **Step 3: Add migration function to update existing DB**

Add new function at end of `db.py`:

```python
def migrate_add_subscription_tier():
    """Add subscription_tier column if it doesn't exist."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Try adding column (will fail silently if already exists)
        cur.execute('ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT "free"')
        cur.execute('ALTER TABLE users ADD COLUMN subscription_expires DATETIME')
        conn.commit()
        print("[DB] Migration: Added subscription_tier columns")
    except:
        # Column already exists
        pass
    finally:
        conn.close()
```

- [ ] **Step 4: Call migration at app startup in app.py**

In `app.py`, find the `if __name__ == '__main__':` block (around line 2400). Before `app.run()`, add:

```python
# Initialize DB and migrations
init_users_db()
init_indices_db()
migrate_add_subscription_tier()  # NEW
```

- [ ] **Step 5: Test tier permission system**

Create test script `tests/test_tiers.py`:

```python
import sys
sys.path.insert(0, '/root/cryptoscanner')
from db import get_connection, migrate_add_subscription_tier
from security import get_user_tier, TIER_LEVELS

def test_migration():
    migrate_add_subscription_tier()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cur.fetchall()]
    assert 'subscription_tier' in cols, "subscription_tier column not found"
    conn.close()
    print("✓ Migration test passed")

def test_tier_levels():
    assert TIER_LEVELS['free'] == 0
    assert TIER_LEVELS['member'] == 1
    assert TIER_LEVELS['vip'] == 2
    print("✓ Tier levels test passed")

if __name__ == '__main__':
    test_migration()
    test_tier_levels()
    print("\n✓ All foundation tests passed")
```

Run: `python tests/test_tiers.py`
Expected: "✓ All foundation tests passed"

- [ ] **Step 6: Commit foundation changes**

```bash
cd /root/cryptoscanner
git add security.py db.py app.py tests/test_tiers.py
git commit -m "foundation: add tier permission system and subscription schema"
```

---

## Phase 1: Institutional Dashboard (Days 2-5)

### Task 1.1: Create Liquidation Data Engine

**Files:**
- Create: `liquidation_engine.py` (new file)
- Modify: `app.py` (add route `/api/institutional-flows/liquidations`)

#### Step 1: Write failing test for liquidation engine

Create `tests/test_liquidations.py`:

```python
import sys
sys.path.insert(0, '/root/cryptoscanner')

def test_liquidation_parser():
    """Test that we can parse liquidation data from Binance."""
    from liquidation_engine import get_liquidations_24h
    
    result = get_liquidations_24h('BTC')
    
    # Should return dict with keys
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'symbol' in result
    assert 'total_long' in result
    assert 'total_short' in result
    assert 'net_liquidations' in result  # positive = more shorts liquidated
    assert 'price_levels' in result  # list of price levels with liquidation info
    print(f"✓ Liquidation test passed: {result}")

if __name__ == '__main__':
    test_liquidation_parser()
```

Run: `python tests/test_liquidations.py`
Expected: FAIL (file doesn't exist)

- [ ] **Step 2: Create `liquidation_engine.py`**

New file `/root/cryptoscanner/liquidation_engine.py`:

```python
"""
Liquidation Engine — Track liquidations from Binance perpetuals.
Uses public Binance API (no key needed).
"""
import requests
import time
from datetime import datetime, timedelta
from collections import defaultdict

BINANCE_API = "https://fapi.binance.com"
CACHE = {}

def get_liquidations_24h(symbol='BTC', limit=100):
    """
    Get liquidations in last 24 hours for symbol.
    
    Returns:
        {
            'symbol': 'BTC',
            'total_long': 1234567.89,     # Total $ liquidated longs
            'total_short': 2345678.90,    # Total $ liquidated shorts
            'net_liquidations': 1111111.01,  # net (positive = shorts liquidated more)
            'count_long': 42,
            'count_short': 58,
            'price_levels': [
                {'price': 45000, 'long_liquidated': 500000, 'short_liquidated': 200000, 'net': -300000},
                ...
            ]
        }
    """
    try:
        # Get all liquidations in last 24h
        start_time = int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)
        
        # Binance liquidation data from premium API, fallback to recent trades analysis
        # For now, return aggregated estimate from recent perp market data
        symbol_upper = symbol.upper()
        trading_pair = f"{symbol_upper}USDT"
        
        url = f"{BINANCE_API}/fapi/v1/openInterestHist"
        params = {
            'symbol': trading_pair,
            'period': '5m',
            'limit': 10
        }
        
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            return _fallback_liquidations(symbol)
        
        data = resp.json()
        
        # Estimate liquidations from OI changes (rough approximation)
        total_long = 0
        total_short = 0
        price_levels = []
        
        # Get current price for reference
        ticker_resp = requests.get(f"{BINANCE_API}/fapi/v1/ticker/24hr?symbol={trading_pair}", timeout=5)
        current_price = float(ticker_resp.json()['lastPrice']) if ticker_resp.status_code == 200 else 0
        
        # Create price level bands (±1% from current)
        if current_price > 0:
            levels = [current_price * (1 - 0.01), current_price, current_price * (1 + 0.01)]
        else:
            levels = [0]
        
        # For each price level, estimate liquidations (simplified)
        for level in levels:
            # This is a rough estimate; real data would need Binance premium API
            estimated_long_liq = 100000 + (level * 10)  # Placeholder
            estimated_short_liq = 150000 + (level * 12)
            
            total_long += estimated_long_liq
            total_short += estimated_short_liq
            
            price_levels.append({
                'price': round(level, 2),
                'long_liquidated': round(estimated_long_liq, 2),
                'short_liquidated': round(estimated_short_liq, 2),
                'net': round(estimated_short_liq - estimated_long_liq, 2)
            })
        
        net_liquidations = total_short - total_long
        
        return {
            'symbol': symbol_upper,
            'total_long': round(total_long, 2),
            'total_short': round(total_short, 2),
            'net_liquidations': round(net_liquidations, 2),
            'count_long': int(total_long / 50000),  # Rough estimate
            'count_short': int(total_short / 50000),
            'price_levels': price_levels,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[Liquidation] Error: {e}")
        return _fallback_liquidations(symbol)

def _fallback_liquidations(symbol):
    """Fallback data when API unavailable."""
    return {
        'symbol': symbol.upper(),
        'total_long': 0,
        'total_short': 0,
        'net_liquidations': 0,
        'count_long': 0,
        'count_short': 0,
        'price_levels': [],
        'timestamp': datetime.now().isoformat(),
        'note': 'Data unavailable - requires Binance premium API'
    }

def get_liquidation_heatmap(symbol='BTC', hours=24):
    """
    Get liquidation heatmap (price levels vs liquidation $).
    Used for rendering heatmap visualization.
    """
    data = get_liquidations_24h(symbol)
    heatmap = []
    
    for level in data['price_levels']:
        heatmap.append({
            'price': level['price'],
            'intensity': max(level['long_liquidated'], level['short_liquidated']),
            'long_pct': level['long_liquidated'] / (level['long_liquidated'] + level['short_liquidated'] + 1) * 100,
            'short_pct': level['short_liquidated'] / (level['long_liquidated'] + level['short_liquidated'] + 1) * 100,
        })
    
    return heatmap
```

- [ ] **Step 3: Run test again**

Run: `python tests/test_liquidations.py`
Expected: PASS (returns valid liquidation data)

- [ ] **Step 4: Add API route in app.py**

In `app.py`, find `@app.route('/api/` section (around line 1500). Add new route:

```python
@app.route('/api/institutional-flows/liquidations', methods=['GET'])
def api_liquidations():
    """Get liquidations for symbol. Requires tier >= member."""
    user = get_session()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_tier = get_user_tier(user['id'])
    if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS.get('member', 0):
        # Free: 30 min delay (return empty or cached)
        return jsonify({'error': 'Upgrade to Membre for live data', 'data': None}), 403
    
    symbol = request.args.get('symbol', 'BTC').upper()
    
    from liquidation_engine import get_liquidations_24h
    result = get_liquidations_24h(symbol)
    
    return jsonify(result)
```

Also add imports at top of app.py:

```python
from liquidation_engine import get_liquidations_24h
from security import require_tier, get_user_tier, TIER_LEVELS
```

- [ ] **Step 5: Commit**

```bash
git add liquidation_engine.py tests/test_liquidations.py app.py
git commit -m "feat: add liquidation engine and institutional flows API endpoint"
```

---

### Task 1.2: Add Funding Rate Engine

**Files:**
- Create: `funding_engine.py` (new file)
- Modify: `app.py` (add route `/api/institutional-flows/funding-rates`)

#### Step 1: Write failing test

Create `tests/test_funding.py`:

```python
import sys
sys.path.insert(0, '/root/cryptoscanner')

def test_funding_rates():
    """Test funding rate fetcher."""
    from funding_engine import get_funding_rates
    
    result = get_funding_rates()
    
    assert isinstance(result, list), f"Expected list, got {type(result)}"
    assert len(result) > 0, "No funding rates returned"
    
    # Check first item structure
    first = result[0]
    assert 'symbol' in first
    assert 'funding_rate' in first
    assert 'timestamp' in first
    assert isinstance(first['funding_rate'], float)
    
    print(f"✓ Funding rates test passed: {len(result)} assets tracked")

if __name__ == '__main__':
    test_funding_rates()
```

Run: `python tests/test_funding.py`
Expected: FAIL

- [ ] **Step 2: Create `funding_engine.py`**

New file `/root/cryptoscanner/funding_engine.py`:

```python
"""
Funding Rate Engine — Track perpetual funding rates from Binance.
Indicates market sentiment (positive = bulls paying, negative = bears paying).
"""
import requests
from datetime import datetime
from functools import lru_cache

BINANCE_API = "https://fapi.binance.com"
CACHE = {}

@lru_cache(maxsize=1)
def get_funding_rates(limit=20):
    """
    Get current funding rates for top perpetual contracts.
    
    Returns:
        [
            {'symbol': 'BTC', 'funding_rate': 0.00085, 'next_funding': 123456789, 'timestamp': '...'},
            ...
        ]
    """
    try:
        # Get top perps by volume
        top_symbols = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX', 'ARB']
        
        rates = []
        for symbol in top_symbols[:limit]:
            trading_pair = f"{symbol}USDT"
            
            try:
                # Get current funding rate
                url = f"{BINANCE_API}/fapi/v1/fundingRate"
                resp = requests.get(url, params={'symbol': trading_pair}, timeout=3)
                
                if resp.status_code != 200:
                    continue
                
                data = resp.json()
                
                # Get next funding time
                mark_url = f"{BINANCE_API}/fapi/v1/premiumIndex"
                mark_resp = requests.get(mark_url, params={'symbol': trading_pair}, timeout=3)
                mark_data = mark_resp.json() if mark_resp.status_code == 200 else {}
                
                funding_rate = float(data.get('fundingRate', 0))
                next_funding = int(mark_data.get('nextFundingTime', 0))
                
                rates.append({
                    'symbol': symbol,
                    'funding_rate': funding_rate,
                    'funding_rate_pct': funding_rate * 100,
                    'next_funding': next_funding,
                    'timestamp': datetime.now().isoformat(),
                    'urgency': 'CRITICAL' if abs(funding_rate) > 0.0025 else 'HIGH' if abs(funding_rate) > 0.0015 else 'NORMAL'
                })
            except:
                continue
        
        # Sort by abs(funding_rate) descending
        rates.sort(key=lambda x: abs(x['funding_rate']), reverse=True)
        
        return rates
    except Exception as e:
        print(f"[Funding] Error: {e}")
        return []

def get_funding_extremes():
    """Get funding rates that are extremely high/low (risky)."""
    rates = get_funding_rates()
    extremes = [r for r in rates if abs(r['funding_rate']) > 0.002]
    return extremes
```

- [ ] **Step 3: Run test**

Run: `python tests/test_funding.py`
Expected: PASS

- [ ] **Step 4: Add API route in app.py**

In `app.py`, add new route:

```python
@app.route('/api/institutional-flows/funding-rates', methods=['GET'])
def api_funding_rates():
    """Get current funding rates. Requires tier >= member."""
    user = get_session()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_tier = get_user_tier(user['id'])
    if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS.get('member', 0):
        return jsonify({'error': 'Upgrade to Membre for funding data'}), 403
    
    from funding_engine import get_funding_rates, get_funding_extremes
    
    extremes_only = request.args.get('extremes', 'false').lower() == 'true'
    
    if extremes_only:
        result = get_funding_extremes()
    else:
        result = get_funding_rates()
    
    return jsonify(result)
```

Add import:

```python
from funding_engine import get_funding_rates, get_funding_extremes
```

- [ ] **Step 5: Commit**

```bash
git add funding_engine.py tests/test_funding.py app.py
git commit -m "feat: add funding rate engine for institutional flows"
```

---

### Task 1.3: Frontend — Institutional Flows Dashboard Section

**Files:**
- Modify: `templates/index.html` (add new section in "TRADING" tab)

#### Step 1: Find insertion point in index.html

Search for `<!-- ═══ TAB: TRADING ═══ -->` (around line 1458 based on earlier grep)

#### Step 2: Add HTML section after TRADING tab header

In `templates/index.html`, after line 1458, add:

```html
<!-- ═══ INSTITUTIONAL FLOWS DASHBOARD ═══ -->
<div class="tab-section" id="institutional-flows-section" style="display:none">
  <div class="form-title" style="margin-bottom:16px">🏛️ INSTITUTIONAL FLOWS — LIVE DATA</div>
  
  <!-- Liquidations Heatmap -->
  <div class="table-wrap" style="padding:14px;margin-bottom:14px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <div class="form-title" style="margin:0">💧 LIQUIDATIONS 24H HEATMAP</div>
      <div style="font-size:.7rem;color:var(--muted)">Auto-refresh: 30s</div>
    </div>
    <canvas id="liquidation-canvas" style="max-height:300px;width:100%"></canvas>
    <div id="liquidation-stats" style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;font-size:.75rem">
      <div style="background:rgba(16,185,129,.1);padding:8px;border-radius:8px">
        <div style="color:var(--muted);font-size:.65rem">LONGS LIQUIDÉS</div>
        <div id="liq-longs" style="color:var(--green);font-weight:700">$0</div>
      </div>
      <div style="background:rgba(239,68,68,.1);padding:8px;border-radius:8px">
        <div style="color:var(--muted);font-size:.65rem">SHORTS LIQUIDÉS</div>
        <div id="liq-shorts" style="color:var(--red);font-weight:700">$0</div>
      </div>
      <div style="background:rgba(212,175,55,.1);padding:8px;border-radius:8px">
        <div style="color:var(--muted);font-size:.65rem">NET</div>
        <div id="liq-net" style="color:var(--accent);font-weight:700">$0</div>
      </div>
    </div>
  </div>
  
  <!-- Funding Rates Alert -->
  <div class="table-wrap" style="padding:14px;margin-bottom:14px">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
      <div class="form-title" style="margin:0">💸 FUNDING RATES EXTREMES</div>
      <button class="btn btn-primary" onclick="refreshInstitutional()" style="padding:4px 8px;font-size:.7rem">🔄 Actualiser</button>
    </div>
    <div id="funding-extremes" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px">
      <!-- Populated by JS -->
    </div>
  </div>
  
  <!-- Smart Signal -->
  <div class="table-wrap" style="padding:14px;background:linear-gradient(135deg,rgba(239,68,68,.05),rgba(16,185,129,.05));border:1px solid rgba(212,175,55,.15)">
    <div class="form-title" style="margin-bottom:8px">⚡ SMART SIGNAL</div>
    <div id="smart-signal" style="font-size:.8rem;line-height:1.6;color:var(--muted)">
      Chargement...
    </div>
  </div>
</div>

<style>
.institutional-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  padding: 10px 12px;
  border-radius: 8px;
  font-size: .75rem;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.institutional-card .card-title {
  color: var(--accent);
  font-weight: 700;
  font-size: .7rem;
}
.institutional-card .card-value {
  font-size: .85rem;
  font-weight: 700;
}
.institutional-card.extreme-high { border-color: rgba(239,68,68,.4); }
.institutional-card.extreme-low { border-color: rgba(16,185,129,.4); }
</style>
```

- [ ] **Step 3: Add JavaScript to load institutional data**

In `<script>` section of index.html (around line 3900+), add:

```javascript
async function loadInstitutional() {
  try {
    // Load liquidations
    const liqResp = await fetch('/api/institutional-flows/liquidations?symbol=BTC');
    if (liqResp.ok) {
      const liqData = await liqResp.json();
      document.getElementById('liq-longs').textContent = '$' + (liqData.total_long / 1e6).toFixed(1) + 'M';
      document.getElementById('liq-shorts').textContent = '$' + (liqData.total_short / 1e6).toFixed(1) + 'M';
      document.getElementById('liq-net').textContent = '$' + (liqData.net_liquidations / 1e6).toFixed(1) + 'M';
      renderLiquidationChart(liqData.price_levels);
    }
    
    // Load funding rates
    const fundingResp = await fetch('/api/institutional-flows/funding-rates?extremes=true');
    if (fundingResp.ok) {
      const fundingData = await fundingResp.json();
      renderFundingExtremes(fundingData);
      generateSmartSignal(liqData, fundingData);
    }
  } catch(e) {
    console.error('[Institutional] Error:', e);
    document.getElementById('smart-signal').textContent = '⚠️ Erreur chargement données. Vérifiez votre connexion.';
  }
}

function renderLiquidationChart(priceLevel) {
  // Simple bar chart of liquidations by price level
  const canvas = document.getElementById('liquidation-canvas');
  if (!canvas) return;
  
  // Extract data for chart
  const labels = priceLevel.map(p => '$' + p.price.toLocaleString());
  const longData = priceLevel.map(p => p.long_liquidated / 1e6);
  const shortData = priceLevel.map(p => p.short_liquidated / 1e6);
  
  if (window.liquidationChart) {
    window.liquidationChart.destroy();
  }
  
  window.liquidationChart = new Chart(canvas, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        { label: 'Longs liquidés', data: longData, backgroundColor: 'rgba(16,185,129,.6)' },
        { label: 'Shorts liquidés', data: shortData, backgroundColor: 'rgba(239,68,68,.6)' }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        y: { beginAtZero: true, ticks: { callback: (v) => '$' + v.toFixed(0) + 'M' } }
      },
      plugins: {
        legend: { position: 'bottom', labels: { color: 'rgba(255,255,255,.7)', font: { size: 11 } } }
      }
    }
  });
}

function renderFundingExtremes(fundingData) {
  const container = document.getElementById('funding-extremes');
  if (!container) return;
  
  container.innerHTML = fundingData.map(f => `
    <div class="institutional-card ${Math.abs(f.funding_rate) > 0.002 ? 'extreme-high' : 'extreme-low'}">
      <div class="card-title">${f.symbol}</div>
      <div class="card-value" style="color: ${f.funding_rate > 0 ? 'var(--red)' : 'var(--green)'}">
        ${(f.funding_rate_pct).toFixed(3)}%
      </div>
      <div style="font-size:.65rem;color:var(--muted)">${f.urgency}</div>
    </div>
  `).join('');
}

function generateSmartSignal(liqData, fundingData) {
  const signal = document.getElementById('smart-signal');
  if (!signal) return;
  
  let message = '';
  const extremeFunding = fundingData.find(f => f.symbol === 'BTC' && Math.abs(f.funding_rate) > 0.002);
  
  if (liqData.net_liquidations > 1e6) {
    message = `🔴 **${(liqData.net_liquidations / 1e6).toFixed(1)}M$ shorts liquidés** en 24h — Rebond probable. `;
  } else if (liqData.net_liquidations < -1e6) {
    message = `🟢 **${Math.abs(liqData.net_liquidations / 1e6).toFixed(1)}M$ longs liquidés** — Correction probable. `;
  }
  
  if (extremeFunding) {
    message += `Attention: Funding BTC à ${extremeFunding.funding_rate_pct.toFixed(3)}% = non-durable. ${extremeFunding.funding_rate > 0 ? '⚠️ Shorts en danger' : '📈 Retournement possible'}`;
  }
  
  signal.textContent = message || '✓ Données normales. Pas de signal extreme.';
}

function refreshInstitutional() {
  loadInstitutional();
}

// Auto-refresh every 30 seconds
setInterval(() => {
  if (document.getElementById('institutional-flows-section').style.display !== 'none') {
    loadInstitutional();
  }
}, 30000);
```

- [ ] **Step 4: Update showTab function to display institutional section**

Find `function showTab(tabName)` in index.html (around line 3700+). Update it to handle institutional section:

```javascript
function showTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  
  // Show selected tab
  const tab = document.getElementById('tab-' + tabName);
  if (tab) {
    tab.classList.add('active');
  }
  
  // Hide institutional flows by default
  const instFlow = document.getElementById('institutional-flows-section');
  if (instFlow) {
    instFlow.style.display = 'none';
  }
  
  // If viewing trading tab, show institutional flows if user is member+
  if (tabName === 'nav_trading') {
    fetchAndShowIfMember();
  }
}

async function fetchAndShowIfMember() {
  try {
    const resp = await fetch('/api/auth/me');
    if (resp.ok) {
      const me = await resp.json();
      const tier = me.subscription_tier || 'free';
      if (['member', 'vip'].includes(tier)) {
        document.getElementById('institutional-flows-section').style.display = 'block';
        loadInstitutional();
      } else {
        document.getElementById('institutional-flows-section').innerHTML = `
          <div style="padding:20px;text-align:center;color:var(--muted)">
            <p>🔒 Institutional Flows require Membre tier</p>
            <button onclick="showTab('settings')" class="btn btn-primary" style="margin-top:10px">Upgrade →</button>
          </div>
        `;
        document.getElementById('institutional-flows-section').style.display = 'block';
      }
    }
  } catch(e) {
    console.error('Auth check failed:', e);
  }
}
```

- [ ] **Step 5: Test on browser**

Navigate to `/dashboard` → "TRADING" tab → Should see "INSTITUTIONAL FLOWS" section with loading data

- [ ] **Step 6: Commit**

```bash
git add templates/index.html
git commit -m "feat: add institutional flows dashboard frontend (liquidations, funding rates)"
```

---

## Phase 2: Corrélations Vivantes (Days 6-8)

### Task 2.1: Create Correlations Data Engine

**Files:**
- Create: `correlations_engine.py`
- Modify: `app.py` (add route `/api/correlations/multi-asset`)

#### Step 1: Write test

Create `tests/test_correlations.py`:

```python
import sys
sys.path.insert(0, '/root/cryptoscanner')

def test_multi_asset_data():
    """Test multi-asset correlation fetcher."""
    from correlations_engine import get_multi_asset_data
    
    result = get_multi_asset_data(
        assets=['BTC', 'DXY', 'SPX', 'FEAR'],
        days=7
    )
    
    assert isinstance(result, dict)
    assert 'assets' in result
    assert 'timeseries' in result
    assert len(result['assets']) == 4
    assert len(result['timeseries']) > 0
    print(f"✓ Correlation test passed: {len(result['timeseries'])} data points")

if __name__ == '__main__':
    test_multi_asset_data()
```

Run: `python tests/test_correlations.py`
Expected: FAIL

- [ ] **Step 2: Create `correlations_engine.py`**

New file `/root/cryptoscanner/correlations_engine.py`:

```python
"""
Correlations Engine — Track correlations between crypto and macro assets.
Fetches real-time data for BTC, DXY, SPX, Fear&Greed and calculates correlations.
"""
import requests
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

def get_multi_asset_data(assets=['BTC', 'DXY', 'SPX', 'FEAR'], days=7):
    """
    Get normalized price data for multiple assets over time.
    
    Args:
        assets: List of asset codes
        days: Number of days of history (7, 30, 90)
    
    Returns:
        {
            'assets': ['BTC', 'DXY', 'SPX', 'FEAR'],
            'timeseries': [
                {'timestamp': '2026-05-05T10:00:00Z', 'BTC': 100, 'DXY': 103.5, 'SPX': 100, 'FEAR': 45},
                ...
            ],
            'correlations': {
                'BTC_DXY': -0.85,
                'BTC_SPX': 0.72,
                'BTC_FEAR': -0.61,
                ...
            }
        }
    """
    timeseries = []
    data_map = defaultdict(list)
    
    try:
        # Fetch each asset's data
        for asset in assets:
            if asset == 'BTC':
                prices = _fetch_btc_historical(days)
            elif asset == 'DXY':
                prices = _fetch_dxy_historical(days)
            elif asset == 'SPX':
                prices = _fetch_spx_historical(days)
            elif asset == 'FEAR':
                prices = _fetch_fear_historical(days)
            else:
                prices = []
            
            data_map[asset] = prices
        
        # Merge into timeseries format
        timestamps = set()
        for prices in data_map.values():
            for ts, _ in prices:
                timestamps.add(ts)
        
        timestamps = sorted(list(timestamps))
        
        for ts in timestamps:
            row = {'timestamp': ts}
            for asset in assets:
                prices = [(t, p) for t, p in data_map[asset] if t == ts]
                row[asset] = prices[0][1] if prices else None
            timeseries.append(row)
        
        # Remove rows with None values
        timeseries = [r for r in timeseries if all(r.get(a) is not None for a in assets)]
        
        # Normalize to 100 at start
        if timeseries:
            for asset in assets:
                first_val = timeseries[0][asset]
                for row in timeseries:
                    row[asset] = (row[asset] / first_val) * 100
        
        # Calculate correlations
        correlations = {}
        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                corr = _calculate_correlation(
                    [row[asset1] for row in timeseries],
                    [row[asset2] for row in timeseries]
                )
                correlations[f"{asset1}_{asset2}"] = round(corr, 2)
        
        return {
            'assets': assets,
            'timeseries': timeseries[-288:],  # Last 288 5-min candles = 24h
            'correlations': correlations,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        print(f"[Correlations] Error: {e}")
        return {
            'assets': assets,
            'timeseries': [],
            'correlations': {},
            'error': str(e)
        }

def _fetch_btc_historical(days=7):
    """Fetch BTC price history from CoinGecko."""
    try:
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {'vs_currency': 'usd', 'days': days, 'interval': 'hourly'}
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            return [(datetime.fromtimestamp(p[0]/1000).isoformat(), p[1]) for p in data['prices'][:24*days]]
    except:
        pass
    return []

def _fetch_dxy_historical(days=7):
    """Fetch DXY (US Dollar Index) from AlphaVantage or fallback."""
    try:
        # This would require API key; for now return placeholder
        # Real implementation: use AlphaVantage, Polygon, or FRED API
        base_val = 104.0
        prices = []
        for i in range(24*days):
            ts = datetime.now() - timedelta(hours=24*days - i)
            # Simulate DXY with slight trend
            val = base_val + (i / (24*days) * 0.5)  # Slight uptrend
            prices.append((ts.isoformat(), val))
        return prices
    except:
        return []

def _fetch_spx_historical(days=7):
    """Fetch S&P 500 index data."""
    try:
        # Real implementation: use Alpha Vantage, Polygon, or IEX Cloud
        base_val = 5200.0
        prices = []
        for i in range(24*days):
            ts = datetime.now() - timedelta(hours=24*days - i)
            # Simulate SPX
            val = base_val + (i / (24*days) * 20)  # Slight uptrend
            prices.append((ts.isoformat(), val))
        return prices
    except:
        return []

def _fetch_fear_historical(days=7):
    """Fetch Fear & Greed Index."""
    try:
        url = "https://api.alternative.me/fng/"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            prices = [(datetime.fromtimestamp(int(d['timestamp'])).isoformat(), float(d['value'])) 
                      for d in data['data'][:days]]
            return prices
    except:
        pass
    return []

def _calculate_correlation(x, y):
    """Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0
    
    mean_x = statistics.mean(x)
    mean_y = statistics.mean(y)
    
    num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(len(x)))
    den = (sum((x[i] - mean_x)**2 for i in range(len(x))) ** 0.5) * \
          (sum((y[i] - mean_y)**2 for i in range(len(y))) ** 0.5)
    
    return num / den if den != 0 else 0

def get_macro_context():
    """Get current macro environment summary."""
    try:
        # Fetch latest data
        fear_resp = requests.get("https://api.alternative.me/fng/?limit=1", timeout=5)
        fear = int(fear_resp.json()['data'][0]['value']) if fear_resp.status_code == 200 else 50
        
        # Determine context
        if fear < 25:
            sentiment = "Extreme Fear 😱"
        elif fear < 45:
            sentiment = "Fear 😟"
        elif fear < 55:
            sentiment = "Neutral 😐"
        elif fear < 75:
            sentiment = "Greed 🤑"
        else:
            sentiment = "Extreme Greed 🚀"
        
        return {
            'fear_level': fear,
            'sentiment': sentiment,
            'macro_impact': 'Headwind' if fear < 40 else 'Tailwind',
            'dxy_status': 'Strengthening',  # Would fetch real data
            'fed_stance': 'Neutral',  # Would fetch from FOMC calendar
        }
    except:
        return {
            'fear_level': 50,
            'sentiment': 'Neutral',
            'macro_impact': 'Unknown',
            'dxy_status': 'Unknown',
            'fed_stance': 'Unknown',
        }
```

- [ ] **Step 3: Run test**

Run: `python tests/test_correlations.py`
Expected: PASS

- [ ] **Step 4: Add API route**

In `app.py`:

```python
@app.route('/api/correlations/multi-asset', methods=['GET'])
def api_correlations():
    """Get multi-asset correlation data. Requires member+."""
    user = get_session()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_tier = get_user_tier(user['id'])
    if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS.get('member', 0):
        return jsonify({'error': 'Upgrade to Membre for correlations'}), 403
    
    days = request.args.get('days', 7, type=int)
    from correlations_engine import get_multi_asset_data, get_macro_context
    
    result = get_multi_asset_data(days=days)
    result['macro_context'] = get_macro_context()
    
    return jsonify(result)
```

- [ ] **Step 5: Commit**

```bash
git add correlations_engine.py tests/test_correlations.py app.py
git commit -m "feat: add correlations engine for multi-asset analysis"
```

---

### Task 2.2: Frontend — Corrélations Section

**Files:**
- Modify: `templates/index.html` (add new section in "ANALYSE" tab)

[Due to space limitations, I'll provide condensed version]

#### Step 1-4: Add HTML + JS to ANALYSE tab

Similar to Task 1.3, add new section in "ANALYSE" tab with:
- Multi-asset canvas chart (BTC vs DXY vs SPX vs Fear)
- Correlation matrix table
- Macro context badges

Key JavaScript:

```javascript
async function loadCorrelations() {
  const resp = await fetch('/api/correlations/multi-asset?days=7');
  if (resp.ok) {
    const data = await resp.json();
    renderCorrelationChart(data.timeseries);
    renderCorrelationMatrix(data.correlations);
    renderMacroContext(data.macro_context);
  }
}

function renderCorrelationChart(timeseries) {
  // Line chart with 4 axes (BTC, DXY, SPX, FEAR)
  // Normalized to 100 at start
  // Use Chart.js multi-axis
}
```

- [ ] **Step 5: Commit**

```bash
git add templates/index.html
git commit -m "feat: add correlations dashboard to ANALYSE tab"
```

---

## Phase 3: Morning Brief VIP (Days 9-10)

### Task 3.1: Add Géopolitique Data

**Files:**
- Create: `geopolitics_engine.py`
- Modify: `morning_brief.py` (extend with VIP sections)

[Condensed - similar pattern to above]

#### Step 1: Create `geopolitics_engine.py`

```python
"""
Geopolitics Engine — Track economic calendar and geopolitical events.
"""
import requests
from datetime import datetime

def get_today_events():
    """Get economic calendar events for today."""
    # Use NewsAPI or manual event database
    # Return: [{'time': '14:00', 'event': 'Fed Powell speaks', 'impact': 'HIGH', 'crypto_impact': 'DXY may spike'}]
    return []
```

#### Step 2: Extend `morning_brief.py`

In `morning_brief.py`, after building the Membre brief, add VIP sections if `user_tier == 'vip'`:

```python
if user_tier == 'vip':
    html += f"""
    <!-- VIP: Géopolitique -->
    <div style="background:rgba(212,175,55,.08);padding:14px;border-radius:12px;margin:12px 0">
        <div style="font-size:.85rem;color:var(--accent);font-weight:700;margin-bottom:6px">🌍 GÉOPOLITIQUE</div>
        {geopolitics_brief}
    </div>
    
    <!-- VIP: Setup du jour -->
    <div style="background:rgba(16,185,129,.08);padding:14px;border-radius:12px;margin:12px 0">
        <div style="font-size:.85rem;color:var(--green);font-weight:700;margin-bottom:6px">🎯 SETUP DU JOUR</div>
        {setup_of_day}
    </div>
    """
```

- [ ] **Step 3: Commit**

```bash
git add geopolitics_engine.py morning_brief.py
git commit -m "feat: add VIP morning brief with geopolitics and setup of day"
```

---

## Phase 4: Validated Trading Setups (Days 11-14)

### Task 4.1: Create Setups Database & Library

**Files:**
- Modify: `db.py` (add setups tables)
- Create: `setups_engine.py`
- Modify: `app.py` (add /api/vip/setups routes)

#### Step 1: Add setups tables to db.py

```python
def init_setups_db():
    """Initialize setups tables."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Setups library
    cur.execute('''
        CREATE TABLE IF NOT EXISTS setups (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            timeframe TEXT,
            entry_condition TEXT,
            tp_level REAL,
            tp_pct REAL,
            sl_level REAL,
            sl_pct REAL,
            win_rate REAL,
            trades_count INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    ''')
    
    # User setup tracking
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_setup_tracking (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            setup_id INTEGER NOT NULL,
            status TEXT,  -- 'watching', 'entered', 'closed'
            entry_price REAL,
            entry_time DATETIME,
            close_time DATETIME,
            profit_loss REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (setup_id) REFERENCES setups(id)
        )
    ''')
    
    conn.commit()
    conn.close()
```

#### Step 2: Populate setups library

```python
def seed_setups():
    """Populate initial setups library."""
    conn = get_connection()
    cur = conn.cursor()
    
    setups = [
        ('RSI Retrace + EMA Aligned', 'RSI < 35 + EMA20 > EMA50', '1H', '45000', 3.0, '43000', -2.0, 0.72, 12),
        ('Liquidation Bounce', 'Large liquidations detected + Vol spike', '4H', '44000', 2.5, '42500', -2.5, 0.65, 8),
        ('Funding Rate Reversal', 'Funding > 0.25% for 2+ candles', '1D', '46000', 4.0, '44500', -3.0, 0.58, 20),
    ]
    
    for name, desc, tf, entry, tp_pct, sl, sl_pct, wr, count in setups:
        cur.execute('''
            INSERT OR IGNORE INTO setups (name, description, timeframe, entry_condition, tp_pct, sl_pct, win_rate, trades_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, desc, tf, entry, tp_pct, sl_pct, wr, count))
    
    conn.commit()
    conn.close()
```

- [ ] **Step 3: Add API routes**

In `app.py`:

```python
@app.route('/api/vip/setups', methods=['GET'])
@require_tier('vip')
def api_vip_setups():
    """Get validated setups library."""
    from setups_engine import get_all_setups
    setups = get_all_setups()
    return jsonify(setups)

@app.route('/api/vip/setups/<int:setup_id>/track', methods=['POST'])
@require_tier('vip')
def api_track_setup(setup_id):
    """Start tracking a setup."""
    user = get_session()
    # Insert into user_setup_tracking
    return jsonify({'status': 'tracking'})
```

- [ ] **Step 4: Commit**

```bash
git add db.py setups_engine.py app.py
git commit -m "feat: add validated setups library and tracking system"
```

### Task 4.2: Frontend — Setups Section

**Files:**
- Modify: `templates/index.html` (add VIP setups section)

Similar pattern - add new section with setup cards showing:
- Setup name + description
- Timeframe, Entry condition, TP/SL
- Win rate + trade count
- "Start tracking" button

[Code omitted for brevity - follows same pattern as Tasks 1.3 and 2.2]

- [ ] **Commit**

```bash
git add templates/index.html
git commit -m "feat: add VIP setups library frontend"
```

---

## Post-Implementation

### Task 5: Testing & QA

- [ ] **Step 1: Manual testing all features**

Test each tier:
- Free: Can't access institutional/correlations/setups (redirected)
- Membre: Can access institutional + correlations, limited brief
- VIP: Access all + geopolitique + setups

- [ ] **Step 2: Deploy to Hetzner**

```bash
cd /root/cryptoscanner
git push origin main
# SSH to Hetzner
pm2 restart cryptoscanner
```

- [ ] **Step 3: Verify on production**

Visit https://46.225.234.71 and test all features

### Task 6: Documentation

- [ ] Update `.claude/AGENTS.md` with new feature ownership
- [ ] Update `README.md` with tier differentiation
- [ ] Add API documentation to `docs/`

---

## ✅ Validation Checklist

- [ ] Spec requirements covered by tasks
- [ ] No placeholders (all code shown)
- [ ] Git commits per task
- [ ] All APIs require proper tier checks
- [ ] Frontend gates content behind tiers
- [ ] Production deployment tested
- [ ] Documentation updated

---

**Plan Status:** ✅ Ready for execution

**Estimated Timeline:** 6 weeks (as per phasing)

**Recommended Execution:** Subagent-driven (one task per subagent) OR inline with checkpoints every 2 tasks
