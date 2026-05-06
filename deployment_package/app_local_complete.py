"""
Heatmap OI+Volume — Local Complete Test Server
Lance: python3 app_local_complete.py
Puis visite: http://localhost:5000
"""
from flask import Flask, jsonify, render_template_string
from datetime import datetime
import sys
sys.path.insert(0, '.')

# Mock data pour tests locaux
MOCK_CRYPTOS = [
    {'symbol': 'BTC', 'intensity': 0.82, 'color': 'red', 'volume_24h': 28e9, 'oi_change_1h': 3.2},
    {'symbol': 'ETH', 'intensity': 0.65, 'color': 'orange', 'volume_24h': 15e9, 'oi_change_1h': 1.8},
    {'symbol': 'SOL', 'intensity': 0.35, 'color': 'blue', 'volume_24h': 2e9, 'oi_change_1h': -0.5},
    {'symbol': 'XRP', 'intensity': 0.48, 'color': 'orange', 'volume_24h': 1.2e9, 'oi_change_1h': 0.8},
    {'symbol': 'DOGE', 'intensity': 0.55, 'color': 'orange', 'volume_24h': 3e9, 'oi_change_1h': 2.1},
    {'symbol': 'ADA', 'intensity': 0.42, 'color': 'blue', 'volume_24h': 1.5e9, 'oi_change_1h': -0.2},
]

app = Flask(__name__)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/api/heatmap/all', methods=['GET'])
def get_heatmap_all():
    """Global heatmap — all cryptos"""
    return jsonify({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "cryptos": MOCK_CRYPTOS
    }), 200

@app.route('/api/heatmap/<symbol>', methods=['GET'])
def get_heatmap_detail(symbol):
    """Detail heatmap by price level"""
    price_map = {
        'BTC': 70000,
        'ETH': 3500,
        'SOL': 200,
        'XRP': 2.5,
        'DOGE': 0.45,
        'ADA': 1.2
    }
    current_price = price_map.get(symbol, 100)

    price_levels = []
    for i in range(-3, 4):
        level_price = current_price * (1 + i * 0.01)
        distance_pct = abs(i) / 3.0
        intensity = 1.0 - distance_pct

        # Color assignment
        if intensity < 0.4:
            color = "blue"
        elif intensity < 0.7:
            color = "orange"
        else:
            color = "red"

        price_levels.append({
            "price": round(level_price, 2),
            "intensity": round(intensity, 4),
            "color": color
        })

    return jsonify({
        "symbol": symbol,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "price_levels": price_levels
    }), 200

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FRONTEND
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.route('/')
def dashboard():
    """Complete heatmap dashboard"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CryptoScanner Pro — Heatmap OI+Volume</title>
        <script src="https://s3.tradingview.com/tv.js"></script>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e, #16213e);
                color: #e0e0f0;
                padding: 20px;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
            }

            header {
                text-align: center;
                margin-bottom: 30px;
                padding: 20px;
                background: rgba(255, 215, 0, 0.1);
                border-radius: 10px;
                border: 1px solid rgba(255, 215, 0, 0.3);
            }

            header h1 {
                color: #ffd700;
                font-size: 2em;
                margin-bottom: 5px;
            }

            header p {
                color: #aaa;
                font-size: 0.9em;
            }

            .layout {
                display: grid;
                grid-template-columns: 1fr 2fr;
                gap: 20px;
                margin-bottom: 30px;
            }

            .panel {
                background: rgba(22, 33, 62, 0.8);
                border: 1px solid rgba(255, 215, 0, 0.2);
                border-radius: 10px;
                padding: 20px;
                backdrop-filter: blur(10px);
            }

            .panel h2 {
                color: #ffd700;
                margin-bottom: 15px;
                font-size: 1.3em;
                border-bottom: 2px solid rgba(255, 215, 0, 0.3);
                padding-bottom: 10px;
            }

            .panel h3 {
                color: #ffd700;
                margin-top: 20px;
                margin-bottom: 10px;
                font-size: 1.1em;
            }

            .heatmap-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }

            .heatmap-table thead {
                background: rgba(15, 52, 96, 0.5);
                border-bottom: 2px solid rgba(255, 215, 0, 0.3);
            }

            .heatmap-table th,
            .heatmap-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid rgba(255, 215, 0, 0.1);
            }

            .heatmap-table th {
                color: #ffd700;
                font-weight: bold;
            }

            .heatmap-row {
                cursor: pointer;
                transition: background 0.2s ease;
            }

            .heatmap-row:hover {
                background: rgba(255, 215, 0, 0.1);
            }

            .heatmap-row.selected {
                background: rgba(255, 215, 0, 0.2);
                border-left: 3px solid #ffd700;
            }

            .intensity-bar {
                display: inline-block;
                height: 20px;
                border-radius: 3px;
                min-width: 80px;
                margin-right: 8px;
                font-size: 0.85em;
                color: white;
                font-weight: bold;
                text-align: center;
                line-height: 20px;
            }

            .intensity-blue { background: linear-gradient(90deg, #3498db, #2980b9); }
            .intensity-orange { background: linear-gradient(90deg, #e67e22, #d35400); }
            .intensity-red { background: linear-gradient(90deg, #e74c3c, #c0392b); }

            #chart-container {
                width: 100%;
                height: 400px;
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 20px;
            }

            .price-levels {
                display: flex;
                flex-direction: column;
                gap: 8px;
                max-height: 300px;
                overflow-y: auto;
            }

            .price-level {
                display: flex;
                align-items: center;
                padding: 10px;
                background: rgba(15, 52, 96, 0.3);
                border-radius: 5px;
                font-size: 0.9em;
            }

            .price-level-price {
                flex: 0 0 80px;
                font-weight: bold;
                color: #ffd700;
            }

            .price-level-bar {
                flex: 1;
                margin: 0 10px;
                height: 20px;
                border-radius: 3px;
            }

            .price-level-intensity {
                flex: 0 0 50px;
                text-align: right;
                color: #aaa;
            }

            .status {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 0.9em;
                font-weight: bold;
                margin: 10px 0;
            }

            .status.ok { background: #27ae60; color: white; }
            .status.error { background: #e74c3c; color: white; }

            .info-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
                margin-top: 15px;
            }

            .info-item {
                background: rgba(15, 52, 96, 0.3);
                padding: 10px;
                border-radius: 5px;
                border-left: 3px solid #ffd700;
            }

            .info-label {
                color: #aaa;
                font-size: 0.8em;
                text-transform: uppercase;
            }

            .info-value {
                color: #ffd700;
                font-weight: bold;
                font-size: 1.2em;
                margin-top: 5px;
            }

            .loading {
                text-align: center;
                color: #aaa;
                padding: 20px;
            }

            @media (max-width: 1024px) {
                .layout {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 768px) {
                header h1 { font-size: 1.5em; }
                .panel { padding: 15px; }
                .info-grid { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🔥 CryptoScanner Pro — Heatmap OI+Volume</h1>
                <p>Real-time Open Interest + Volume intensity heatmap for Binance Futures</p>
            </header>

            <div class="layout">
                <!-- LEFT: Global Heatmap -->
                <div class="panel">
                    <h2>📊 Global Heatmap</h2>
                    <p style="color: #aaa; font-size: 0.9em; margin-bottom: 10px;">
                        Click a crypto to see details & chart
                    </p>
                    <div id="heatmap-container" class="loading">Loading...</div>
                </div>

                <!-- RIGHT: Detail View -->
                <div class="panel">
                    <h2 id="detail-title">Select a Crypto</h2>

                    <div id="chart-container" style="display: none; height: 500px; margin-bottom: 20px; border-radius: 8px; overflow: hidden;"></div>

                    <div id="detail-content">
                        <div class="loading" style="padding: 40px; text-align: center;">
                            Click a crypto from the heatmap to view chart & price levels
                        </div>
                    </div>

                    <div id="info-panel" style="display: none;">
                        <h3>Price Levels (Heatmap Overlay)</h3>
                        <div class="price-levels" id="price-levels-container"></div>
                    </div>
                </div>
            </div>

            <!-- FOOTER -->
            <footer style="text-align: center; color: #666; font-size: 0.85em; padding-top: 20px; border-top: 1px solid rgba(255,215,0,0.1);">
                <p>✅ Local Test Server — All endpoints responding</p>
                <p style="color: #888; margin-top: 10px;">
                    API: /api/heatmap/all | /api/heatmap/&lt;symbol&gt;
                </p>
            </footer>
        </div>

        <script>
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // Global Heatmap Component
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            class GlobalHeatmap {
                constructor(containerId) {
                    this.container = document.getElementById(containerId);
                    this.data = [];
                    this.selectedSymbol = null;
                }

                async loadData() {
                    try {
                        const response = await fetch('/api/heatmap/all');
                        if (!response.ok) throw new Error(`HTTP ${response.status}`);
                        const result = await response.json();
                        this.data = result.cryptos;
                        this.render();
                    } catch (error) {
                        console.error('Failed to load heatmap:', error);
                        this.container.innerHTML = `<div class="status error">⚠️ Error: ${error.message}</div>`;
                    }
                }

                render() {
                    const html = `
                        <table class="heatmap-table">
                            <thead>
                                <tr>
                                    <th style="width: 60px;">Symbol</th>
                                    <th>Intensity</th>
                                    <th style="width: 80px;">Volume</th>
                                    <th style="width: 80px;">OI Δ 1h</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${this.data.map(c => `
                                    <tr class="heatmap-row" data-symbol="${c.symbol}" style="cursor: pointer;">
                                        <td style="font-weight: bold; color: #ffd700;">${c.symbol}</td>
                                        <td>
                                            <span class="intensity-bar intensity-${c.color}">
                                                ${c.intensity.toFixed(2)}
                                            </span>
                                        </td>
                                        <td>${c.volume_24h ? (c.volume_24h/1e9).toFixed(1)+'B' : '-'}</td>
                                        <td style="color: ${c.oi_change_1h > 0 ? '#27ae60' : '#e74c3c'};">
                                            ${c.oi_change_1h > 0 ? '📈 +' : '📉 '}${c.oi_change_1h.toFixed(1)}%
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                    this.container.innerHTML = html;
                    this.attachEventListeners();
                }

                attachEventListeners() {
                    document.querySelectorAll('.heatmap-row').forEach(row => {
                        row.addEventListener('click', () => {
                            document.querySelectorAll('.heatmap-row').forEach(r => r.classList.remove('selected'));
                            row.classList.add('selected');
                            const symbol = row.dataset.symbol;
                            this.selectCrypto(symbol);
                        });
                    });
                }

                selectCrypto(symbol) {
                    this.selectedSymbol = symbol;
                    window.dispatchEvent(new CustomEvent('cryptoSelected', { detail: { symbol } }));
                }
            }

            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // TradingView Chart + Price Level Indicators
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            class TradingViewChart {
                constructor(containerId) {
                    this.containerId = containerId;
                }

                initChart(symbol, priceData) {
                    try {
                        const container = document.getElementById(this.containerId);
                        if (!container) {
                            console.error('❌ Container not found');
                            return;
                        }

                        container.innerHTML = '';
                        container.style.display = 'block';
                        container.style.position = 'relative';

                        console.log(`🎯 Loading TradingView chart for ${symbol}USDT...`);

                        // Create TradingView Widget
                        new TradingView.widget({
                            "autosize": true,
                            "symbol": `BINANCE:${symbol}USDT`,
                            "interval": "60",
                            "timezone": "Etc/UTC",
                            "theme": "dark",
                            "style": "1",
                            "locale": "en",
                            "toolbar_bg": "#0f3460",
                            "enable_publishing": false,
                            "hide_side_toolbar": false,
                            "allow_symbol_change": false,
                            "container_id": this.containerId
                        });

                        // Add price level indicators below chart
                        if (priceData && priceData.price_levels) {
                            setTimeout(() => {
                                this.addPriceLevelIndicators(priceData.price_levels);
                            }, 500);
                        }

                        console.log(`✨ TradingView chart loaded for ${symbol}`);

                    } catch (error) {
                        console.error('❌ Chart error:', error);
                        const container = document.getElementById(this.containerId);
                        if (container) {
                            container.innerHTML = `<p style="color: #e74c3c; text-align: center; padding: 50px;">⚠️ Error: ${error.message}</p>`;
                        }
                    }
                }

                addPriceLevelIndicators(priceLevels) {
                    if (!priceLevels || priceLevels.length === 0) return;

                    try {
                        const colorMap = { 'blue': '#3498db', 'orange': '#e67e22', 'red': '#e74c3c' };
                        const container = document.getElementById(this.containerId);

                        // Create indicators panel below chart
                        const panel = document.createElement('div');
                        panel.style.position = 'absolute';
                        panel.style.bottom = '5px';
                        panel.style.left = '10px';
                        panel.style.zIndex = '100';
                        panel.style.display = 'flex';
                        panel.style.gap = '8px';
                        panel.style.flexWrap = 'wrap';

                        const maxLevels = Math.min(5, priceLevels.length);
                        const step = Math.floor(priceLevels.length / maxLevels) || 1;

                        for (let i = 0; i < priceLevels.length; i += step) {
                            if (i >= priceLevels.length) break;
                            const level = priceLevels[i];
                            const color = colorMap[level.color];

                            const badge = document.createElement('div');
                            badge.style.display = 'flex';
                            badge.style.alignItems = 'center';
                            badge.style.gap = '6px';
                            badge.style.padding = '6px 10px';
                            badge.style.backgroundColor = `${color}20`;
                            badge.style.border = `2px dashed ${color}`;
                            badge.style.borderRadius = '4px';
                            badge.style.fontSize = '11px';
                            badge.style.fontWeight = 'bold';
                            badge.style.color = color;

                            const dot = document.createElement('div');
                            dot.style.width = '8px';
                            dot.style.height = '8px';
                            dot.style.backgroundColor = color;
                            dot.style.borderRadius = '50%';

                            const price = document.createElement('span');
                            price.textContent = `$${level.price.toFixed(level.price < 10 ? 2 : 0)}`;

                            badge.appendChild(dot);
                            badge.appendChild(price);
                            panel.appendChild(badge);
                        }

                        container.appendChild(panel);
                        console.log(`✅ Added ${maxLevels} price level indicators`);

                    } catch (error) {
                        console.error('❌ Indicator error:', error);
                    }
                }

                destroy() {
                    const container = document.getElementById(this.containerId);
                    if (container) {
                        container.innerHTML = '';
                        container.style.display = 'none';
                    }
                }
            }

            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // Detail Heatmap Component
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            class DetailHeatmap {
                constructor() {
                    this.selectedSymbol = null;
                    this.tvChart = new TradingViewChart('chart-container');
                    this.priceData = null;
                }

                async loadData(symbol) {
                    try {
                        console.log(`📍 Loading heatmap for ${symbol}...`);

                        // Load price levels
                        const response = await fetch(`/api/heatmap/${symbol}`);
                        if (!response.ok) throw new Error(`HTTP ${response.status}`);
                        this.priceData = await response.json();

                        // Init TradingView chart
                        this.tvChart.initChart(symbol, this.priceData);

                        // Update title
                        this.render(symbol);
                    } catch (error) {
                        console.error('❌ Failed to load detail:', error);
                    }
                }

                render(symbol) {
                    const title = `📈 ${symbol} — 1H Real-time Chart`;
                    document.getElementById('detail-title').innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span>${title}</span>
                            <span style="font-size: 0.8em; color: #ffd700; background: rgba(255,215,0,0.2); padding: 5px 10px; border-radius: 3px;">
                                TradingView • 1H • Price Levels
                            </span>
                        </div>
                    `;

                    // Hide content - show only chart
                    document.getElementById('detail-content').style.display = 'none';
                    document.getElementById('info-panel').style.display = 'none';
                }
            }

            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            // Initialize
            // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            window.globalHeatmap = new GlobalHeatmap('heatmap-container');
            window.detailHeatmap = new DetailHeatmap();

            window.globalHeatmap.loadData();

            window.addEventListener('cryptoSelected', (event) => {
                window.detailHeatmap.loadData(event.detail.symbol);
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔥 HEATMAP OI+VOLUME — COMPLETE LOCAL TEST SERVER")
    print("="*70)
    print("\n📍 http://localhost:5000")
    print("📊 Complete dashboard with global + detail heatmap")
    print("🖱️  Click a crypto in the left table to see price levels")
    print("\n✅ API Endpoints:")
    print("   • GET /api/heatmap/all")
    print("   • GET /api/heatmap/<symbol>")
    print("\nAppuyez sur CTRL+C pour arrêter\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
