#!/usr/bin/env python3
"""
CryptoScanner Pro V11 — Forex Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Taux temps réel : Frankfurter (gratuit), Alpha Vantage (clé optionnelle)
• Paires majeures, mineures et exotiques
• Détection de sessions de trading (Tokyo, Londres, New York)
• Signaux techniques Forex (EMA crossover, RSI, Bollinger)
• Corrélations DXY ↔ Crypto
• Calendrier d'impact événements macro sur les paires
• Cache intelligent pour économiser les appels API
"""

import requests
import sqlite3
from db import get_connection
import os
import time
import threading
from datetime import datetime, timedelta
from typing import Optional

DB_PATH = "cryptoscanner.db"
ALPHA_VANTAGE_KEY = os.environ.get("ALPHA_VANTAGE_KEY", "")

# ── APIs gratuites ────────────────────────────────────────────
FRANKFURTER_BASE  = "https://api.frankfurter.app"
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
EXCHANGE_RATE_URL = "https://api.exchangerate-api.com/v4/latest"

# ── Catalogue des paires ──────────────────────────────────────
FOREX_PAIRS = {
    # Paires majeures (le plus tradées au monde)
    "majors": {
        "EUR/USD": {"name":"Euro / Dollar",         "emoji":"🇪🇺", "pip":0.0001, "category":"major"},
        "GBP/USD": {"name":"Livre / Dollar",        "emoji":"🇬🇧", "pip":0.0001, "category":"major"},
        "USD/JPY": {"name":"Dollar / Yen",          "emoji":"🇯🇵", "pip":0.01,   "category":"major"},
        "USD/CHF": {"name":"Dollar / Franc Suisse", "emoji":"🇨🇭", "pip":0.0001, "category":"major"},
        "AUD/USD": {"name":"Dollar Aus. / Dollar",  "emoji":"🇦🇺", "pip":0.0001, "category":"major"},
        "USD/CAD": {"name":"Dollar / Dollar Can.",  "emoji":"🇨🇦", "pip":0.0001, "category":"major"},
        "NZD/USD": {"name":"Dollar NZ / Dollar",    "emoji":"🇳🇿", "pip":0.0001, "category":"major"},
    },
    # Paires croisées (sans USD)
    "crosses": {
        "EUR/GBP": {"name":"Euro / Livre",          "emoji":"🇪🇺", "pip":0.0001, "category":"cross"},
        "EUR/JPY": {"name":"Euro / Yen",            "emoji":"🇯🇵", "pip":0.01,   "category":"cross"},
        "EUR/CHF": {"name":"Euro / Franc Suisse",   "emoji":"🇨🇭", "pip":0.0001, "category":"cross"},
        "GBP/JPY": {"name":"Livre / Yen",           "emoji":"🇬🇧", "pip":0.01,   "category":"cross"},
        "GBP/AUD": {"name":"Livre / Dollar Aus.",   "emoji":"🇦🇺", "pip":0.0001, "category":"cross"},
        "EUR/AUD": {"name":"Euro / Dollar Aus.",    "emoji":"🇦🇺", "pip":0.0001, "category":"cross"},
        "EUR/CAD": {"name":"Euro / Dollar Can.",    "emoji":"🇨🇦", "pip":0.0001, "category":"cross"},
    },
    # Paires exotiques (plus volatiles)
    "exotics": {
        "USD/TRY": {"name":"Dollar / Livre Turque", "emoji":"🇹🇷", "pip":0.0001, "category":"exotic"},
        "USD/ZAR": {"name":"Dollar / Rand SA",      "emoji":"🇿🇦", "pip":0.0001, "category":"exotic"},
        "USD/MXN": {"name":"Dollar / Peso Mex.",    "emoji":"🇲🇽", "pip":0.0001, "category":"exotic"},
        "USD/BRL": {"name":"Dollar / Real Brés.",   "emoji":"🇧🇷", "pip":0.0001, "category":"exotic"},
        "USD/SGD": {"name":"Dollar / Dollar Sing.", "emoji":"🇸🇬", "pip":0.0001, "category":"exotic"},
    },
}

# Toutes les paires en dict plat
ALL_PAIRS = {**FOREX_PAIRS["majors"], **FOREX_PAIRS["crosses"], **FOREX_PAIRS["exotics"]}

# ── Sessions de trading Forex (heure Paris / CET) ────────────
TRADING_SESSIONS = {
    "sydney":    {"open":  7, "close": 16, "emoji":"🇦🇺", "name":"Sydney"},
    "tokyo":     {"open":  1, "close": 10, "emoji":"🇯🇵", "name":"Tokyo"},
    "london":    {"open":  8, "close": 17, "emoji":"🇬🇧", "name":"Londres"},
    "new_york":  {"open": 14, "close": 23, "emoji":"🇺🇸", "name":"New York"},
}

# Paires les plus actives par session
SESSION_PAIRS = {
    "tokyo":    ["USD/JPY","EUR/JPY","GBP/JPY","AUD/USD","NZD/USD"],
    "london":   ["EUR/USD","GBP/USD","EUR/GBP","EUR/CHF","GBP/CHF"],
    "new_york": ["EUR/USD","GBP/USD","USD/CAD","USD/CHF","USD/JPY"],
    "overlap":  ["EUR/USD","GBP/USD"],  # Overlap Londres/NY = plus forte liquidité
}

# ── Cache thread-safe ─────────────────────────────────────────
_cache: dict = {}
_cache_lock = threading.Lock()

def _cache_set(key: str, value, ttl: int = 300):
    with _cache_lock:
        _cache[key] = {"value": value, "expires": time.time() + ttl}

def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() < entry["expires"]:
            return entry["value"]
        return None


# ══════════════════════════════════════════════════════════════
# 1. FETCH TAUX EN TEMPS RÉEL
# ══════════════════════════════════════════════════════════════

def fetch_forex_rates(base: str = "USD") -> dict:
    """
    Récupère les taux de change via Frankfurter (open source, sans clé API).
    Fallback sur exchangerate-api si indisponible.
    TTL cache : 5 minutes.
    """
    cache_key = f"forex_rates_{base}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    # Source 1 : Frankfurter (recommandée)
    try:
        r = requests.get(
            f"{FRANKFURTER_BASE}/latest",
            params={"from": base},
            timeout=8
        )
        data = r.json()
        if data.get("rates"):
            result = {
                "base":   data["base"],
                "rates":  data["rates"],
                "date":   data.get("date",""),
                "source": "frankfurter",
            }
            _cache_set(cache_key, result, 300)
            return result
    except Exception as e:
        print(f"[Forex] Frankfurter error: {e}")

    # Fallback : exchangerate-api (sans clé)
    try:
        r = requests.get(f"{EXCHANGE_RATE_URL}/{base}", timeout=8)
        data = r.json()
        if data.get("rates"):
            result = {
                "base":   base,
                "rates":  data["rates"],
                "date":   data.get("date",""),
                "source": "exchangerate-api",
            }
            _cache_set(cache_key, result, 300)
            return result
    except Exception as e:
        print(f"[Forex] ExchangeRate-API error: {e}")

    return {"base": base, "rates": {}, "source": "error"}


def fetch_all_pairs() -> list:
    """
    Construit les données complètes de toutes les paires Forex.
    Calcule la variation 24h en comparant les taux actuels aux taux d'hier.
    """
    cache_key = "forex_all_pairs"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    # Taux actuels
    rates_usd = fetch_forex_rates("USD")
    current   = rates_usd.get("rates", {})

    # Taux d'il y a 24h via Frankfurter historical
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        r = requests.get(
            f"{FRANKFURTER_BASE}/{yesterday}",
            params={"from": "USD"},
            timeout=8
        )
        prev_rates = r.json().get("rates", {})
    except Exception:
        prev_rates = {}

    result = []
    sessions = get_active_sessions()
    active_session_pairs = []
    for s in sessions:
        active_session_pairs.extend(SESSION_PAIRS.get(s["id"], []))

    for pair, info in ALL_PAIRS.items():
        from_sym, to_sym = pair.split("/")
        try:
            rate = _cross_rate(from_sym, to_sym, current)
            prev = _cross_rate(from_sym, to_sym, prev_rates) if prev_rates else None

            change_pct = 0.0
            change_pip = 0.0
            if prev and prev > 0:
                change_pct = round((rate - prev) / prev * 100, 4)
                change_pip = round((rate - prev) / info["pip"], 1)

            # Spread simulé (basé sur liquidité typique)
            spread = _estimate_spread(pair)

            result.append({
                "pair":          pair,
                "from":          from_sym,
                "to":            to_sym,
                "name":          info["name"],
                "emoji":         info["emoji"],
                "category":      info["category"],
                "rate":          round(rate, 5),
                "prev_rate":     round(prev, 5) if prev else None,
                "change_pct":    change_pct,
                "change_pip":    change_pip,
                "spread":        spread,
                "pip_value":     info["pip"],
                "is_active":     pair in active_session_pairs,
                "signal":        None,  # Rempli par analyze_forex_pair
                "ts":            datetime.now().strftime("%H:%M:%S"),
            })
        except Exception as e:
            print(f"[Forex] pair {pair} error: {e}")

    result.sort(key=lambda x: x["category"] + x["pair"])
    _cache_set(cache_key, result, 300)
    return result


def _cross_rate(from_sym: str, to_sym: str, rates: dict) -> float:
    """Calcule un taux croisé depuis des taux USD."""
    if not rates:
        raise ValueError("Rates vides")
    if from_sym == "USD":
        return float(rates.get(to_sym, 0))
    elif to_sym == "USD":
        from_rate = float(rates.get(from_sym, 0))
        return 1.0 / from_rate if from_rate else 0
    else:
        from_rate = float(rates.get(from_sym, 0))
        to_rate   = float(rates.get(to_sym, 0))
        return (to_rate / from_rate) if from_rate else 0


def _estimate_spread(pair: str) -> float:
    """Spread typique en pips par paire."""
    spreads = {
        "EUR/USD": 0.5, "GBP/USD": 0.8, "USD/JPY": 0.6,
        "USD/CHF": 1.0, "AUD/USD": 0.9, "USD/CAD": 1.1,
        "NZD/USD": 1.2, "EUR/GBP": 0.8, "EUR/JPY": 1.0,
        "GBP/JPY": 1.5, "USD/TRY": 8.0, "USD/ZAR": 12.0,
    }
    return spreads.get(pair, 2.0)


# ══════════════════════════════════════════════════════════════
# 2. SIGNAUX TECHNIQUES FOREX
# ══════════════════════════════════════════════════════════════

def fetch_forex_candles(pair: str, interval: str = "1h", limit: int = 100) -> list:
    """
    Récupère les bougies OHLC d'une paire Forex.
    Source : Alpha Vantage (gratuit avec clé).
    """
    cache_key = f"forex_candles_{pair}_{interval}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    if not ALPHA_VANTAGE_KEY:
        # Générer des données de démonstration réalistes
        return _generate_demo_candles(pair, limit)

    from_sym, to_sym = pair.split("/")
    av_interval = {"15m":"15min","1h":"60min","4h":"240min","1d":"daily"}.get(interval,"60min")

    try:
        function = "FX_INTRADAY" if interval != "1d" else "FX_DAILY"
        params   = {"apikey": ALPHA_VANTAGE_KEY, "from_symbol": from_sym, "to_symbol": to_sym,
                    "outputsize": "compact"}
        if function == "FX_INTRADAY":
            params.update({"function": function, "interval": av_interval})
        else:
            params["function"] = function

        r    = requests.get(ALPHA_VANTAGE_URL, params=params, timeout=12)
        data = r.json()

        # Clé dynamique selon la fonction
        key = [k for k in data if "Time Series" in k]
        if not key:
            return _generate_demo_candles(pair, limit)

        candles = []
        for ts, ohlc in sorted(data[key[0]].items(), reverse=True)[:limit]:
            candles.append({
                "t": int(datetime.fromisoformat(ts).timestamp() * 1000),
                "o": float(ohlc["1. open"]),
                "h": float(ohlc["2. high"]),
                "l": float(ohlc["3. low"]),
                "c": float(ohlc["4. close"]),
                "v": 0,  # Le Forex n'a pas de volume centralisé
            })
        candles.reverse()
        _cache_set(cache_key, candles, 60)
        return candles
    except Exception as e:
        print(f"[Forex] Candles {pair} error: {e}")
        return _generate_demo_candles(pair, limit)


def _generate_demo_candles(pair: str, limit: int = 100) -> list:
    """Génère des bougies de démonstration réalistes pour une paire."""
    import random
    base_prices = {
        "EUR/USD":1.085, "GBP/USD":1.265, "USD/JPY":150.5, "USD/CHF":0.895,
        "AUD/USD":0.652, "USD/CAD":1.365, "NZD/USD":0.604, "EUR/GBP":0.856,
        "EUR/JPY":163.2, "GBP/JPY":190.3, "USD/TRY":32.1,  "USD/ZAR":18.7,
    }
    price  = base_prices.get(pair, 1.2)
    candles = []
    now    = int(time.time()) * 1000

    random.seed(hash(pair) % 1000)
    for i in range(limit):
        chg  = random.gauss(0, 0.001)
        price = max(price * (1 + chg), 0.001)
        h    = price * (1 + abs(random.gauss(0, 0.0005)))
        l    = price * (1 - abs(random.gauss(0, 0.0005)))
        o    = price * (1 + random.gauss(0, 0.0003))
        candles.append({
            "t": now - (limit - i) * 3_600_000,
            "o": round(o, 5), "h": round(h, 5),
            "l": round(l, 5), "c": round(price, 5), "v": 0,
        })
    return candles


def analyze_forex_pair(pair: str, candles: list = None) -> Optional[dict]:
    """
    Analyse technique complète d'une paire Forex.
    Retourne un signal structuré (achat/vente/neutre + score).
    """
    if candles is None:
        candles = fetch_forex_candles(pair, "1h", 100)
    if len(candles) < 30:
        return None

    closes  = [c["c"] for c in candles]
    current = closes[-1]

    # Indicateurs
    rsi     = _calc_rsi(closes, 14)
    ema20   = _calc_ema(closes, 20)
    ema50   = _calc_ema(closes, 50)
    ema200  = _calc_ema(closes, 200) if len(closes) >= 200 else None
    bb_low, bb_mid, bb_high = _calc_bollinger(closes, 20)
    atr     = _calc_atr(candles, 14)

    signals = []
    score   = 50

    # ── EMA Crossover ─────────────────────────────────────────
    if ema20 and ema50:
        if ema20 > ema50:
            signals.append({"label": "📈 EMA20 > EMA50 (Haussier)", "type": "buy", "strength": 20})
            score += 20
        else:
            signals.append({"label": "📉 EMA20 < EMA50 (Baissier)", "type": "sell", "strength": 20})
            score -= 20

    # ── Prix vs EMA200 (tendance long terme) ──────────────────
    if ema200:
        if current > ema200:
            signals.append({"label": "📊 Au-dessus EMA200 (Tendance haussière)", "type": "buy", "strength": 15})
            score += 15
        else:
            signals.append({"label": "📊 Sous EMA200 (Tendance baissière)", "type": "sell", "strength": 15})
            score -= 15

    # ── RSI ───────────────────────────────────────────────────
    if rsi is not None:
        if rsi < 30:
            signals.append({"label": f"🟢 RSI {rsi:.0f} — Survente", "type": "buy", "strength": 25})
            score += 25
        elif rsi > 70:
            signals.append({"label": f"🔴 RSI {rsi:.0f} — Surachat", "type": "sell", "strength": 25})
            score -= 25
        elif rsi < 40:
            signals.append({"label": f"📉 RSI {rsi:.0f} — Zone basse", "type": "buy", "strength": 10})
            score += 10
        elif rsi > 60:
            signals.append({"label": f"📈 RSI {rsi:.0f} — Zone haute", "type": "sell", "strength": 10})
            score -= 10

    # ── Bollinger Bands ───────────────────────────────────────
    if bb_low and bb_high:
        if current <= bb_low:
            signals.append({"label": "📏 Sous BB inférieure — Rebond possible", "type": "buy", "strength": 20})
            score += 20
        elif current >= bb_high:
            signals.append({"label": "📏 Sur BB supérieure — Pullback possible", "type": "sell", "strength": 20})
            score -= 20

    # ── Momentum (variation sur 5 bougies) ───────────────────
    if len(closes) >= 5:
        momentum = (closes[-1] - closes[-6]) / closes[-6] * 100
        if momentum > 0.5:
            signals.append({"label": f"⚡ Momentum +{momentum:.2f}%", "type": "buy", "strength": 10})
            score += 10
        elif momentum < -0.5:
            signals.append({"label": f"⚡ Momentum {momentum:.2f}%", "type": "sell", "strength": 10})
            score -= 10

    score = max(0, min(100, score))

    # Direction globale
    buy_strength  = sum(s["strength"] for s in signals if s["type"] == "buy")
    sell_strength = sum(s["strength"] for s in signals if s["type"] == "sell")
    if buy_strength > sell_strength + 10:
        direction = "buy"
    elif sell_strength > buy_strength + 10:
        direction = "sell"
    else:
        direction = "neutral"

    # Support/Résistance (20 dernières bougies)
    recent = candles[-20:]
    resistance = max(c["h"] for c in recent)
    support    = min(c["l"] for c in recent)

    info = ALL_PAIRS.get(pair, {})

    return {
        "pair":       pair,
        "name":       info.get("name", pair),
        "rate":       round(current, 5),
        "rsi":        round(rsi, 1) if rsi else None,
        "ema20":      round(ema20, 5) if ema20 else None,
        "ema50":      round(ema50, 5) if ema50 else None,
        "ema200":     round(ema200, 5) if ema200 else None,
        "bb_low":     round(bb_low, 5) if bb_low else None,
        "bb_high":    round(bb_high, 5) if bb_high else None,
        "atr":        round(atr, 5) if atr else None,
        "support":    round(support, 5),
        "resistance": round(resistance, 5),
        "direction":  direction,
        "score":      score,
        "signals":    signals,
        "ts":         datetime.now().strftime("%H:%M:%S"),
    }


# ══════════════════════════════════════════════════════════════
# 3. SESSIONS DE TRADING
# ══════════════════════════════════════════════════════════════

def _is_forex_open() -> bool:
    """Le forex est fermé du vendredi 22h UTC au dimanche 22h UTC (heure Paris : sam 00h - lun 00h)."""
    now = datetime.now()
    wd = now.weekday()  # 0=lun, 5=sam, 6=dim
    return not (wd == 5 or wd == 6)


def get_active_sessions() -> list:
    """
    Retourne les sessions de trading actuellement ouvertes (heure Paris CET).
    Tient compte de l'overlap London/NY (= liquidité maximale).
    Retourne une liste vide le week-end (marchés fermés).
    """
    if not _is_forex_open():
        return []

    now_hour = datetime.now().hour
    active   = []

    for session_id, s in TRADING_SESSIONS.items():
        open_h  = s["open"]
        close_h = s["close"]
        if open_h <= now_hour < close_h:
            active.append({
                "id":      session_id,
                "name":    s["name"],
                "emoji":   s["emoji"],
                "closes":  f"{close_h:02d}:00",
                "pairs":   SESSION_PAIRS.get(session_id, []),
            })

    # Détecter l'overlap London/NY (14h-17h Paris)
    if 14 <= now_hour < 17:
        active.append({
            "id":    "overlap",
            "name":  "Overlap Londres/NY 🔥",
            "emoji": "⚡",
            "closes":"17:00",
            "pairs": SESSION_PAIRS["overlap"],
        })

    return active


def get_session_overview() -> dict:
    """Vue complète des sessions avec heures d'ouverture."""
    now_hour = datetime.now().hour
    is_weekend = not _is_forex_open()
    sessions = []
    for sid, s in TRADING_SESSIONS.items():
        is_open = (not is_weekend) and (s["open"] <= now_hour < s["close"])
        opens_in = None
        if not is_open:
            if is_weekend:
                opens_in = "Fermé (week-end)"
            else:
                h_diff = (s["open"] - now_hour) % 24
                opens_in = f"Dans {h_diff}h"
        sessions.append({
            "id":       sid,
            "name":     s["name"],
            "emoji":    s["emoji"],
            "open":     f"{s['open']:02d}:00",
            "close":    f"{s['close']:02d}:00",
            "is_open":  is_open,
            "opens_in": opens_in,
            "pairs":    SESSION_PAIRS.get(sid, []),
        })
    return {
        "sessions":        sessions,
        "active_count":    sum(1 for s in sessions if s["is_open"]),
        "best_session":    _get_best_session(now_hour) if not is_weekend else "📅 Marchés fermés — rouvrent lundi",
        "current_hour":    f"{now_hour:02d}:00",
    }


def _get_best_session(hour: int) -> str:
    if 14 <= hour < 17:   return "⚡ OVERLAP London/NY — Liquidité maximale"
    elif 8 <= hour < 17:  return "🇬🇧 Session Londres — Haute liquidité EUR/GBP"
    elif 14 <= hour < 23: return "🇺🇸 Session New York — Haute liquidité USD"
    elif 1 <= hour < 10:  return "🇯🇵 Session Tokyo — Paires JPY/AUD actives"
    else:                  return "🌙 Faible liquidité — Marchés calmes"


# ══════════════════════════════════════════════════════════════
# 4. CORRÉLATIONS FOREX ↔ CRYPTO
# ══════════════════════════════════════════════════════════════

def get_crypto_forex_correlations(crypto_prices: dict = None) -> dict:
    """
    Analyse les corrélations entre crypto et Forex.
    
    Corrélations historiques connues :
    - BTC / DXY   : Corrélation inverse (DXY fort = BTC baisse)
    - BTC / EUR/USD : Corrélation positive modérée
    - Risk assets / USD/JPY : Corrélation positive (risk-on)
    - Or / USD/CHF  : Corrélation positive (safe havens)
    """
    rates = fetch_forex_rates("USD")
    r = rates.get("rates", {})

    correlations = []

    # DXY simulé (indice dollar vs panier de devises)
    dxy_approx = _calc_dxy_approx(r)
    correlations.append({
        "pair":        "DXY (Dollar Index)",
        "value":       round(dxy_approx, 2),
        "change":      0,  # Serait calculé vs hier
        "impact":      "🔴 DXY fort = Pression sur BTC" if dxy_approx > 104 else "🟢 DXY faible = Favorable aux cryptos",
        "signal":      "bearish_crypto" if dxy_approx > 104 else "bullish_crypto",
        "strength":    "fort" if abs(dxy_approx - 100) > 4 else "modéré",
    })

    # EUR/USD
    eurusd = r.get("EUR", 0)
    if eurusd:
        eurusd_rate = 1 / eurusd if eurusd else 0
        correlations.append({
            "pair":    "EUR/USD",
            "value":   round(eurusd_rate, 4),
            "impact":  "🟢 EUR/USD fort = Risk-ON favorable aux cryptos" if eurusd_rate > 1.09 else "⚪ EUR/USD neutre",
            "signal":  "bullish_crypto" if eurusd_rate > 1.09 else "neutral",
            "strength":"modéré",
        })

    # USD/JPY (risk-on/risk-off baromètre)
    jpyusd = r.get("JPY", 0)
    if jpyusd:
        usdjpy = jpyusd  # USD/JPY direct
        correlations.append({
            "pair":    "USD/JPY",
            "value":   round(usdjpy, 2),
            "impact":  "🟢 USD/JPY > 145 = Risk-ON (yen faible)" if usdjpy > 145 else "🔴 USD/JPY < 145 = Risk-OFF (yen fort = safe haven)",
            "signal":  "bullish_crypto" if usdjpy > 145 else "bearish_crypto",
            "strength":"modéré",
        })

    return {
        "correlations": correlations,
        "dxy":          round(dxy_approx, 2),
        "market_mood":  _interpret_forex_mood(dxy_approx),
        "ts":           datetime.now().strftime("%H:%M:%S"),
    }


def _calc_dxy_approx(rates: dict) -> float:
    """
    Approximation du Dollar Index (DXY) basé sur les 6 paires du panier officiel.
    Poids officiels : EUR 57.6%, JPY 13.6%, GBP 11.9%, CAD 9.1%, SEK 4.2%, CHF 3.6%
    """
    try:
        eur = rates.get("EUR", 0)
        jpy = rates.get("JPY", 0)
        gbp = rates.get("GBP", 0)
        cad = rates.get("CAD", 0)
        sek = rates.get("SEK", 0)
        chf = rates.get("CHF", 0)
        if not all([eur, jpy, gbp, cad]):
            return 100.0
        # DXY = USD force relative (inverse des taux en USD)
        eurusd = 1/eur if eur else 1
        usdjpy = jpy
        gbpusd = 1/gbp if gbp else 1
        usdcad = cad
        usdsek = sek if sek else 10
        usdchf = chf if chf else 0.9

        dxy = (100.0 * (eurusd ** -0.576) * (usdjpy ** 0.136) *
               (gbpusd ** -0.119) * (usdcad ** 0.091) *
               (usdsek ** 0.042) * (usdchf ** 0.036))
        return round(dxy, 2)
    except Exception:
        return 100.0


def _interpret_forex_mood(dxy: float) -> str:
    if dxy > 107:   return "💪 Dollar très fort — Risk-OFF — Défavorable aux cryptos"
    elif dxy > 104: return "📈 Dollar fort — Légère pression sur les cryptos"
    elif dxy > 100: return "⚪ Dollar neutre — Marché équilibré"
    elif dxy > 97:  return "📉 Dollar faible — Risk-ON — Favorable aux cryptos"
    else:           return "💫 Dollar très faible — Fort Risk-ON — Très favorable"


# ══════════════════════════════════════════════════════════════
# 5. INDICATEURS TECHNIQUES (réutilisables)
# ══════════════════════════════════════════════════════════════

def _calc_rsi(closes: list, period: int = 14) -> Optional[float]:
    if len(closes) < period + 2: return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0)); losses.append(max(-d, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0: return 100.0
    return round(100 - (100 / (1 + ag/al)), 2)


def _calc_ema(values: list, period: int) -> Optional[float]:
    if len(values) < period: return None
    k   = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = v * k + ema * (1 - k)
    return ema


def _calc_bollinger(closes: list, period: int = 20):
    if len(closes) < period: return None, None, None
    w   = closes[-period:]
    avg = sum(w) / period
    std = (sum((x - avg) ** 2 for x in w) / period) ** 0.5
    return avg - 2*std, avg, avg + 2*std


def _calc_atr(candles: list, period: int = 14) -> Optional[float]:
    if len(candles) < period + 1: return None
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]["h"], candles[i]["l"], candles[i-1]["c"]
        trs.append(max(h-l, abs(h-pc), abs(l-pc)))
    return sum(trs[-period:]) / period


# ══════════════════════════════════════════════════════════════
# 6. SCAN COMPLET (utilisé par app.py)
# ══════════════════════════════════════════════════════════════

def forex_full_scan() -> dict:
    """
    Scan complet du marché Forex.
    Retourne tout ce dont l'interface a besoin.
    """
    pairs   = fetch_all_pairs()
    sessions = get_session_overview()
    correl  = get_crypto_forex_correlations()

    # Ajouter signaux techniques aux paires majeures
    for p in pairs:
        if p["category"] in ("major", "cross"):
            try:
                signal = analyze_forex_pair(p["pair"])
                if signal:
                    p["signal"]    = signal["direction"]
                    p["score"]     = signal["score"]
                    p["rsi"]       = signal["rsi"]
                    p["support"]   = signal["support"]
                    p["resistance"]= signal["resistance"]
            except Exception:
                pass

    # Stats rapides
    movers_up   = sorted([p for p in pairs if p["change_pct"] > 0],
                          key=lambda x: x["change_pct"], reverse=True)[:5]
    movers_down = sorted([p for p in pairs if p["change_pct"] < 0],
                          key=lambda x: x["change_pct"])[:5]

    return {
        "pairs":         pairs,
        "sessions":      sessions,
        "correlations":  correl,
        "movers_up":     movers_up,
        "movers_down":   movers_down,
        "pair_count":    len(pairs),
        "active_pairs":  sum(1 for p in pairs if p.get("is_active")),
        "ts":            datetime.now().strftime("%H:%M:%S"),
    }


def init_forex_db():
    """Crée les tables Forex si elles n'existent pas."""
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS forex_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT NOT NULL,
            rate REAL NOT NULL,
            change_pct REAL DEFAULT 0,
            change_pip REAL DEFAULT 0,
            ts TEXT NOT NULL,
            source TEXT DEFAULT 'frankfurter'
        );
        CREATE TABLE IF NOT EXISTS forex_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 0,
            pair TEXT NOT NULL,
            condition TEXT NOT NULL,
            target_rate REAL NOT NULL,
            active INTEGER DEFAULT 1,
            triggered INTEGER DEFAULT 0,
            created TEXT
        );
    """)
    conn.commit(); conn.close()
