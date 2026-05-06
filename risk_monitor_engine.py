#!/usr/bin/env python3
"""
Risk Monitor Engine — Heatmap corrélations dynamiques + Score de risque par asset
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Combine : corrélations + volatilité + liquidités + concentration whale
Génère un score de risque 1-10 pour chaque crypto.
"""

import requests
import time
from datetime import datetime, timedelta
from correlations_engine import calculate_correlation_matrix, get_price_history
from scanner_engine import ScannerEngine

SYMBOLS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "MATIC"]
BINANCE_BASE = "https://api.binance.com/api/v3"

engine = None

def init_risk_monitor():
    global engine
    try:
        engine = ScannerEngine()
    except:
        pass

def calc_volatility_24h(symbol: str) -> float:
    """Calcule la volatilité sur 24h (écart-type %)."""
    try:
        prices = get_price_history(symbol, interval='1h', limit=24)
        if len(prices) < 2:
            return 5.0

        price_values = [p for p in prices if p > 0]
        if not price_values:
            return 5.0

        returns = []
        for i in range(1, len(price_values)):
            ret = ((price_values[i] - price_values[i-1]) / price_values[i-1]) * 100
            returns.append(ret)

        if not returns:
            return 5.0

        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = variance ** 0.5

        return min(10.0, max(0.5, std_dev / 2))
    except:
        return 5.0

def calc_liquidity_score(symbol: str) -> float:
    """Score liquidités basé sur orderbook depth."""
    try:
        r = requests.get(f"{BINANCE_BASE}/depth", params={"symbol": f"{symbol}USDT", "limit": 20}, timeout=5)
        if r.status_code != 200:
            return 5.0

        data = r.json()
        bids = sum(float(b[1]) for b in data.get("bids", []))
        asks = sum(float(a[1]) for a in data.get("asks", []))
        total_depth = bids + asks

        if total_depth < 100000:
            return 2.0
        elif total_depth < 1000000:
            return 4.0
        elif total_depth < 5000000:
            return 7.0
        else:
            return 9.0
    except:
        return 5.0

def calc_concentration_risk(symbol: str) -> float:
    """Score concentration whales (0-10, élevé = risqué)."""
    try:
        market = engine.get_last() if engine else None
        if not market:
            return 5.0

        for coin in market.get("coins", []):
            if coin.get("symbol") == symbol:
                volume = float(coin.get("volume_24h", 0) or 0)
                if volume < 100000000:
                    return 8.0
                elif volume < 500000000:
                    return 6.0
                else:
                    return 3.0
        return 5.0
    except:
        return 5.0

def calc_systemic_correlation(symbol: str, corr_matrix: dict) -> float:
    """Score corrélation système (moyenne des corrélations avec autres)."""
    try:
        correlations = corr_matrix.get("correlations", {})
        symbol_corrs = correlations.get(symbol, {})

        if not symbol_corrs:
            return 5.0

        values = [abs(float(v)) for v in symbol_corrs.values() if v is not None]
        if not values:
            return 5.0

        avg_corr = sum(values) / len(values)
        return avg_corr * 10
    except:
        return 5.0

def calc_asset_risk_score(symbol: str, corr_matrix: dict) -> dict:
    """Calcule le score de risque complet (1-10) pour un asset."""
    vol = calc_volatility_24h(symbol)
    liq = 10 - calc_liquidity_score(symbol)
    conc = calc_concentration_risk(symbol)
    corr = calc_systemic_correlation(symbol, corr_matrix)

    weights = {"volatility": 0.25, "liquidity": 0.20, "concentration": 0.30, "correlation": 0.25}
    score = (
        vol * weights["volatility"] +
        liq * weights["liquidity"] +
        conc * weights["concentration"] +
        corr * weights["correlation"]
    )

    score = min(10.0, max(1.0, score))

    return {
        "symbol": symbol,
        "score": round(score, 1),
        "volatility": round(vol, 1),
        "liquidity": round(10 - liq, 1),
        "concentration": round(conc, 1),
        "correlation": round(corr, 1),
        "risk_level": "🔴 CRITIQUE" if score >= 8 else "🟠 ÉLEVÉ" if score >= 6 else "🟡 MODÉRÉ" if score >= 4 else "🟢 BAS"
    }

def get_risk_monitor_data() -> dict:
    """Fonction principale retournant toutes les données du Risk Monitor."""
    try:
        corr_matrix = calculate_correlation_matrix(symbols=SYMBOLS)

        scores = []
        for symbol in SYMBOLS:
            score_data = calc_asset_risk_score(symbol, corr_matrix)
            scores.append(score_data)

        scores.sort(key=lambda x: x["score"], reverse=True)

        alerts = []
        correlations_data = corr_matrix.get("correlations", {})

        btc_corr_nasdaq = correlations_data.get("BTC", {}).get("NASDAQ", 0)
        if btc_corr_nasdaq and btc_corr_nasdaq < 0.3:
            alerts.append({
                "type": "divergence",
                "message": "⚠️ Décorrélation BTC-Nasdaq : changement de régime probable",
                "severity": "high"
            })

        avg_corr = sum(
            abs(float(v)) for symbol_corrs in correlations_data.values()
            for v in symbol_corrs.values() if v
        ) / max(1, sum(len(v) for v in correlations_data.values()))

        if avg_corr > 0.8:
            alerts.append({
                "type": "high_correlation",
                "message": "🔴 Toutes les cryptos sont corrélées : risque systémique élevé",
                "severity": "critical"
            })
        elif avg_corr < 0.4:
            alerts.append({
                "type": "low_correlation",
                "message": "🟢 Corrélations basses : conditions favorables pour la diversification",
                "severity": "positive"
            })

        critical_scores = [s for s in scores if s["score"] >= 8]
        if critical_scores:
            assets_str = ", ".join([s["symbol"] for s in critical_scores[:3]])
            alerts.append({
                "type": "high_risk_assets",
                "message": f"⚠️ Assets critiques ({assets_str}) : volatilité/concentration élevées",
                "severity": "high"
            })

        return {
            "matrix": corr_matrix,
            "scores": scores,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat(),
            "avg_correlation": round(avg_corr, 2)
        }
    except Exception as e:
        print(f"[Risk Monitor] Error: {e}")
        return {
            "matrix": {},
            "scores": [],
            "alerts": [{"type": "error", "message": f"Erreur: {str(e)}", "severity": "low"}],
            "timestamp": datetime.now().isoformat()
        }

init_risk_monitor()
