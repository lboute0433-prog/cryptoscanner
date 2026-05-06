# Morning Brief Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the `/brief` page HTML in `morning_brief.py` with professional styling (gradient, interactive tables, hierarchy, spacing) following Approche C spec.

**Architecture:** Modify `build_brief_html()` function to generate new HTML with inline CSS. Keep data binding (Jinja2 `{{ }}`) intact. CSS all inline for Telegram compatibility. Tables with ranking medals, progress bars, hover effects, and sentiment-colored borders.

**Tech Stack:** Python, Jinja2 templating, inline CSS, HTML tables, JavaScript onclick handlers for expand/collapse.

---

## File Structure

### Files to Modify
- **`morning_brief.py`** (lines 420-639)
  - Function: `build_brief_html(analysis, market_data, token)`
  - Replace entire HTML generation with new design
  - Keep all data binding intact (`analysis.get()`, `market_data.get()`, etc.)
  - Keep helper functions (`clr()`, `pct()`, `fmtVol()`) unchanged

### No New Files
- All CSS is inline within the HTML `<style>` tag
- No external stylesheets needed

---

## Task Breakdown

### Task 1: Create CSS Variables & Global Styles

**Files:**
- Modify: `morning_brief.py:420-500` (new `<style>` section)

- [ ] **Step 1: Open morning_brief.py and locate the `build_brief_html()` function**

Find line 420 where the function starts returning the HTML template.

- [ ] **Step 2: Replace the opening `<style>` section with the new color palette**

```python
# Inside the f-string, after <style>, add:
"""
:root {
  --bg-gradient: linear-gradient(135deg, #0f1428 0%, #1e1a4a 100%);
  --accent-gold: #ffd700;
  --sentiment-green: #4caf50;
  --sentiment-red: #f44336;
  --text-primary: #e0e0f0;
  --text-secondary: #ccc;
  --text-muted: #aaa;
  --text-subtle: #666;
  --card-bg: rgba(37,37,64,0.8);
  --row-alt-1: rgba(255,255,255,0.02);
  --row-alt-2: rgba(0,0,0,0.2);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Segoe UI', Arial, sans-serif;
  background: var(--bg-gradient);
  color: var(--text-primary);
  min-height: 100vh;
}
"""
```

- [ ] **Step 3: Add header and body layout styles**

```css
.hdr {
  background: linear-gradient(135deg, #1a1a2e, #16213e);
  padding: 20px 24px;
  border-bottom: 2px solid var(--accent-gold);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.wrap {
  max-width: 900px;
  margin: 20px auto;
  padding: 0 16px 60px;
}

.score-card {
  background: rgba(30,30,48,0.6);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 14px;
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
  border-left: 4px solid var(--accent-gold);
}

.score-card > div:first-child {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.score-value {
  font-size: 72px;
  font-weight: 700;
  line-height: 1;
}

.score-max {
  color: var(--text-subtle);
  font-size: 12px;
}

.score-signal {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 6px;
}

.score-bar {
  background: #333;
  border-radius: 6px;
  height: 10px;
  overflow: hidden;
  margin-bottom: 8px;
  width: 100%;
}

.score-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #f44336, #ffd700, #4caf50);
}
```

- [ ] **Step 4: Add section styles (sec, sec-head, sec-body)**

```css
.sec {
  background: #1e1e30;
  border-radius: 10px;
  margin-bottom: 8px;
  overflow: hidden;
}

.sec-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 13px 18px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: background 0.15s;
  background: rgba(0,0,0,0.3);
  border-bottom: 2px solid var(--accent-gold);
}

.sec-head:hover {
  background: rgba(37,37,64,0.5);
}

.sec-body {
  display: none;
  padding: 16px 18px;
}

.sec.open .sec-body {
  display: block;
}

.sec-head span:last-child {
  transition: transform 0.2s;
}

.sec.open .sec-head span:last-child {
  transform: scaleY(-1);
}
```

- [ ] **Step 5: Commit**

```bash
git add morning_brief.py
git commit -m "style: add CSS palette and global layout styles"
```

---

### Task 2: Style Score Card & Cards (BTC/ETH, F&G)

**Files:**
- Modify: `morning_brief.py:500-600` (CSS section continued)

- [ ] **Step 1: Add card styles for BTC/ETH section**

```css
.cards {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.card {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 16px;
  flex: 1;
  min-width: 200px;
  border-left: 4px solid var(--accent-gold);
  transition: all 0.2s ease;
}

.card:hover {
  background: rgba(37,37,64,1);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}

.card-sym {
  font-size: 16px;
  font-weight: 700;
  color: var(--accent-gold);
}

.card-price {
  font-size: 22px;
  font-weight: 700;
  margin: 4px 0;
  color: var(--text-primary);
}

.card-change {
  font-weight: 700;
  font-size: 16px;
}

.card-change-7d {
  color: var(--text-muted);
  font-size: 11px;
}

.card-note {
  color: #aaa;
  font-size: 13px;
  line-height: 1.6;
  margin-top: 10px;
}
```

- [ ] **Step 2: Add Fear & Greed grid styles**

```css
.grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin: 10px 0;
}

.fg-cell {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 14px;
  text-align: center;
}

.fg-label {
  color: var(--text-subtle);
  font-size: 10px;
  margin-bottom: 4px;
}

.fg-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--accent-gold);
}

.fg-class {
  color: var(--text-muted);
  font-size: 11px;
}
```

- [ ] **Step 3: Add row/column utility styles**

```css
.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  border-bottom: 1px solid #1a1a28;
  font-size: 13px;
}

.row:last-child {
  border-bottom: none;
}

.row-label {
  color: var(--text-muted);
}

.row-value {
  font-weight: 700;
}

.note {
  color: #ccc;
  font-size: 13px;
  line-height: 1.6;
  margin-top: 10px;
}
```

- [ ] **Step 4: Commit**

```bash
git add morning_brief.py
git commit -m "style: add card and grid layout styles"
```

---

### Task 3: Style Tables (Approche C - Interactive Tables)

**Files:**
- Modify: `morning_brief.py:600-680` (CSS section continued)

- [ ] **Step 1: Add base table styles**

```css
table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  margin-top: 8px;
  background: linear-gradient(135deg, #0a0e27 0%, #1a1a3a 100%);
  border-radius: 6px;
  overflow: hidden;
}

thead {
  background: linear-gradient(90deg, rgba(0,0,0,0.4) 0%, rgba(255,215,0,0.1) 100%);
  border-bottom: 2px solid var(--accent-gold);
  border-top: 1px solid rgba(255,215,0,0.2);
}

th {
  padding: 14px 16px;
  text-align: left;
  color: var(--text-subtle);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

th:first-child {
  color: var(--accent-gold);
  font-weight: 700;
}

th[style*="text-align: right"],
th[style*="text-align: center"] {
  text-align: right;
}

th {
  cursor: pointer;
}

th:hover {
  color: var(--accent-gold);
}
```

- [ ] **Step 2: Add tbody and row styles**

```css
tbody tr {
  transition: all 0.25s ease;
  border-left: 4px solid transparent;
}

tbody tr:nth-child(odd) {
  background: var(--row-alt-1);
}

tbody tr:nth-child(even) {
  background: var(--row-alt-2);
}

tbody tr:hover {
  background: rgba(76,175,80,0.15);
}

tbody tr.negative:hover {
  background: rgba(244,67,54,0.15);
}

tbody tr.positive {
  border-left-color: var(--sentiment-green);
}

tbody tr.negative {
  border-left-color: var(--sentiment-red);
}

td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

td:last-child {
  border-bottom: none;
}
```

- [ ] **Step 3: Add ranking and progress bar styles**

```css
.rank-medal {
  font-size: 12px;
  font-weight: 700;
  text-align: center;
  width: 30px;
}

.sym {
  color: var(--accent-gold);
  font-weight: 700;
  font-size: 15px;
}

.name {
  color: var(--text-secondary);
  font-size: 13px;
}

.performance-bar {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.bar-fill {
  width: 50px;
  height: 5px;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--sentiment-green) 0%, var(--sentiment-green) 82%, rgba(76,175,80,0.3) 82%);
}

.bar-fill.negative {
  background: linear-gradient(90deg, var(--sentiment-red) 0%, var(--sentiment-red) 24%, rgba(244,67,54,0.3) 24%);
}

.perc-text {
  font-weight: 700;
  font-size: 13px;
  min-width: 50px;
}

.perc-text.positive {
  color: var(--sentiment-green);
}

.perc-text.negative {
  color: var(--sentiment-red);
}

.price {
  color: var(--text-muted);
  font-size: 13px;
  text-align: right;
}
```

- [ ] **Step 4: Commit**

```bash
git add morning_brief.py
git commit -m "style: add interactive table styles with ranking, bars, and sentiment colors"
```

---

### Task 4: Style Winners/Losers & Lists

**Files:**
- Modify: `morning_brief.py:680-730` (CSS section continued)

- [ ] **Step 1: Add winners/losers grid styles**

```css
.winners-losers {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.winners {
  background: rgba(76,175,80,0.08);
  border-radius: 6px;
  padding: 10px;
  border-left: 3px solid var(--sentiment-green);
}

.losers {
  background: rgba(244,67,54,0.08);
  border-radius: 6px;
  padding: 10px;
  border-left: 3px solid var(--sentiment-red);
}

.winners-title {
  color: var(--sentiment-green);
  font-weight: 700;
  font-size: 12px;
  margin-bottom: 6px;
}

.losers-title {
  color: var(--sentiment-red);
  font-weight: 700;
  font-size: 12px;
  margin-bottom: 6px;
}

.winners-item,
.losers-item {
  color: var(--text-secondary);
  padding: 2px 0;
  font-size: 12px;
}

.winners-item:before {
  content: "▸ ";
  color: var(--sentiment-green);
  font-weight: 700;
  margin-right: 4px;
}

.losers-item:before {
  content: "▸ ";
  color: var(--sentiment-red);
  font-weight: 700;
  margin-right: 4px;
}
```

- [ ] **Step 2: Add news/macro list styles**

```css
ul {
  list-style: none;
  margin-top: 8px;
}

li {
  padding: 6px 0;
  border-bottom: 1px solid #1a1a28;
  color: var(--text-secondary);
  font-size: 13px;
  display: flex;
  gap: 8px;
}

li:last-child {
  border-bottom: none;
}

li:before {
  content: "▸ ";
  color: var(--accent-gold);
  font-weight: 700;
  flex-shrink: 0;
}

li.macro:before {
  color: var(--sentiment-green);
}
```

- [ ] **Step 3: Add COT alignment box styles**

```css
.cot-alignment {
  background: rgba(76,175,80,0.1);
  border-radius: 6px;
  border-left: 3px solid var(--sentiment-green);
  padding: 10px 12px;
  margin-top: 10px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.cot-alignment.bearish {
  background: rgba(244,67,54,0.1);
  border-left-color: var(--sentiment-red);
}

.cot-alignment strong {
  color: var(--accent-gold);
}
```

- [ ] **Step 4: Commit**

```bash
git add morning_brief.py
git commit -m "style: add winners/losers, lists, and COT alignment box styles"
```

---

### Task 5: Style Footer & Responsive

**Files:**
- Modify: `morning_brief.py:730-760` (CSS section continued)

- [ ] **Step 1: Add footer and media query styles**

```css
.footer {
  text-align: center;
  padding: 30px 20px;
  color: #444;
  font-size: 12px;
  border-top: 1px solid #1a1a28;
  margin-top: 40px;
}

@media (max-width: 600px) {
  .hdr {
    flex-direction: column;
  }

  .cards {
    flex-direction: column;
  }

  .card {
    min-width: 100%;
  }

  .grid-2,
  .winners-losers {
    grid-template-columns: 1fr;
  }

  table {
    font-size: 12px;
  }

  th, td {
    padding: 10px 8px;
  }

  .wrap {
    padding: 0 12px 40px;
  }
}
```

- [ ] **Step 2: Close the `<style>` tag**

Make sure to close with `</style>` before the opening `<body>`.

- [ ] **Step 3: Commit**

```bash
git add morning_brief.py
git commit -m "style: add footer and responsive design styles"
```

---

### Task 6: Refactor HTML Header Section

**Files:**
- Modify: `morning_brief.py:760-810` (HTML body)

- [ ] **Step 1: Update the header block**

Replace the current header with:

```html
<div class="hdr">
  <div>
    <div style="font-size: 20px; font-weight: 700; color: var(--accent-gold);">📊 CryptoScanner Pro</div>
    <div style="color: var(--text-muted); font-size: 11px;">Morning Brief · Membres</div>
  </div>
  <div style="text-align: right;">
    <div style="color: var(--accent-gold); font-weight: 700;">{date_str}</div>
    <div style="color: var(--text-muted); font-size: 12px;">Généré à {time_str}</div>
    <div style="background: #ff4444; color: #fff; font-size: 10px; padding: 2px 8px; border-radius: 10px; margin-top: 4px; display: inline-block;">⏰ Expire à minuit</div>
  </div>
</div>
```

- [ ] **Step 2: Update the score card section**

```html
<div class="score-card">
  <div>
    <div class="score-value" style="color: {sc};">{sv}</div>
    <div class="score-max">/100</div>
  </div>
  <div style="flex: 1;">
    <div class="score-signal" style="color: {sc};">{ss.upper()}</div>
    <div class="score-bar">
      <div class="score-bar-fill" style="width: {sv}%;"></div>
    </div>
    <div style="color: #aaa; font-size: 12px;">{score.get('justification','')}</div>
  </div>
</div>
```

- [ ] **Step 3: Commit**

```bash
git add morning_brief.py
git commit -m "refactor: redesign header and score card HTML"
```

---

### Task 7: Refactor HTML Sections (Aperçu, BTC/ETH, Altcoins)

**Files:**
- Modify: `morning_brief.py:810-900` (HTML body continued)

- [ ] **Step 1: Update Aperçu global section**

```html
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>🌍 Aperçu global</span><span>▲</span></div>
  <div class="sec-body">
    <div class="row"><span class="row-label">Sentiment</span><span class="row-value" style="color: var(--accent-gold);">{analysis.get('apercu',{}).get('sentiment','—')}</span></div>
    <div class="row"><span class="row-label">Market Cap Total</span><span class="row-value">${mcap_t/1e12:.2f}T</span></div>
    <div class="row"><span class="row-label">BTC Dominance</span><span class="row-value" style="color: #f7931a;">{btc_dom:.1f}%</span></div>
    <p class="note">{analysis.get('apercu',{}).get('commentaire','')}</p>
  </div>
</div>
```

- [ ] **Step 2: Update BTC/ETH section**

```html
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>₿ Bitcoin & Ethereum</span><span>▲</span></div>
  <div class="sec-body">
    <div class="cards">
      <div class="card">
        <div class="card-sym">BTC</div>
        <div class="card-price">${btc_d.get('prix',0):,.0f}</div>
        <div class="card-change" style="color: {clr(btc_d.get('variation_24h',0))};">{pct(btc_d.get('variation_24h',0))}</div>
        <div class="card-change-7d">7j: {pct(btc_d.get('variation_7j',0))}</div>
        <p class="card-note">{btc_d.get('analyse','')}</p>
      </div>
      <div class="card">
        <div class="card-sym">ETH</div>
        <div class="card-price">${eth_d.get('prix',0):,.0f}</div>
        <div class="card-change" style="color: {clr(eth_d.get('variation_24h',0))};">{pct(eth_d.get('variation_24h',0))}</div>
        <div class="card-change-7d">7j: {pct(eth_d.get('variation_7j',0))}</div>
        <p class="card-note">{eth_d.get('analyse','')}</p>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Update Altcoins section with new table design**

```html
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>🪙 Altcoins</span><span>▼</span></div>
  <div class="sec-body">
    <table>
      <thead>
        <tr>
          <th style="width: 30px; text-align: center;">№</th>
          <th onclick="alert('Sort by Symbol')">▲ Symbole</th>
          <th>Nom</th>
          <th style="text-align: center;" onclick="alert('Sort by Performance')">Performance ▼</th>
          <th style="text-align: right;">Prix</th>
        </tr>
      </thead>
      <tbody>
        {alt_rows}
      </tbody>
    </table>
    <div class="winners-losers">
      <div class="winners">
        <div class="winners-title">🟢 Gagnants</div>
        {winners}
      </div>
      <div class="losers">
        <div class="losers-title">🔴 Perdants</div>
        {losers}
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 4: Commit**

```bash
git add morning_brief.py
git commit -m "refactor: redesign apercu, BTC/ETH, and altcoins sections"
```

---

### Task 8: Update Altcoins Row Generation (Python Helper)

**Files:**
- Modify: `morning_brief.py:449-453` (Python helper to generate alt_rows)

- [ ] **Step 1: Replace alt_rows generation with new format**

Current code (around line 449):
```python
alt_rows = "".join([
    f'<tr><td style="color:#ffd700;font-weight:700">{a.get("symbole","")}</td>'
    f'<td style="color:#888">{a.get("nom","")}</td>'
    f'<td style="color:{clr(a.get("variation_24h",0))};font-weight:700">{pct(a.get("variation_24h",0))}</td></tr>'
    for a in alts])
```

Replace with:
```python
def get_rank_medal(idx):
    medals = ["🥇", "🥈", "🥉"]
    return medals[idx] if idx < 3 else "•"

alt_rows = "".join([
    f'<tr class="{"positive" if float(a.get("variation_24h",0) or 0) >= 0 else "negative"}">'
    f'<td class="rank-medal">{get_rank_medal(i)} {i+1}</td>'
    f'<td class="sym">{a.get("symbole","")}</td>'
    f'<td class="name">{a.get("nom","")}</td>'
    f'<td style="text-align: center;"><div class="performance-bar">'
    f'<div class="bar-fill {"" if float(a.get("variation_24h",0) or 0) >= 0 else "negative"}" style="width: {50 * min(100, abs(float(a.get("variation_24h",0) or 0))) / 100}px;"></div>'
    f'<span class="perc-text {"positive" if float(a.get("variation_24h",0) or 0) >= 0 else "negative"}">{pct(a.get("variation_24h",0))}</span>'
    f'</div></td>'
    f'<td class="price">${"100.00" if not a.get("prix") else f"{float(a.get("prix",0)):,.2f}"}</td>'
    f'</tr>'
    for i, a in enumerate(alts)])
```

**Note:** You'll need to add price data to each altcoin dict in `_fallback_analysis()` and `generate_analysis()` if not already present.

- [ ] **Step 2: Commit**

```bash
git add morning_brief.py
git commit -m "feat: generate interactive altcoins table rows with ranking, bars, and sentiment"
```

---

### Task 9: Refactor HTML Remaining Sections (Dérivés, ETF, COT, etc.)

**Files:**
- Modify: `morning_brief.py:900-1050` (HTML body continued)

- [ ] **Step 1: Update Dérivés section**

```html
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>⚡ Dérivés</span><span>▼</span></div>
  <div class="sec-body">
    <div class="row"><span class="row-label">Funding Rate BTC</span><span class="row-value">{derives.get('funding','—')}</span></div>
    <div class="row"><span class="row-label">Open Interest BTC</span><span class="row-value">{derives.get('open_interest','—')}</span></div>
    <p class="note">{derives.get('analyse','')}</p>
  </div>
</div>
```

- [ ] **Step 2: Update ETF section**

```html
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>🏦 ETF BTC / ETH</span><span>▼</span></div>
  <div class="sec-body">
    <div class="row"><span class="row-label">Flux ETF BTC</span><span class="row-value">{etf_d.get('btc','—')}</span></div>
    <div class="row"><span class="row-label">Flux ETF ETH</span><span class="row-value">{etf_d.get('eth','—')}</span></div>
    <p class="note">{etf_d.get('analyse','')}</p>
  </div>
</div>
```

- [ ] **Step 3: Update COT section with alignment box**

```html
<div class="sec">
  <div class="sec-head" onclick="tog(this)">
    <span>📊 COT — Positionnement Institutionnel</span>
    <span style="color: {'var(--sentiment-green)' if 'HAUSSIER' in str(cot_d.get('signal_btc','')) else 'var(--sentiment-red)' if 'BAISSIER' in str(cot_d.get('signal_btc','')) else 'var(--accent-gold)'};"> {'🟢' if 'HAUSSIER' in str(cot_d.get('signal_btc','')) else '🔴' if 'BAISSIER' in str(cot_d.get('signal_btc','')) else '⚪'} {cot_d.get('signal_btc','N/D')}</span>
  </div>
  <div class="sec-body">
    {'<div style="background: #2a1a1a; border: 1px solid var(--sentiment-red); border-radius: 6px; padding: 8px 12px; margin-bottom: 10px; font-size: 11px; color: var(--sentiment-red);">⚠️ Données COT de démonstration — rapport CFTC non disponible</div>' if cot_d.get('is_demo') else ''}
    <div class="row">
      <span class="row-label">👔 Leveraged Funds (BTC net)</span>
      <span class="row-value" style="color: {'var(--sentiment-green)' if (cot_d.get('lf_net_btc') or 0) < 0 else 'var(--sentiment-red)'}">{(cot_d.get('lf_net_btc') or 0):+,}</span>
    </div>
    <div class="row">
      <span class="row-label">🏦 Asset Managers (BTC net)</span>
      <span class="row-value" style="color: {'var(--sentiment-green)' if (cot_d.get('am_net_btc') or 0) > 0 else 'var(--sentiment-red)'}">{(cot_d.get('am_net_btc') or 0):+,}</span>
    </div>
    <div class="row">
      <span class="row-label">📈 Open Interest BTC</span>
      <span class="row-value">{(cot_d.get('oi_btc') or 0):,} contrats</span>
    </div>
    <div class="row">
      <span class="row-label">Ξ Signal ETH</span>
      <span class="row-value" style="color: {'var(--sentiment-green)' if 'HAUSSIER' in str(cot_d.get('signal_eth','')) else 'var(--sentiment-red)' if 'BAISSIER' in str(cot_d.get('signal_eth','')) else 'var(--text-muted)'}">{cot_d.get('signal_eth','N/D')}</span>
    </div>
    <div class="cot-alignment {'bearish' if 'BAISSIER' in str(cot_d.get('signal_btc','')) else ''}">
      <strong>Alignement :</strong> {cot_d.get('alignement','—')}
    </div>
    <p class="note">{cot_d.get('verdict','—')}</p>
  </div>
</div>
```

- [ ] **Step 4: Commit**

```bash
git add morning_brief.py
git commit -m "refactor: redesign derives, ETF, and COT sections"
```

---

### Task 10: Refactor HTML Final Sections (Fear&Greed, Macro, News, Résumé, Footer)

**Files:**
- Modify: `morning_brief.py:1050-1200` (HTML body end)

- [ ] **Step 1: Update Fear & Greed section**

```html
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>😱 Fear & Greed</span><span>▲</span></div>
  <div class="sec-body">
    <div class="grid-2">
      <div class="fg-cell">
        <div class="fg-label">AUJOURD'HUI</div>
        <div class="fg-value" style="color: {'var(--sentiment-green)' if (fg[0].get('value',50) if fg else fg_d.get('valeur',50)) >= 60 else 'var(--sentiment-red)' if (fg[0].get('value',50) if fg else fg_d.get('valeur',50)) <= 40 else 'var(--accent-gold)'}">{fg[0].get('value','?') if fg else fg_d.get('valeur','?')}</div>
        <div class="fg-class">{fg[0].get('value_classification','') if fg else fg_d.get('label','')}</div>
      </div>
      <div class="fg-cell">
        <div class="fg-label">HIER</div>
        <div class="fg-value" style="color: var(--text-subtle);">{fg[1].get('value','—') if len(fg)>1 else '—'}</div>
        <div class="fg-class">{fg[1].get('value_classification','') if len(fg)>1 else ''}</div>
      </div>
    </div>
    <p class="note">{fg_d.get('interpretation','')}</p>
  </div>
</div>
```

- [ ] **Step 2: Update Macro du jour section**

```html
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>📅 Macro du jour</span><span>▲</span></div>
  <div class="sec-body">
    <ul>
      {macro_li or '<li style="color: var(--text-muted); font-size: 13px;">Aucun point macro saillant.</li>'}
    </ul>
  </div>
</div>
```

- [ ] **Step 3: Update Actualités section**

```html
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>📰 Actualités</span><span>▲</span></div>
  <div class="sec-body">
    <ul>
      {news_li}
    </ul>
  </div>
</div>
```

- [ ] **Step 4: Update Résumé stratégique section**

```html
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>🎯 Résumé stratégique</span><span>▲</span></div>
  <div class="sec-body">
    <div class="row">
      <span class="row-label">Biais</span>
      <span class="row-value" style="color: {sigc(resume.get('biais','Neutral'))};"> {'🟢' if resume.get('biais')=='Bullish' else '🔴' if resume.get('biais')=='Bearish' else '🟡'} {resume.get('biais','—')}</span>
    </div>
    <p class="note"><strong style="color: var(--accent-gold);">Moteurs :</strong> {resume.get('drivers','—')}</p>
    <p class="note"><strong style="color: var(--sentiment-red);">Risques :</strong> {resume.get('risques','—')}</p>
    <p class="note"><strong style="color: var(--sentiment-green);">Catalyseurs :</strong> {resume.get('catalyseurs','—')}</p>
  </div>
</div>
```

- [ ] **Step 5: Update footer**

```html
<div class="footer">
  <div>📊 CryptoScanner Pro · Membres</div>
  <div style="margin-top: 4px;">Brief expire à minuit · Usage personnel</div>
  <div style="margin-top: 4px;">© {datetime.now().year} CryptoScanner · Données techniques à titre informatif — ne constitue pas un conseil d'achat ou de vente</div>
</div>
```

- [ ] **Step 6: Add JavaScript toggle function at end of HTML**

```html
<script>
function tog(h) {
  const s = h.closest('.sec');
  s.classList.toggle('open');
  const c = h.querySelector('span:last-child');
  if (c) c.textContent = s.classList.contains('open') ? '▲' : '▼';
}
</script>
```

- [ ] **Step 7: Commit**

```bash
git add morning_brief.py
git commit -m "refactor: redesign Fear&Greed, Macro, News, Résumé, and footer sections"
```

---

### Task 11: Test Locally & Fix Data Issues

**Files:**
- Test: Generate local brief via `/api/brief/trigger`

- [ ] **Step 1: Start the app locally**

```bash
cd /path/to/cryptoscanner
python app.py
```

- [ ] **Step 2: Open browser and trigger brief generation**

Navigate to: `http://localhost:5000/api/brief/trigger`

Expected: JSON response with `{"ok":true,"message":"Brief en cours...","url":"..."}`

- [ ] **Step 3: Open the brief link in the response**

Check: Does the page load? Are all styles visible (colors, spacing, tables)?

- [ ] **Step 4: Verify key elements render**

- [ ] Score card displays with gradient background
- [ ] BTC/ETH cards side-by-side with gold border
- [ ] Altcoins table shows ranking medals (🥇🥈🥉)
- [ ] Barres de progression visible
- [ ] Sections expand/collapse on click
- [ ] Fear & Greed shows 2-column grid
- [ ] COT alignment box visible with colored border
- [ ] Footer at bottom

- [ ] **Step 5: Check mobile responsiveness**

Resize browser to 600px width. Verify:
- Cards stack vertically
- Grid becomes single column
- Table is readable

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "test: verify morning brief redesign renders correctly"
```

---

### Task 12: Deploy & Final Verification

**Files:**
- Deploy: `morning_brief.py` to production server

- [ ] **Step 1: Upload file to server via SCP**

```bash
scp morning_brief.py user@server:/path/to/cryptoscanner/
```

- [ ] **Step 2: SSH into server and restart app**

```bash
ssh user@server
cd /path/to/cryptoscanner
pm2 restart cryptoscanner
pm2 logs cryptoscanner
```

Expected: No errors, brief regenerates successfully

- [ ] **Step 3: Test brief generation at next scheduled time (8 AM) or trigger manually**

Navigate to: `https://46.225.234.71/brief?token=<today_token>`

- [ ] **Step 4: Verify styling in production**

Check all visual elements match spec (colors, spacing, tables, hover effects)

- [ ] **Step 5: Test Telegram delivery**

Verify brief message arrives in Telegram with correct formatting

- [ ] **Step 6: Commit**

```bash
git add morning_brief.py
git commit -m "deploy: production morning brief redesign live"
```

---

## Validation Checklist

- [ ] CSS palette (gradient, colors) matches spec
- [ ] Typography hierarchy consistent (h2, h3, body sizes)
- [ ] Tableaux have ranking medals 🥇🥈🥉
- [ ] Progress bars visible and colored by sentiment
- [ ] Hover effects work (rows change background)
- [ ] Sections expand/collapse with chevrons
- [ ] Fear & Greed 2-column grid
- [ ] COT alignment box styled correctly
- [ ] Winners/Losers sections with colored borders
- [ ] Responsive design works at <600px
- [ ] All data binds correctly (no empty fields)
- [ ] Footer displays copyright
- [ ] No HTML/CSS syntax errors
- [ ] Tested locally
- [ ] Deployed to production
- [ ] Live in Telegram

---

**Status:** Ready for implementation  
**Next Step:** Use superpowers:subagent-driven-development to execute tasks sequentially with reviews between steps.

