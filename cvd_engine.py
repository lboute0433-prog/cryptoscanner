"""
CVD Engine — Cumulative Volume Delta
Source: Bybit klines (taker buy ratio proxy + candle direction fallback)
"""
import requests
import time
from datetime import datetime

BYBIT_BASE = "https://api.bybit.com"


def _fetch_klines(symbol, interval="60", limit=100):
    """Recupere les klines Bybit."""
    try:
        r = requests.get(
            f"{BYBIT_BASE}/v5/market/kline",
            params={"category": "linear", "symbol": symbol, "interval": interval, "limit": limit},
            timeout=8,
        )
        if r.status_code != 200:
            return []
        return r.json().get("result", {}).get("list", [])
    except Exception as e:
        print(f"[CVD] klines {symbol}: {e}")
        return []


def _fetch_taker_ratio(symbol, limit=100):
    """Proxy buy/sell via endpoint public Bybit account-ratio."""
    try:
        r = requests.get(
            f"{BYBIT_BASE}/v5/market/account-ratio",
            params={"category": "linear", "symbol": symbol, "period": "1h", "limit": limit},
            timeout=8,
        )
        if r.status_code != 200:
            return []
        return r.json().get("result", {}).get("list", [])
    except Exception as e:
        print(f"[CVD] ratio {symbol}: {e}")
        return []


def get_cvd_data(symbol="BTCUSDT", interval="60", limit=48):
    """
    Calcule un CVD simplifie:
    - delta = volume * (buy_ratio - sell_ratio) si ratio dispo
    - sinon fallback direction bougie
    """
    try:
        klines = _fetch_klines(symbol, interval, limit)
        if not klines:
            return {"ok": False, "error": "Pas de donnees Bybit"}

        ratio_data = _fetch_taker_ratio(symbol, limit)
        cvd_points = []
        cumulative = 0.0

        for i, k in enumerate(reversed(klines)):
            ts = int(k[0]) // 1000
            open_p = float(k[1])
            close = float(k[4])
            vol = float(k[5])

            if ratio_data and i < len(ratio_data):
                rec = ratio_data[i] if i < len(ratio_data) else None
                if rec:
                    buy_ratio = float(rec.get("buyRatio", 0.5) or 0.5)
                    buy_vol = vol * buy_ratio
                    sell_vol = vol * (1 - buy_ratio)
                    delta = buy_vol - sell_vol
                else:
                    delta = 0.0
            else:
                delta = vol if close >= open_p else -vol

            cumulative += delta
            cvd_points.append(
                {
                    "ts": ts,
                    "time": datetime.fromtimestamp(ts).strftime("%d/%m %H:%M"),
                    "close": close,
                    "cvd": round(cumulative, 2),
                    "delta": round(delta, 2),
                    "vol": round(vol, 2),
                }
            )

        divergence = "neutral"
        divergence_msg = "Pas de divergence notable"
        if len(cvd_points) >= 6:
            recent = cvd_points[-6:]
            price_trend = recent[-1]["close"] - recent[0]["close"]
            cvd_trend = recent[-1]["cvd"] - recent[0]["cvd"]
            if price_trend > 0 and cvd_trend < 0:
                divergence = "bearish"
                divergence_msg = "Divergence baissiere: prix monte mais CVD baisse (distribution)."
            elif price_trend < 0 and cvd_trend > 0:
                divergence = "bullish"
                divergence_msg = "Divergence haussiere: prix baisse mais CVD monte (accumulation)."

        return {
            "ok": True,
            "symbol": symbol,
            "interval": interval,
            "points": cvd_points[-24:],
            "current_cvd": cvd_points[-1]["cvd"] if cvd_points else 0,
            "current_price": cvd_points[-1]["close"] if cvd_points else 0,
            "divergence": divergence,
            "divergence_msg": divergence_msg,
            "total_points": len(cvd_points),
        }
    except Exception as e:
        print(f"[CVD] Erreur: {e}")
        return {"ok": False, "error": str(e)}


def get_cvd_multi(symbols=None, interval="60"):
    """CVD pour plusieurs actifs."""
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT"]
    result = {}
    for sym in symbols:
        result[sym] = get_cvd_data(sym, interval)
        time.sleep(0.25)
    return result

