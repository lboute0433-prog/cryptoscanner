# CryptoScanner Pro — VIP Features (Phase 2)

**Last Updated:** 2026-05-05  
**Status:** Production Ready

---

## Feature 1: Institutional Dashboard

### Overview
Real-time monitoring of institutional activity, liquidations, and funding rates. Designed for traders seeking early signals from whale activity and exchange mechanics.

### Components

#### 1.1 Liquidations Heatmap
**API Endpoint:** `GET /api/institutional-flows/liquidations?symbol=BTC`

Displays liquidation cascade data:
- Long/short liquidations by price level
- Volume-weighted average liquidation prices
- Heatmap colors: Red (heavy liquidation zones), Yellow (moderate)
- Updates: Real-time (5-second refresh)

**Data Source:** Binance public API (`GET /fapi/v1/openInterest`)

**Frontend Component:**
- Grid layout with symbol filters (BTC, ETH, SOL, etc.)
- Interactive heatmap (canvas-based)
- Color scale: 0 (no liquidations) → 10 (extreme liquidation zone)

#### 1.2 Funding Rates
**API Endpoint:** `GET /api/institutional-flows/funding-rates`

Displays perpetual futures funding rates:
- Positive rate: Longs pay shorts (bullish signal)
- Negative rate: Shorts pay longs (bearish signal)
- Useful for sentiment analysis (high positive = overlevered longs)

**Data Source:** Binance public API (`GET /fapi/v1/fundingRate`)

**Frontend Component:**
- Table with 24h funding rate, current rate, historical 7d chart
- Color-coded: Green (positive), Red (negative)
- Auto-refresh every 30 seconds

#### 1.3 Whale Tracking
**API Endpoint:** `GET /api/institutional-flows/whales`

Monitors large address movements:
- Whale addresses (>$100k transfers)
- Transfer direction (exchange inflow = selling pressure, outflow = accumulation)
- Volume and timestamp

**Data Source:** Blockchain explorers (Etherscan, Solscan) integration via news_macro.py

**Frontend Component:**
- Recent whale transactions list
- Filter by symbol, time range
- Alert triggers for large movements

### Use Case
Senior trader monitors liquidation levels before high-impact news. Sees heavy BTC shorts underwater at $45,000 mark. When economic data comes, expects volatility but knows shorts won't cascade below that level. Positions accordingly. Funding rates confirm overlevered longs (positive 0.15% per 8h), validating bias to fade rallies.

---

## Feature 2: Live Correlations

### Overview
Multi-asset correlation analysis in real-time. Helps traders understand which assets move together and spot divergences (risk management, pair trading).

### Components

#### 2.1 Correlation Matrix
**API Endpoint:** `GET /api/correlations/matrix?symbols=BTC,ETH,BNB,SOL`

Displays Pearson correlation coefficients:
- Range: -1 (perfectly inverse) to +1 (perfectly correlated)
- Matrix updated every 5 minutes (based on 24h rolling window)
- Shows 9x9 grid (top 9 assets by default)

**Calculation Method:**
```
Pearson r = Cov(X,Y) / (σX × σY)
```

**Interpretation:**
- \>0.7: High correlation (assets move together)
- 0.3-0.7: Moderate correlation
- <0.3: Low correlation (independent movement)
- <0: Inverse correlation (one up, one down)

**Frontend Component:**
- Interactive heatmap (canvas-based visualization)
- Color scale: Dark blue (inverse) → Red (highly correlated)
- Hover shows exact correlation value
- Clickable to drill into correlation strength over time

#### 2.2 Asset Clustering
**API Endpoint:** `GET /api/correlations/clusters?symbols=BTC,ETH,SOL`

Groups assets by correlation similarity:
- Cluster 1: BTC, ETH (high correlation 0.92)
- Cluster 2: SOL, AVAX (correlation 0.78)
- Cluster 3: Stablecoins (near-zero correlation)
- Outliers: Assets with unique price movement

**Algorithm:** K-means clustering (k=3 default) on correlation matrix

**Use Case:**
- **Portfolio risk:** If holding both BTC and ETH, they're correlated — diversification limited
- **Pair trading:** Find assets with recently broken correlations (divergence signal)
- **Hedging:** Stablecoins/fiat show zero correlation — optimal hedges

#### 2.3 Correlation Over Time
Tracks correlation strength historically:
- Shows when BTC-ETH correlation was 0.95 vs current 0.88
- Identifies correlation regime changes (useful for regime switches)
- Visualization: Line chart of rolling 24h correlation

### Data Source
Binance public API (1-hour OHLCV, last 24 bars):
```
GET /api/v3/klines?symbol=BTCUSDT&interval=1h&limit=24
```

No authentication needed (public endpoints).

### Example Output
```json
{
  "correlation_matrix": [
    [1.0, 0.915, 0.823, 0.671],
    [0.915, 1.0, 0.889, 0.734],
    [0.823, 0.889, 1.0, 0.812],
    [0.671, 0.734, 0.812, 1.0]
  ],
  "symbols": ["BTC", "ETH", "BNB", "SOL"],
  "clusters": {
    "cluster_1": ["BTC", "ETH"],
    "cluster_2": ["BNB", "SOL"]
  },
  "strong_correlations": [
    {"pair": "BTC-ETH", "correlation": 0.915},
    {"pair": "BNB-SOL", "correlation": 0.812}
  ]
}
```

### Use Case
Portfolio manager holds diversified crypto: BTC (60%), ETH (30%), SOL (10%). Correlation matrix shows BTC-ETH at 0.92 (highly correlated despite different fundamentals). Realizes portfolio is effectively 90% exposed to "large-cap crypto" factor. Rebalances to add low-correlation assets (stablecoins, farming tokens).

---

## Feature 3: VIP Morning Brief (Enhanced)

### Overview
Strategic macro/geopolitical analysis for VIP traders. Integrates economic calendar, regulatory sentiment, and crypto-specific catalysts into one concise brief.

### Components

#### 3.1 Risk Score (1-10 Scale)
**Calculation:**
- Baseline: 5 (neutral)
- Adjust +1 for each hawkish central bank event (ECB hiking rates → harder for risk assets)
- Adjust -1 for each dovish event (Fed pausing hikes → risk-on)
- Adjust ±1.5 for regulatory news (negative regulation = +risk, positive ETF approval = -risk)
- Final: Clamp to 1-10 scale

**Example:**
- Risk score 2 (risk-on): Fed cutting rates, positive regulation, dovish CB signals
- Risk score 8 (risk-off): Hawkish ECB, banking crisis fears, crackdown news

#### 3.2 Economic Calendar
Fetches high-impact events:
- US Non-Farm Payroll (NFP) — every 1st Friday
- CPI/PCE releases — strong correlation with crypto (inflation → risk-off)
- ECB interest rate decisions
- China GDP data

**Event Filtering:**
- Only "High", "Critical", "Major" importance levels shown
- Upcoming (24h) + Recent releases (last 24h)

**Crypto Impact Assessment:**
```
If event = USD inflation data:
  IF actual > forecast: "Hawkish surprise" → bearish for risk assets
  IF actual < forecast: "Dovish surprise" → bullish for crypto
```

#### 3.3 Regulatory News Feed
Scrapes for keywords:
- "SEC", "CFTC", "regulation", "ban", "approve", "ETF", "license"
- Categorizes by sentiment:
  - Positive: "SEC approves Bitcoin ETF" → +5 impact
  - Negative: "China bans crypto" → -5 impact
  - Neutral: "Regulatory framework discussion"

**Sectors Affected:**
- DeFi (decentralized platforms)
- Stablecoins (USDC, USDT regulation)
- Exchanges (CEX licensing)
- Altcoins (token classification)
- CBDC (digital currencies)

#### 3.4 VIP Insights (AI-Generated)
Strategic bullet points for decision-making:

**Example 1 (Risk Score 8 — Risk-Off):**
> "🔴 Elevated geopolitical risk — tighten stops, consider de-risking non-core positions"

**Example 2 (Dovish Catalyst Incoming):**
> "📉 Dovish catalyst incoming: ECB rate hold — potential support for risk assets"

**Example 3 (Regulatory Positive):**
> "✅ Positive regulatory momentum (3 items) — institutional adoption likely to accelerate"

### Data Sources
1. **Economic Calendar:** news_macro.py (`fetch_economic_calendar()`)
2. **Regulatory News:** news_macro.py (`get_news_from_db()`)
3. **Crypto-Specific Impact:** Internal heuristics (asset correlation, sector exposure)

### Example Output
```json
{
  "economic_calendar": {
    "upcoming_events": [
      {
        "title": "US Non-Farm Payroll",
        "currency": "USD",
        "time": "2026-05-09T12:30:00Z",
        "importance": "critical",
        "impact_crypto": {
          "score": 9,
          "direction": "hawkish",
          "reasoning": "USD event, highest correlation"
        }
      }
    ],
    "recent_releases": [
      {
        "title": "US CPI YoY",
        "actual": "3.4%",
        "forecast": "3.5%",
        "assessment": "Better than expected",
        "impact_crypto": {
          "score": 7,
          "direction": "dovish"
        }
      }
    ]
  },
  "regulatory_news": [
    {
      "title": "SEC Approves Bitcoin Spot ETF",
      "sentiment": "positive",
      "sectors_affected": ["Major Assets", "Exchanges"]
    }
  ],
  "risk_score": 4.2,
  "sentiment": "risk-on",
  "vip_insights": [
    "🟢 Favorable geopolitical backdrop — risk-on conditions support alt season",
    "✅ Positive regulatory momentum — institutional adoption likely"
  ]
}
```

### Use Case
CTO wakes at 6 AM EST, opens CryptoScanner. VIP Brief shows:
- Risk score: 3 (risk-on)
- Dovish Fed signals
- 2 positive regulatory items
- NFP coming Friday (bullish if weak jobs)

Decision: Increase BTC/ETH long exposure. Set stop-loss above NFP expectations. Plan to take profits if positive NFP surprises to the upside.

---

## Feature 4: Trading Setups Library

### Overview
Database of validated trading setups with real historical trade examples. Each setup shows entry/exit rules, statistics (win rate, risk/reward), and proof (actual trades).

### Components

#### 4.1 Setup Schema

Each setup includes:

| Field | Example | Purpose |
|-------|---------|---------|
| name | "BTC Breakout Momentum" | Human-readable identifier |
| asset | "BTC" | Trading pair |
| pattern_type | "breakout" | breakout, divergence, retest, support, resistance |
| timeframe | "4h" | 1h, 4h, 1d |
| entry_rule | "Break above 20-day resistance with volume > 150% MA" | Entry condition |
| exit_rule | "Take profit at 1.5R or stop loss hit" | Exit condition |
| stop_loss_rule | "5% below breakout point" | Risk management |
| take_profit_rule | "1.5x risk-reward ratio" | Profit target |
| risk_reward_ratio | 1.5 | Risk per trade / Potential reward |
| avg_win_rate | 0.68 | 68% of trades win |
| total_trades | 50 | Historical examples |
| winning_trades | 34 | 34 out of 50 |
| difficulty | "Intermediate" | Beginner, Intermediate, Advanced |
| market_condition | "trending" | trending, consolidating, ranging |

#### 4.2 Filtering & Search

**API Endpoints:**
- `GET /api/setups/all` — All setups, sorted by win rate
- `GET /api/setups/asset/BTC` — BTC-only setups
- `GET /api/setups/pattern/breakout` — Breakout setups only
- `GET /api/setups/high-probability` — >60% win rate (default threshold)

**Frontend Filters:**
- Asset: BTC, ETH, SOL, Show All
- Difficulty: Beginner, Intermediate, Advanced
- Min Win Rate: Slider 50%-100%
- Pattern Type: All, Breakout, Divergence, Retest

#### 4.3 Trade Examples

Each setup has real trade history:

| Date | Entry | Exit | Stop | Profit | Duration | Result |
|------|-------|------|------|--------|----------|--------|
| 2025-11-15 | $42,500 | $46,875 | $40,375 | +$2,375 | 4.2h | WIN |
| 2025-11-18 | $43,200 | $40,960 | $41,040 | -$1,200 | 2.1h | LOSS |
| 2025-11-22 | $44,100 | $48,510 | $41,895 | +$3,410 | 6.8h | WIN |

**Display:** Modal/detail view shows last 10 trades, statistics, equity curve

#### 4.4 Performance Metrics

For each setup, calculated from examples:

```
Win Rate = Winning Trades / Total Trades
Avg Win = Σ(Winning Trade Profits) / Winning Trades
Avg Loss = Σ(Losing Trade Losses) / Losing Trades
Profit Factor = Gross Profit / Gross Loss
Equity Curve = Cumulative PnL over time
```

### Data Source

Internal database (SQLite):
- `trading_setups` table — Setup definitions
- `setup_examples` table — Real trade history

No external API calls needed (pure database read).

### Sample Setups (Seeded)

**Setup 1: BTC Breakout Momentum**
- Pattern: Breakout above 20-day resistance
- Win Rate: 68% (34/50)
- R:R: 1.5:1
- Avg Trade: 4.2 hours
- Best For: Trending markets

**Setup 2: ETH Bullish Divergence**
- Pattern: RSI higher low on lower price low (bullish divergence)
- Win Rate: 62% (26/42)
- R:R: 1.25:1
- Avg Trade: 8.3 hours
- Best For: Oversold bounces, range-bound markets

**Setup 3: SOL Support Retest**
- Pattern: Retest of broken support (pullback buying)
- Win Rate: 65% (22/34)
- R:R: 1:1 (balanced risk-reward)
- Avg Trade: 2.1 hours
- Best For: Scalping, tight stops

### Use Case
Swing trader browses Setups Library. Sees "BTC Breakout Momentum" with 68% win rate. Studies the 34 real winning trades + 16 losses. Understands:
- Entry: Wait for break above resistance + volume spike
- Exit: Trail stop or take 1.5R profit
- Risk: 5% of account per trade
- Timeframe: Typically 4-8 hours

Trades this setup for 1 month: 15 trades, 10 wins, 5 losses. Actual 67% win rate matches historical (68%). Confidence grows; refines parameters for their market regime.

---

## Feature 5: Frontend Integration

### VIP Navigation (index.html)

Added to ANALYSE section:
```html
<button id="btn-brief-vip" class="tab-btn vip-exclusive">
  👑 VIP BRIEF
</button>
<button id="btn-setups" class="tab-btn vip-exclusive">
  👑 SETUPS
</button>
```

### VIP Brief Tab (tab-brief_vip)

Sections:
1. **Risk Score Gauge** — 1-10 with color gradient (red = risk-off, green = risk-on)
2. **VIP Insights** — 3 strategic bullet points
3. **Top Risks & Catalysts** — Cards showing downside/upside catalysts
4. **Economic Calendar** — Upcoming + recent economic releases
5. **Regulatory News** — Sentiment-colored news feed

### Setups Tab (tab-setups)

Sections:
1. **Statistics Cards** — Total setups, high-probability count, average win rate
2. **Filter Buttons** — Asset (BTC/ETH/SOL), Difficulty, Win Rate threshold
3. **Setups Grid** — Card layout showing name, asset, pattern, difficulty, win rate, R:R
4. **Setup Detail Modal** — Click card to see entry/exit rules, historical trades, equity curve

### Styling

New CSS class: `.vip-exclusive`
- Gold/amber accent color (differentiate from Free/Member)
- 👑 Badge indicates VIP-only content
- Hover effects match existing design

---

## Tier Access Control

### Verification Method

All VIP endpoints verify:
```python
@app.route('/api/morning-brief/vip')
def api_vip_brief():
    user = _role_guard("vip")  # Raises 403 if not VIP
    return jsonify(get_geopolitical_summary())
```

**Database Check:**
```sql
SELECT subscription_tier FROM users WHERE id = ? AND subscription_expires > NOW()
```

Expected values:
- `free` — No access to VIP features
- `member` — Access to Member features only
- `vip` — Access to all VIP features

### Response Codes

| Code | Scenario |
|------|----------|
| 200 | VIP user, data returned |
| 401 | Not logged in |
| 403 | Logged in but not VIP tier |
| 500 | Server error (API timeout, DB issue) |

---

## Performance Considerations

| Feature | Compute Time | Frequency | Cache |
|---------|--------------|-----------|-------|
| Liquidations Heatmap | 500ms | 5s | 5min browser |
| Funding Rates | 200ms | 30s | None (real-time) |
| Correlation Matrix | 2s (9x9) | 5min | 10min cache |
| Economic Calendar | 300ms | 30min | 1h cache (external) |
| Regulatory News | 400ms | 1h | 1h cache |
| Trading Setups | <50ms | On-demand | None (static) |

**Peak Usage:** All VIPs loading dashboard simultaneously
- Expected: <2s full page load
- Mitigation: Serve setups from cache, correlation matrix from 10min cache

---

## Monitoring & Alerts

### VIP Endpoint Health

```bash
# Monitor response times
curl -w "@curl-format.txt" \
  -H "Authorization: Bearer $TOKEN" \
  https://cryptoscanner.prod/api/morning-brief/vip
```

### Common Issues

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Blank risk score | news_macro.py API timeout | Increase timeout, retry |
| Empty setups list | DB not initialized | Run `init_setups_tables()` |
| Correlation matrix [NaN] | Binance API down | Fallback to cached values |
| 403 Forbidden on VIP endpoints | subscription_tier not set | Update user DB |

---

## Support & Training

### For VIP Users
1. **VIP Brief:** Check each morning for macro regime changes
2. **Correlations:** Use to spot diversification gaps, pair trading opportunities
3. **Liquidations:** Set alerts for key liquidation zones as support/resistance
4. **Setups Library:** Use as reference, don't trade blindly (market conditions vary)
5. **Funding Rates:** Monitor for leverage extremes (positive >0.1% = risky long bias)

### For Admins
- Monthly: Review trading setups performance, add new examples
- Weekly: Monitor VIP endpoint uptime, check for API errors
- Daily: Verify macro data freshness (not stale >2h)

---

**Last Updated:** 2026-05-05  
**Next Review:** 2026-06-05
