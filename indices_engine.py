#!/usr/bin/env python3
"""
CryptoScanner Pro V11 — Indices & Multi-Exchange Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Indices boursiers : S&P500, Nasdaq, CAC40, DAX, Nikkei, VIX, DXY
• Matières premières : Or, Argent, Pétrole WTI/Brent, Gaz naturel
• Corrélations cross-marchés (Crypto ↔ VIX ↔ DXY ↔ Indices)
• Score de Risque Global (Market Mood Index 0-100)
• Exchange Bybit — Spot + Futures
• Exchange OKX  — Spot + Futures
• Exchange Coinbase — Spot
"""

import requests
import sqlite3
from db import get_connection
import time
import threading
import os
from datetime import datetime
from typing import Optional

DB_PATH = "cryptoscanner.db"

# ── APIs ──────────────────────────────────────────────────────
YAHOO_FINANCE_URL  = "https://query1.finance.yahoo.com/v8/finance/chart"
YAHOO_QUOTE_URL    = "https://query1.finance.yahoo.com/v7/finance/quote"
COINCAP_URL        = "https://api.coincap.io/v2"

BYBIT_SPOT_URL     = "https://api.bybit.com/v5/market/tickers"
BYBIT_KLINES_URL   = "https://api.bybit.com/v5/market/kline"
BYBIT_FUNDING_URL  = "https://api.bybit.com/v5/market/funding/history"

OKX_TICKER_URL     = "https://www.okx.com/api/v5/market/tickers"
OKX_KLINES_URL     = "https://www.okx.com/api/v5/market/candles"
OKX_FUNDING_URL    = "https://www.okx.com/api/v5/public/funding-rate"

COINBASE_TICKER    = "https://api.coinbase.com/v2/exchange-rates"
COINBASE_PRODUCTS  = "https://api.exchange.coinbase.com/products"

# ── Catalogue des indices ──────────────────────────────────────
INDICES_CONFIG = {
    # Indices US
    "SP500":   {"symbol": "^GSPC",    "name": "S&P 500",         "emoji": "🇺🇸", "type": "index",     "region": "us"},
    "NASDAQ":  {"symbol": "^IXIC",    "name": "Nasdaq Composite","emoji": "💻", "type": "index",     "region": "us"},
    "DOW":     {"symbol": "^DJI",     "name": "Dow Jones",       "emoji": "🏦", "type": "index",     "region": "us"},
    "SP500_F": {"symbol": "ES=F",     "name": "S&P 500 Futures", "emoji": "📊", "type": "futures",   "region": "us"},
    # Indices Europe
    "CAC40":   {"symbol": "^FCHI",    "name": "CAC 40",          "emoji": "🇫🇷", "type": "index",     "region": "eu"},
    "DAX":     {"symbol": "^GDAXI",   "name": "DAX",             "emoji": "🇩🇪", "type": "index",     "region": "eu"},
    "FTSE":    {"symbol": "^FTSE",    "name": "FTSE 100",        "emoji": "🇬🇧", "type": "index",     "region": "eu"},
    "EUROSTOXX":{"symbol":"^STOXX50E","name": "Euro Stoxx 50",   "emoji": "🇪🇺", "type": "index",     "region": "eu"},
    # Indices Asie
    "NIKKEI":  {"symbol": "^N225",    "name": "Nikkei 225",      "emoji": "🇯🇵", "type": "index",     "region": "asia"},
    "HANGSENG":{"symbol": "^HSI",     "name": "Hang Seng",       "emoji": "🇭🇰", "type": "index",     "region": "asia"},
    # Indicateurs de volatilité / fear
    "VIX":     {"symbol": "^VIX",     "name": "VIX (Fear Index)","emoji": "😱", "type": "volatility","region": "us"},
    "VVIX":    {"symbol": "^VVIX",    "name": "VVIX",            "emoji": "📉", "type": "volatility","region": "us"},
    # Dollar Index
    "DXY":     {"symbol": "DX-Y.NYB", "name": "Dollar Index",    "emoji": "💵", "type": "currency",  "region": "global"},
    # Matières premières
    "GOLD":    {"symbol": "GC=F",     "name": "Or (Gold)",       "emoji": "🥇", "type": "commodity", "region": "global"},
    "SILVER":  {"symbol": "SI=F",     "name": "Argent (Silver)", "emoji": "🪙", "type": "commodity", "region": "global"},
    "OIL_WTI": {"symbol": "CL=F",     "name": "Pétrole WTI",     "emoji": "🛢️", "type": "commodity", "region": "global"},
    "OIL_BRENT":{"symbol":"BZ=F",     "name": "Pétrole Brent",   "emoji": "⛽", "type": "commodity", "region": "global"},
    "GAS":     {"symbol": "NG=F",     "name": "Gaz Naturel",     "emoji": "🔥", "type": "commodity", "region": "global"},
    # ETFs populaires
    "SPY":     {"symbol": "SPY",      "name": "SPDR S&P 500 ETF","emoji": "📈", "type": "etf",       "region": "us"},
    "QQQ":     {"symbol": "QQQ",      "name": "Nasdaq 100 ETF",  "emoji": "💡", "type": "etf",       "region": "us"},
    "GLD":     {"symbol": "GLD",      "name": "Gold ETF",        "emoji": "🥇", "type": "etf",       "region": "global"},
}

# ── Cache ─────────────────────────────────────────────────────
_cache: dict = {}
_cache_lock = threading.Lock()

def _cache_set(key: str, value, ttl: int = 60):
    with _cache_lock:
        _cache[key] = {"value": value, "expires": time.time() + ttl}

def _cache_get(key: str):
    with _cache_lock:
        e = _cache.get(key)
        if e and time.time() < e["expires"]:
            return e["value"]
    return None


# ══════════════════════════════════════════════════════════════
# 1. INDICES BOURSIERS VIA YAHOO FINANCE
# ══════════════════════════════════════════════════════════════

def fetch_single_index(key: str) -> Optional[dict]:
    """Récupère un indice via Yahoo Finance (2 tentatives différentes)."""
    cfg = INDICES_CONFIG.get(key)
    if not cfg:
        return None

    cache_key = f"index_{key}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    symbol = cfg["symbol"]

    # Tentative 1 : Yahoo Finance v7 quote
    for attempt_url in [YAHOO_QUOTE_URL, "https://query2.finance.yahoo.com/v7/finance/quote"]:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
            r = requests.get(
                attempt_url,
                params={"symbols": symbol, "fields": "regularMarketPrice,regularMarketChangePercent,regularMarketPreviousClose,regularMarketDayHigh,regularMarketDayLow,fiftyTwoWeekHigh,fiftyTwoWeekLow"},
                headers=headers,
                timeout=8
            )
            data = r.json()
            results = data.get("quoteResponse", {}).get("result", [])
            if not results:
                continue

            q     = results[0]
            price = float(q.get("regularMarketPrice", 0) or 0)
            chg   = float(q.get("regularMarketChangePercent", 0) or 0)
            prev  = float(q.get("regularMarketPreviousClose", 0) or 0)

            if price <= 0:
                continue

            result = {
                "key":         key,
                "symbol":      symbol,
                "name":        cfg["name"],
                "emoji":       cfg["emoji"],
                "type":        cfg["type"],
                "region":      cfg["region"],
                "price":       round(price, 2),
                "change_pct":  round(chg, 2),
                "change_abs":  round(price - prev, 2) if prev else 0,
                "prev_close":  round(prev, 2),
                "day_high":    round(float(q.get("regularMarketDayHigh", 0) or 0), 2),
                "day_low":     round(float(q.get("regularMarketDayLow",  0) or 0), 2),
                "week52_high": round(float(q.get("fiftyTwoWeekHigh",     0) or 0), 2),
                "week52_low":  round(float(q.get("fiftyTwoWeekLow",      0) or 0), 2),
                "signal":      _interpret_index_signal(key, price, chg),
                "ts":          datetime.now().strftime("%H:%M:%S"),
                "demo":        False,
            }
            _cache_set(cache_key, result, 60)
            return result
        except Exception as e:
            print(f"[Indices] {key} tentative {attempt_url[-10:]} error: {e}")
            continue

    # Tentative 2 : Yahoo Finance v8 chart (autre endpoint)
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"interval": "1d", "range": "2d"},
            headers=headers,
            timeout=8
        )
        data = r.json()
        meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
        price = float(meta.get("regularMarketPrice", 0) or 0)
        prev  = float(meta.get("previousClose", 0) or meta.get("chartPreviousClose", 0) or 0)
        chg   = ((price - prev) / prev * 100) if prev else 0

        if price > 0:
            result = {
                "key": key, "symbol": symbol, "name": cfg["name"],
                "emoji": cfg["emoji"], "type": cfg["type"], "region": cfg["region"],
                "price": round(price, 2), "change_pct": round(chg, 2),
                "change_abs": round(price - prev, 2),
                "prev_close": round(prev, 2),
                "day_high": round(float(meta.get("regularMarketDayHigh", price) or price), 2),
                "day_low":  round(float(meta.get("regularMarketDayLow",  price) or price), 2),
                "week52_high": 0, "week52_low": 0,
                "signal": _interpret_index_signal(key, price, chg),
                "ts": datetime.now().strftime("%H:%M:%S"),
                "demo": False,
            }
            _cache_set(cache_key, result, 60)
            return result
    except Exception as e:
        print(f"[Indices] {key} v8 chart error: {e}")

    # Fallback démo — clairement marqué
    print(f"[Indices] {key} → données de démonstration (Yahoo Finance indisponible)")
    return _get_demo_index(key, cfg)


def fetch_all_indices(keys: list = None) -> dict:
    """Récupère tous les indices (ou ceux spécifiés)."""
    if keys is None:
        keys = list(INDICES_CONFIG.keys())

    results  = {}
    errors   = []
    for key in keys:
        data = fetch_single_index(key)
        if data:
            results[key] = data
        else:
            errors.append(key)

    return {
        "indices": results,
        "count":   len(results),
        "errors":  errors,
        "ts":      datetime.now().strftime("%H:%M:%S"),
    }


def _interpret_index_signal(key: str, price: float, change_pct: float) -> dict:
    """Interprétation contextuelle selon le type d'indice."""
    # VIX : logique inversée
    if key == "VIX":
        if price > 30:
            return {"label": "😱 Panique — Signal achat contrarien", "type": "bullish_crypto", "level": "extreme"}
        elif price > 20:
            return {"label": "😰 Peur — Prudence requise", "type": "bearish_crypto", "level": "high"}
        elif price < 12:
            return {"label": "😌 Complaisance — Marché trop calme", "type": "neutral", "level": "low"}
        return {"label": "😐 VIX normal", "type": "neutral", "level": "normal"}

    # DXY
    if key == "DXY":
        if change_pct > 0.5:
            return {"label": "💪 Dollar fort — Pression sur crypto/or", "type": "bearish_crypto", "level": "strong"}
        elif change_pct < -0.5:
            return {"label": "📉 Dollar faible — Risk-ON", "type": "bullish_crypto", "level": "weak"}
        return {"label": "⚪ Dollar stable", "type": "neutral", "level": "neutral"}

    # Indices classiques
    if change_pct > 1.5:
        return {"label": "🚀 Forte hausse — Risk-ON positif", "type": "bullish_crypto", "level": "strong"}
    elif change_pct > 0.5:
        return {"label": "📈 Hausse modérée — Positif", "type": "bullish_crypto", "level": "moderate"}
    elif change_pct < -1.5:
        return {"label": "💥 Forte baisse — Risk-OFF", "type": "bearish_crypto", "level": "strong"}
    elif change_pct < -0.5:
        return {"label": "📉 Baisse modérée — Prudence", "type": "bearish_crypto", "level": "moderate"}
    return {"label": "⚪ Stable", "type": "neutral", "level": "neutral"}


def _get_demo_index(key: str, cfg: dict) -> dict:
    """Données de démonstration en cas d'erreur API."""
    demo_prices = {
        "SP500": 5200, "NASDAQ": 16400, "DOW": 39000, "CAC40": 8100,
        "DAX": 17800, "FTSE": 7700, "NIKKEI": 39500, "VIX": 18.5,
        "DXY": 104.2, "GOLD": 2340, "SILVER": 27.5, "OIL_WTI": 82.5,
        "OIL_BRENT": 87.0, "GAS": 1.85, "QQQ": 440, "SPY": 520,
    }
    price = demo_prices.get(key, 100)
    return {
        "key": key, "symbol": cfg["symbol"], "name": cfg["name"],
        "emoji": cfg["emoji"], "type": cfg["type"], "region": cfg["region"],
        "price": price, "change_pct": 0.0, "change_abs": 0.0,
        "prev_close": price, "day_high": price * 1.005,
        "day_low": price * 0.995, "week52_high": price * 1.2,
        "week52_low": price * 0.8,
        "signal": _interpret_index_signal(key, price, 0.0),
        "ts": datetime.now().strftime("%H:%M:%S"),
        "demo": True,
    }


# ══════════════════════════════════════════════════════════════
# 2. SCORE DE RISQUE GLOBAL (Market Mood Index 0-100)
# ══════════════════════════════════════════════════════════════

def calc_market_mood_score(
    vix: float = None,
    fear_greed: int = None,
    dxy_change: float = None,
    btc_dominance: float = None,
    sp500_change: float = None,
    funding_avg: float = None,
    btc_change: float = None,
) -> dict:
    """
    Calcule le Market Mood Index (0-100).
    
    0-25   : 🟢 Risk-ON fort  (favorable)
    26-50  : 🟡 Modérément Risk-ON
    51-75  : 🟠 Prudence — Risk-OFF modéré
    76-100 : 🔴 Risk-OFF fort  (dangereux)
    
    Score élevé = danger = risk-off
    Score faible = opportunité = risk-on
    """
    score  = 50  # Base neutre
    detail = []

    # ── VIX (peur du marché traditionnel) — poids 25% ────────
    if vix is not None:
        if vix > 35:
            score += 25; detail.append(f"😱 VIX {vix:.1f} — Panique extrême (+25)")
        elif vix > 25:
            score += 15; detail.append(f"😰 VIX {vix:.1f} — Peur élevée (+15)")
        elif vix > 20:
            score += 8;  detail.append(f"😐 VIX {vix:.1f} — Légère anxiété (+8)")
        elif vix < 12:
            score -= 10; detail.append(f"😌 VIX {vix:.1f} — Complaisance (-10)")
        else:
            detail.append(f"✅ VIX {vix:.1f} — Normal (0)")

    # ── Fear & Greed Crypto — poids 20% ──────────────────────
    if fear_greed is not None:
        if fear_greed < 20:
            score -= 15; detail.append(f"😱 Fear&Greed {fear_greed} — Peur extrême (-15 risk-on signal)")
        elif fear_greed < 35:
            score -= 8;  detail.append(f"😰 Fear&Greed {fear_greed} — Peur (-8)")
        elif fear_greed > 80:
            score += 15; detail.append(f"🤑 Fear&Greed {fear_greed} — Avidité extrême (+15)")
        elif fear_greed > 65:
            score += 8;  detail.append(f"😎 Fear&Greed {fear_greed} — Avidité (+8)")
        else:
            detail.append(f"⚪ Fear&Greed {fear_greed} — Neutre (0)")

    # ── DXY (force du dollar) — poids 15% ────────────────────
    if dxy_change is not None:
        if dxy_change > 0.8:
            score += 15; detail.append(f"💪 DXY +{dxy_change:.1f}% — Dollar fort, Risk-OFF (+15)")
        elif dxy_change > 0.3:
            score += 8;  detail.append(f"📈 DXY +{dxy_change:.1f}% — Dollar modérément fort (+8)")
        elif dxy_change < -0.8:
            score -= 12; detail.append(f"📉 DXY {dxy_change:.1f}% — Dollar faible, Risk-ON (-12)")
        elif dxy_change < -0.3:
            score -= 6;  detail.append(f"📉 DXY {dxy_change:.1f}% — Dollar en baisse (-6)")

    # ── S&P 500 direction — poids 15% ────────────────────────
    if sp500_change is not None:
        if sp500_change < -2:
            score += 15; detail.append(f"💥 S&P500 {sp500_change:.1f}% — Baisse forte, Risk-OFF (+15)")
        elif sp500_change < -1:
            score += 8;  detail.append(f"📉 S&P500 {sp500_change:.1f}% (+8)")
        elif sp500_change > 1.5:
            score -= 10; detail.append(f"🚀 S&P500 +{sp500_change:.1f}% — Hausse, Risk-ON (-10)")
        elif sp500_change > 0.5:
            score -= 5;  detail.append(f"📈 S&P500 +{sp500_change:.1f}% (-5)")

    # ── Funding Rate moyen BTC (surlevier) — poids 12% ───────
    if funding_avg is not None:
        if funding_avg > 0.08:
            score += 12; detail.append(f"💸 Funding {funding_avg:.2f}% — Trop de longs (+12)")
        elif funding_avg > 0.05:
            score += 6;  detail.append(f"💸 Funding {funding_avg:.2f}% élevé (+6)")
        elif funding_avg < -0.03:
            score -= 10; detail.append(f"💸 Funding {funding_avg:.2f}% négatif — Shorts surreprésentés (-10)")

    # ── BTC Dominance (saison altcoins = risque) — poids 8% ──
    if btc_dominance is not None:
        if btc_dominance < 42:
            score += 8;  detail.append(f"🎰 BTC Dom {btc_dominance:.1f}% bas — Risque spéculatif (+8)")
        elif btc_dominance > 58:
            score -= 5;  detail.append(f"🏛️ BTC Dom {btc_dominance:.1f}% élevé — Fuite vers qualité (-5)")

    # ── BTC Price action récente — poids 5% ──────────────────
    if btc_change is not None:
        if btc_change < -5:
            score += 5;  detail.append(f"📉 BTC {btc_change:.1f}% (+5)")
        elif btc_change > 5:
            score -= 3;  detail.append(f"📈 BTC +{btc_change:.1f}% (-3)")

    score = max(0, min(100, score))

    # Interprétation
    if score <= 25:
        label   = "🟢 Risk-ON Fort"
        color   = "#00d4a8"
        advice  = "Conditions favorables — Marchés en mode risk-on"
    elif score <= 45:
        label   = "🟡 Risk-ON Modéré"
        color   = "#ffc107"
        advice  = "Conditions positives avec quelques signaux de prudence"
    elif score <= 60:
        label   = "⚪ Neutre"
        color   = "#888888"
        advice  = "Marché équilibré — Pas de signal fort clair"
    elif score <= 75:
        label   = "🟠 Prudence"
        color   = "#ff9800"
        advice  = "Signaux Risk-OFF présents — Réduire l'exposition"
    else:
        label   = "🔴 Risk-OFF Fort"
        color   = "#f44336"
        advice  = "Conditions défavorables — Protéger le capital"

    return {
        "score":   score,
        "label":   label,
        "color":   color,
        "advice":  advice,
        "detail":  detail,
        "ts":      datetime.now().strftime("%H:%M:%S"),
    }


# ══════════════════════════════════════════════════════════════
# 3. BYBIT ENGINE
# ══════════════════════════════════════════════════════════════

def fetch_bybit_spot() -> list:
    """Récupère les tickers Spot Bybit."""
    cache_key = "bybit_spot"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    try:
        r = requests.get(
            BYBIT_SPOT_URL,
            params={"category": "spot"},
            timeout=8
        )
        data = r.json()
        if data.get("retCode") != 0:
            raise ValueError(data.get("retMsg", "Erreur Bybit"))

        coins = []
        for t in data.get("result", {}).get("list", []):
            sym = t.get("symbol", "")
            if not sym.endswith("USDT"):
                continue
            try:
                price  = float(t.get("lastPrice", 0))
                chg    = float(t.get("price24hPcnt", 0)) * 100
                vol    = float(t.get("turnover24h", 0))
                high   = float(t.get("highPrice24h", 0))
                low    = float(t.get("lowPrice24h", 0))
                if price <= 0 or vol < 50_000:
                    continue
                coins.append({
                    "symbol":      sym.replace("USDT", ""),
                    "price":       price,
                    "change_pct":  round(chg, 2),
                    "volume_usdt": vol,
                    "high":        high,
                    "low":         low,
                    "exchange":    "bybit",
                    "type":        "spot",
                    "market":      "bybit_spot",
                })
            except (ValueError, KeyError):
                continue

        coins.sort(key=lambda x: x["volume_usdt"], reverse=True)
        _cache_set(cache_key, coins, 15)
        return coins
    except Exception as e:
        print(f"[Bybit] Spot error: {e}")
        return []


def fetch_bybit_perp() -> list:
    """Récupère les contrats perpétuels Bybit USDT."""
    cache_key = "bybit_perp"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    try:
        r = requests.get(
            BYBIT_SPOT_URL,
            params={"category": "linear"},  # USDT perps
            timeout=8
        )
        data = r.json()
        if data.get("retCode") != 0:
            return []

        perps = []
        # Récupérer aussi les funding rates
        funding_map = _fetch_bybit_funding()

        for t in data.get("result", {}).get("list", []):
            sym = t.get("symbol", "")
            if not sym.endswith("USDT"):
                continue
            try:
                price   = float(t.get("lastPrice", 0))
                chg     = float(t.get("price24hPcnt", 0)) * 100
                vol     = float(t.get("turnover24h", 0))
                oi      = float(t.get("openInterest", 0))
                funding = funding_map.get(sym, 0)
                if price <= 0 or vol < 100_000:
                    continue

                if funding > 0.05:   funding_sent = "🔴 Baissier"
                elif funding < -0.01: funding_sent = "🟢 Haussier"
                else:                 funding_sent = "⚪ Neutre"

                perps.append({
                    "symbol":        sym.replace("USDT", ""),
                    "pair":          sym,
                    "price":         price,
                    "change_pct":    round(chg, 2),
                    "volume_usdt":   vol,
                    "open_interest": oi,
                    "funding_rate":  round(funding, 4),
                    "funding_sent":  funding_sent,
                    "exchange":      "bybit",
                    "type":          "perp",
                    "market":        "bybit_perp",
                })
            except (ValueError, KeyError):
                continue

        perps.sort(key=lambda x: x["volume_usdt"], reverse=True)
        _cache_set(cache_key, perps[:300], 15)
        return perps[:300]
    except Exception as e:
        print(f"[Bybit] Perp error: {e}")
        return []


def _fetch_bybit_funding() -> dict:
    """Récupère les derniers funding rates Bybit."""
    try:
        r = requests.get(
            BYBIT_SPOT_URL,
            params={"category": "linear", "limit": "200"},
            timeout=6
        )
        data = r.json()
        result = {}
        for t in data.get("result", {}).get("list", []):
            sym = t.get("symbol", "")
            fr  = t.get("fundingRate", None)
            if fr is not None and fr != "":
                try:
                    result[sym] = float(fr) * 100
                except (ValueError, TypeError):
                    pass
        return result
    except Exception:
        return {}


def fetch_bybit_candles(symbol: str, interval: str = "60", limit: int = 100) -> list:
    """Bougies OHLCV Bybit (interval en minutes: 1,3,5,15,30,60,120,240,360,720,D,W,M)."""
    cache_key = f"bybit_candles_{symbol}_{interval}"
    cached    = _cache_get(cache_key)
    if cached:
        return cached
    try:
        av_interval = {"15m":"15","1h":"60","4h":"240","1d":"D"}.get(interval, interval)
        r = requests.get(
            BYBIT_KLINES_URL,
            params={
                "category": "linear",
                "symbol":   symbol + "USDT",
                "interval": av_interval,
                "limit":    limit,
            },
            timeout=8
        )
        data = r.json()
        candles = []
        for c in reversed(data.get("result", {}).get("list", [])):
            candles.append({
                "t": int(c[0]),
                "o": float(c[1]),
                "h": float(c[2]),
                "l": float(c[3]),
                "c": float(c[4]),
                "v": float(c[5]),
            })
        _cache_set(cache_key, candles, 60)
        return candles
    except Exception as e:
        print(f"[Bybit] Candles {symbol} error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
# 4. OKX ENGINE
# ══════════════════════════════════════════════════════════════

def fetch_okx_spot() -> list:
    """Récupère les tickers Spot OKX."""
    cache_key = "okx_spot"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    try:
        r = requests.get(
            OKX_TICKER_URL,
            params={"instType": "SPOT"},
            timeout=8
        )
        data = r.json()
        if data.get("code") != "0":
            raise ValueError(data.get("msg", "Erreur OKX"))

        coins = []
        for t in data.get("data", []):
            inst = t.get("instId", "")
            if not inst.endswith("-USDT"):
                continue
            try:
                price = float(t.get("last", 0))
                open_ = float(t.get("open24h", 0))
                chg   = ((price - open_) / open_ * 100) if open_ else 0
                vol   = float(t.get("volCcy24h", 0))
                high  = float(t.get("high24h", 0))
                low   = float(t.get("low24h", 0))
                if price <= 0 or vol < 10_000:
                    continue
                base = inst.replace("-USDT", "")
                coins.append({
                    "symbol":      base,
                    "price":       price,
                    "change_pct":  round(chg, 2),
                    "volume_usdt": vol,
                    "high":        high,
                    "low":         low,
                    "exchange":    "okx",
                    "type":        "spot",
                    "market":      "okx_spot",
                })
            except (ValueError, ZeroDivisionError):
                continue

        coins.sort(key=lambda x: x["volume_usdt"], reverse=True)
        _cache_set(cache_key, coins, 15)
        return coins
    except Exception as e:
        print(f"[OKX] Spot error: {e}")
        return []


def fetch_okx_perp() -> list:
    """Récupère les contrats perpétuels OKX."""
    cache_key = "okx_perp"
    cached = _cache_get(cache_key)
    if cached:
        return cached
    try:
        r = requests.get(
            OKX_TICKER_URL,
            params={"instType": "SWAP"},
            timeout=8
        )
        data = r.json()
        if data.get("code") != "0":
            return []

        perps = []
        for t in data.get("data", []):
            inst = t.get("instId", "")
            if not inst.endswith("-USDT-SWAP"):
                continue
            try:
                price = float(t.get("last", 0))
                open_ = float(t.get("open24h", 0))
                chg   = ((price - open_) / open_ * 100) if open_ else 0
                vol   = float(t.get("volCcy24h", 0))
                oi    = float(t.get("openInterest", 0))
                if price <= 0 or vol < 50_000:
                    continue
                base = inst.replace("-USDT-SWAP", "")

                # Funding rate OKX
                funding = _fetch_okx_funding_single(inst)
                if funding > 0.05:   funding_sent = "🔴 Baissier"
                elif funding < -0.01: funding_sent = "🟢 Haussier"
                else:                 funding_sent = "⚪ Neutre"

                perps.append({
                    "symbol":        base,
                    "pair":          inst,
                    "price":         price,
                    "change_pct":    round(chg, 2),
                    "volume_usdt":   vol,
                    "open_interest": oi,
                    "funding_rate":  round(funding, 4),
                    "funding_sent":  funding_sent,
                    "exchange":      "okx",
                    "type":          "perp",
                    "market":        "okx_perp",
                })
            except (ValueError, ZeroDivisionError):
                continue

        perps.sort(key=lambda x: x["volume_usdt"], reverse=True)
        _cache_set(cache_key, perps[:300], 15)
        return perps[:300]
    except Exception as e:
        print(f"[OKX] Perp error: {e}")
        return []


def _fetch_okx_funding_single(inst_id: str) -> float:
    """Funding rate pour un instrument OKX."""
    try:
        r = requests.get(
            OKX_FUNDING_URL,
            params={"instId": inst_id},
            timeout=4
        )
        data = r.json()
        items = data.get("data", [])
        if items:
            return float(items[0].get("fundingRate", 0)) * 100
    except Exception:
        pass
    return 0.0


def fetch_okx_candles(symbol: str, interval: str = "1H", limit: int = 100) -> list:
    """Bougies OHLCV OKX."""
    cache_key = f"okx_candles_{symbol}_{interval}"
    cached    = _cache_get(cache_key)
    if cached:
        return cached
    try:
        av_interval = {"15m":"15m","1h":"1H","4h":"4H","1d":"1Dutc"}.get(interval, "1H")
        r = requests.get(
            OKX_KLINES_URL,
            params={
                "instId": symbol + "-USDT",
                "bar":    av_interval,
                "limit":  str(limit),
            },
            timeout=8
        )
        data = r.json()
        candles = []
        for c in reversed(data.get("data", [])):
            candles.append({
                "t": int(c[0]),
                "o": float(c[1]),
                "h": float(c[2]),
                "l": float(c[3]),
                "c": float(c[4]),
                "v": float(c[5]),
            })
        _cache_set(cache_key, candles, 60)
        return candles
    except Exception as e:
        print(f"[OKX] Candles {symbol} error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
# 5. COINBASE SPOT ENGINE
# ══════════════════════════════════════════════════════════════

def fetch_coinbase_spot() -> list:
    """Récupère les tickers Spot Coinbase Exchange."""
    cache_key = "coinbase_spot"
    cached    = _cache_get(cache_key)
    if cached:
        return cached
    try:
        r = requests.get(
            f"{COINBASE_PRODUCTS}",
            timeout=8
        )
        products = r.json()
        coins    = []
        usdt_products = [p for p in products if p.get("quote_currency") == "USD"
                         and p.get("status") == "online"][:100]

        for p in usdt_products:
            try:
                product_id = p["id"]
                stats_r    = requests.get(
                    f"{COINBASE_PRODUCTS}/{product_id}/stats",
                    timeout=4
                )
                s = stats_r.json()
                price  = float(s.get("last", 0))
                open_  = float(s.get("open", 0))
                chg    = ((price - open_) / open_ * 100) if open_ else 0
                vol    = float(s.get("volume", 0)) * price
                if price <= 0 or vol < 10_000:
                    continue
                coins.append({
                    "symbol":      p["base_currency"],
                    "price":       price,
                    "change_pct":  round(chg, 2),
                    "volume_usdt": vol,
                    "high":        float(s.get("high", 0)),
                    "low":         float(s.get("low", 0)),
                    "exchange":    "coinbase",
                    "type":        "spot",
                    "market":      "coinbase_spot",
                })
            except Exception:
                continue

        coins.sort(key=lambda x: x["volume_usdt"], reverse=True)
        _cache_set(cache_key, coins, 30)
        return coins
    except Exception as e:
        print(f"[Coinbase] error: {e}")
        return []


# ══════════════════════════════════════════════════════════════
# 6. AGRÉGATEUR MULTI-EXCHANGE
# ══════════════════════════════════════════════════════════════

def fetch_multi_exchange(exchanges: list = None) -> dict:
    """
    Agrège les données de plusieurs exchanges.
    Détecte les opportunités d'arbitrage entre exchanges.
    """
    if exchanges is None:
        exchanges = ["bybit", "okx"]

    all_coins = {}
    exchange_data = {}

    for exch in exchanges:
        if exch == "bybit":
            coins = fetch_bybit_spot()
        elif exch == "okx":
            coins = fetch_okx_spot()
        elif exch == "coinbase":
            coins = fetch_coinbase_spot()
        else:
            continue

        exchange_data[exch] = coins
        for c in coins:
            sym = c["symbol"]
            if sym not in all_coins:
                all_coins[sym] = []
            all_coins[sym].append({**c, "exchange": exch})

    # Détecter arbitrage (différence de prix > 0.3%)
    arbitrage = []
    for sym, listings in all_coins.items():
        if len(listings) < 2:
            continue
        prices = [(l["exchange"], l["price"]) for l in listings if l["price"] > 0]
        if len(prices) < 2:
            continue
        min_e, min_p = min(prices, key=lambda x: x[1])
        max_e, max_p = max(prices, key=lambda x: x[1])
        diff_pct = (max_p - min_p) / min_p * 100 if min_p > 0 else 0
        if diff_pct > 0.3:
            arbitrage.append({
                "symbol":   sym,
                "buy_on":   min_e,
                "sell_on":  max_e,
                "buy_price":  round(min_p, 6),
                "sell_price": round(max_p, 6),
                "diff_pct": round(diff_pct, 3),
            })

    arbitrage.sort(key=lambda x: x["diff_pct"], reverse=True)

    return {
        "exchanges":    exchange_data,
        "arbitrage":    arbitrage[:20],
        "total_coins":  len(all_coins),
        "ts":           datetime.now().strftime("%H:%M:%S"),
    }


# ══════════════════════════════════════════════════════════════
# 7. CORRÉLATIONS CROSS-MARCHÉS
# ══════════════════════════════════════════════════════════════

def get_cross_market_analysis(
    btc_change: float = 0,
    fear_greed: int = 50,
    vix: float = 18,
    dxy_change: float = 0,
    sp500_change: float = 0,
) -> dict:
    """
    Analyse croisée de tous les marchés.
    Génère des alertes et un résumé de situation.
    """
    alerts   = []
    summary  = []

    # ── Règles cross-marchés ──────────────────────────────────

    # 1. Risk-OFF classique
    if vix > 30 and btc_change < -3:
        alerts.append({
            "type": "danger",
            "title": "⚠️ Risk-OFF confirmé",
            "msg": f"VIX > 30 ({vix:.1f}) + BTC en baisse ({btc_change:.1f}%) — Sortir des positions risquées",
            "severity": "HIGH",
        })

    # 2. Capitulation (opportunité contrarien)
    if fear_greed < 15 and vix > 30:
        alerts.append({
            "type": "opportunity",
            "title": "🎯 Signal de capitulation",
            "msg": f"Fear&Greed {fear_greed} + VIX {vix:.1f} = Peur extrême — Historiquement acheteur à long terme",
            "severity": "HIGH",
        })

    # 3. Dollar fort
    if dxy_change > 0.8:
        alerts.append({
            "type": "warning",
            "title": "💵 Dollar en forte hausse",
            "msg": f"DXY +{dxy_change:.1f}% — Pression sur Or, Cryptos et Marchés émergents",
            "severity": "MEDIUM",
        })

    # 4. Saison Altcoins
    if btc_change > 5 and sp500_change > 0:
        alerts.append({
            "type": "info",
            "title": "🚀 Risk-ON généralisé",
            "msg": f"BTC +{btc_change:.1f}% + S&P500 +{sp500_change:.1f}% — Conditions favorables aux cryptos",
            "severity": "INFO",
        })

    # 5. Découplage Crypto/Equities
    if abs(btc_change - sp500_change) > 5:
        direction = "surperformance" if btc_change > sp500_change else "sous-performance"
        alerts.append({
            "type": "info",
            "title": f"📊 Découplage BTC/Actions",
            "msg": f"BTC {btc_change:.1f}% vs S&P500 {sp500_change:.1f}% — {direction} crypto notable",
            "severity": "LOW",
        })

    # Résumé textuel
    mood = calc_market_mood_score(
        vix=vix,
        fear_greed=fear_greed,
        dxy_change=dxy_change,
        sp500_change=sp500_change,
        btc_change=btc_change,
    )

    return {
        "mood":    mood,
        "alerts":  alerts,
        "summary": mood["advice"],
        "ts":      datetime.now().strftime("%H:%M:%S"),
    }


# ══════════════════════════════════════════════════════════════
# 8. INITIALISATION DB
# ══════════════════════════════════════════════════════════════

def init_indices_db():
    """Crée les tables indices si elles n'existent pas."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS indices_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT,
            price REAL,
            change_pct REAL DEFAULT 0,
            ts TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS mood_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            label TEXT,
            vix REAL,
            fear_greed INTEGER,
            dxy_change REAL,
            ts TEXT NOT NULL
        );
    """)
    conn.commit(); conn.close()
    print("[Indices] Tables initialisees")
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  