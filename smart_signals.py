#!/usr/bin/env python3
"""
CryptoScanner Pro V10 — Smart Signal Engine
Détection intelligente basée sur :
- Confirmation multi-critères (prix + volume + RSI + structure)
- Patterns de bougies japonaises (engulfing, doji, hammer...)
- Divergences RSI/Prix
- Breakouts avec volume confirmé
- Filtre anti-bruit (ignore les micro-mouvements)
"""

from __future__ import annotations

import requests
from datetime import datetime

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"

# ── Seuils intelligents ───────────────────────────────────────
PUMP_PRICE_PCT    = 4.0    # +4% minimum (was 3%)
DUMP_PRICE_PCT    = -4.0   # -4% minimum (was -3%)
VOLUME_MULT_MIN   = 5.0    # ×5 le volume moyen (was ×4)
RSI_OVERSOLD      = 30     # RSI survente (was 32)
RSI_OVERBOUGHT    = 70     # RSI surachat (was 68)
MIN_VOLUME_USD    = 5_000_000  # Volume minimum $5M pour signaux standard
MIN_VOLUME_SMALL  = 500_000   # Volume minimum $500K pour suivi RSI small caps

# ── Historique RSI pour détecter les crossings ───────────────
# {symbol: [rsi_t-2, rsi_t-1]} — rolling 2 dernières valeurs
_rsi_history: dict = {}

# ── Indicateurs ───────────────────────────────────────────────
def calc_rsi(closes, period=14):
    if len(closes) < period+2: return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d,0)); losses.append(max(-d,0))
    ag = sum(gains[-period:])/period
    al = sum(losses[-period:])/period
    if al == 0: return 100.0
    return round(100-(100/(1+ag/al)), 2)

def calc_ema(values, period):
    if len(values) < period: return None
    k = 2/(period+1); ema = sum(values[:period])/period
    for v in values[period:]: ema = v*k + ema*(1-k)
    return ema

def calc_atr(candles, period=14):
    """Average True Range — mesure la volatilité"""
    if len(candles) < period+1: return None
    trs = []
    for i in range(1, len(candles)):
        high = candles[i]["h"]; low = candles[i]["l"]; prev_close = candles[i-1]["c"]
        tr = max(high-low, abs(high-prev_close), abs(low-prev_close))
        trs.append(tr)
    return sum(trs[-period:]) / period

def calc_avg_volume(candles, period=20):
    if len(candles) < period: return None
    return sum(c["v"] for c in candles[-period:]) / period

def calc_bollinger(closes, period=20):
    if len(closes) < period: return None, None, None
    w = closes[-period:]
    avg = sum(w)/period
    std = (sum((x-avg)**2 for x in w)/period)**0.5
    return avg-2*std, avg, avg+2*std

# ── Patterns de bougies ───────────────────────────────────────
def detect_candle_patterns(candles):
    """Détecte les patterns de retournement sur les dernières bougies"""
    if len(candles) < 3: return []
    patterns = []

    c  = candles[-1]   # Bougie actuelle
    p  = candles[-2]   # Bougie précédente
    pp = candles[-3]   # Avant-dernière

    body_c  = abs(c["c"] - c["o"])
    body_p  = abs(p["c"] - p["o"])
    range_c = c["h"] - c["l"]
    range_p = p["h"] - p["l"]

    is_bull_c = c["c"] > c["o"]
    is_bull_p = p["c"] > p["o"]

    # ── ENGULFING HAUSSIER ─────────────────────────────────────
    # Grosse bougie verte qui englobe entièrement la rouge précédente
    if (is_bull_c and not is_bull_p and
        c["o"] <= p["c"] and c["c"] >= p["o"] and
        body_c > body_p * 1.2):
        patterns.append({
            "name": "🕯️ Engulfing Haussier",
            "type": "bullish",
            "strength": 85,
            "desc": "Bougie haussière englobante — retournement probable"
        })

    # ── ENGULFING BAISSIER ─────────────────────────────────────
    if (not is_bull_c and is_bull_p and
        c["o"] >= p["c"] and c["c"] <= p["o"] and
        body_c > body_p * 1.2):
        patterns.append({
            "name": "🕯️ Engulfing Baissier",
            "type": "bearish",
            "strength": 85,
            "desc": "Bougie baissière englobante — retournement probable"
        })

    # ── MARTEAU (Hammer) ───────────────────────────────────────
    # Petite bougie avec longue mèche basse (fond de tendance)
    if range_c > 0:
        lower_wick = min(c["o"], c["c"]) - c["l"]
        upper_wick = c["h"] - max(c["o"], c["c"])
        if (lower_wick > body_c * 2 and
            upper_wick < body_c * 0.3 and
            body_c < range_c * 0.35):
            patterns.append({
                "name": "🔨 Marteau",
                "type": "bullish",
                "strength": 75,
                "desc": "Longue mèche basse — pression acheteuse en fond"
            })

    # ── ÉTOILE FILANTE (Shooting Star) ────────────────────────
    if range_c > 0:
        upper_wick = c["h"] - max(c["o"], c["c"])
        lower_wick = min(c["o"], c["c"]) - c["l"]
        if (upper_wick > body_c * 2 and
            lower_wick < body_c * 0.3 and
            body_c < range_c * 0.35):
            patterns.append({
                "name": "⭐ Étoile Filante",
                "type": "bearish",
                "strength": 75,
                "desc": "Longue mèche haute — pression vendeuse en sommet"
            })

    # ── DOJI ───────────────────────────────────────────────────
    if range_c > 0 and body_c < range_c * 0.08:
        patterns.append({
            "name": "✙ Doji",
            "type": "neutral",
            "strength": 60,
            "desc": "Indécision du marché — attendre confirmation"
        })

    # ── MORNING STAR (3 bougies) ───────────────────────────────
    body_pp = abs(pp["c"] - pp["o"])
    if (not (pp["c"] > pp["o"]) and  # Grosse bougie rouge
        body_p < body_pp * 0.4 and   # Petite bougie indécise
        is_bull_c and                  # Grosse bougie verte
        body_c > body_pp * 0.5 and
        c["c"] > (pp["o"] + pp["c"]) / 2):
        patterns.append({
            "name": "🌅 Morning Star",
            "type": "bullish",
            "strength": 90,
            "desc": "Pattern 3 bougies — fort signal de retournement haussier"
        })

    # ── EVENING STAR (3 bougies) ───────────────────────────────
    if (pp["c"] > pp["o"] and          # Grosse bougie verte
        body_p < body_pp * 0.4 and    # Petite bougie indécise
        not is_bull_c and              # Grosse bougie rouge
        body_c > body_pp * 0.5 and
        c["c"] < (pp["o"] + pp["c"]) / 2):
        patterns.append({
            "name": "🌆 Evening Star",
            "type": "bearish",
            "strength": 90,
            "desc": "Pattern 3 bougies — fort signal de retournement baissier"
        })

    return patterns

def detect_divergence(closes, rsi_values):
    """Détecte les divergences RSI/Prix"""
    if len(closes) < 10 or len(rsi_values) < 10: return None

    # Comparer les 5 dernières vs les 5 précédentes
    price_recent = closes[-5:]
    price_older  = closes[-10:-5]
    rsi_recent   = rsi_values[-5:]
    rsi_older    = rsi_values[-10:-5]

    if not all([price_recent, price_older, rsi_recent, rsi_older]): return None

    price_trend = sum(price_recent)/len(price_recent) - sum(price_older)/len(price_older)
    rsi_trend   = sum(rsi_recent)/len(rsi_recent) - sum(rsi_older)/len(rsi_older)

    # Divergence haussière : prix baisse mais RSI monte
    if price_trend < -0.5 and rsi_trend > 2:
        return {
            "type": "bullish",
            "name": "📊 Divergence RSI Haussière",
            "strength": 80,
            "desc": "Prix en baisse mais RSI remonte — renversement potentiel"
        }
    # Divergence baissière : prix monte mais RSI baisse
    if price_trend > 0.5 and rsi_trend < -2:
        return {
            "type": "bearish",
            "name": "📊 Divergence RSI Baissière",
            "strength": 80,
            "desc": "Prix en hausse mais RSI baisse — essoufflement probable"
        }
    return None

def detect_breakout(candles, closes):
    """Détecte les cassures de résistance/support avec volume"""
    if len(candles) < 20: return None

    # Résistance = plus haut des 20 dernières bougies (sauf la dernière)
    resistance = max(c["h"] for c in candles[-21:-1])
    support    = min(c["l"] for c in candles[-21:-1])
    current    = closes[-1]
    avg_vol    = calc_avg_volume(candles[:-1], 20)
    last_vol   = candles[-1]["v"]

    if avg_vol and avg_vol > 0:
        vol_ratio = last_vol / avg_vol
        # Breakout haussier : cassure résistance + volume confirmé
        if current > resistance * 1.005 and vol_ratio > 2:
            return {
                "type": "bullish",
                "name": "🚀 Breakout Résistance",
                "strength": min(95, 70 + int(vol_ratio * 5)),
                "desc": f"Cassure résistance ${resistance:.4f} avec volume ×{vol_ratio:.1f}",
                "level": resistance,
                "vol_ratio": vol_ratio
            }
        # Breakdown : cassure support + volume
        if current < support * 0.995 and vol_ratio > 2:
            return {
                "type": "bearish",
                "name": "💥 Breakdown Support",
                "strength": min(95, 70 + int(vol_ratio * 5)),
                "desc": f"Cassure support ${support:.4f} avec volume ×{vol_ratio:.1f}",
                "level": support,
                "vol_ratio": vol_ratio
            }
    return None

# ── Analyse complète d'un coin ────────────────────────────────
def analyze_coin_smart(symbol, candles_15m, candles_1h=None):
    """
    Analyse complète multi-timeframe avec confirmation.
    Retourne un signal seulement si plusieurs critères sont alignés.
    """
    if len(candles_15m) < 25:
        return None

    closes_15m = [c["c"] for c in candles_15m]
    volumes    = [c["v"] for c in candles_15m]

    # Indicateurs de base
    rsi        = calc_rsi(closes_15m)
    avg_vol    = calc_avg_volume(candles_15m, 20)
    last_vol   = volumes[-1]
    last_price = closes_15m[-1]
    prev_price = closes_15m[-4]  # 1h avant (4 × 15min)
    atr        = calc_atr(candles_15m)
    bb_low, bb_mid, bb_high = calc_bollinger(closes_15m)
    ma20       = calc_ema(closes_15m, 20)

    if avg_vol is None or avg_vol == 0: return None

    vol_ratio   = last_vol / avg_vol
    price_chg   = (last_price - prev_price) / prev_price * 100
    volume_usd  = last_vol * last_price

    # Filtre minimum — ignorer les coins sans volume
    if volume_usd < MIN_VOLUME_USD: return None

    # ADR approximation : range max/min sur les 96 dernières bougies 15m (≈24h)
    last_96 = candles_15m[-96:] if len(candles_15m) >= 96 else candles_15m
    adr_high = max(c["h"] for c in last_96)
    adr_low  = min(c["l"] for c in last_96)
    adr_pct  = (adr_high - adr_low) / last_price * 100 if last_price > 0 else 0

    signals = []
    score   = 0

    # ── 1. Variation de prix significative ────────────────────
    # Filtre ADR : le move doit représenter ≥25% du range journalier (signal réel vs bruit)
    adr_threshold = adr_pct * 0.25 if adr_pct > 0 else PUMP_PRICE_PCT
    pump_min = max(PUMP_PRICE_PCT, adr_threshold)
    dump_min = min(DUMP_PRICE_PCT, -adr_threshold)

    if price_chg >= pump_min:
        signals.append({"label":"🚀 PUMP +{:.1f}%".format(price_chg), "type":"green", "weight":30})
        score += 30
    elif price_chg <= dump_min:
        signals.append({"label":"💥 DUMP {:.1f}%".format(price_chg), "type":"red", "weight":30})
        score += 30

    # ── 2. Volume spike ───────────────────────────────────────
    if vol_ratio >= VOLUME_MULT_MIN:
        signals.append({"label":f"⚡ VOL ×{vol_ratio:.1f}", "type":"yellow", "weight":25})
        score += 25
    elif vol_ratio >= 2.5:
        signals.append({"label":f"📊 VOL ×{vol_ratio:.1f}", "type":"yellow", "weight":10})
        score += 10

    # ── 3. RSI ────────────────────────────────────────────────
    if rsi is not None:
        if rsi <= RSI_OVERSOLD:
            signals.append({"label":f"🟢 RSI {rsi:.0f} SURVENTE", "type":"green", "weight":20})
            score += 20
        elif rsi >= RSI_OVERBOUGHT:
            signals.append({"label":f"🔴 RSI {rsi:.0f} SURACHAT", "type":"red", "weight":20})
            score += 20
        elif rsi <= 40:
            signals.append({"label":f"📉 RSI {rsi:.0f}", "type":"yellow", "weight":5})
            score += 5

    # ── 4. Bollinger Bands ────────────────────────────────────
    if bb_low and bb_high:
        if last_price <= bb_low:
            signals.append({"label":"📏 Sous BB inf", "type":"green", "weight":15})
            score += 15
        elif last_price >= bb_high:
            signals.append({"label":"📏 Sur BB sup", "type":"red", "weight":15})
            score += 15

    # ── 5. Patterns de bougies ────────────────────────────────
    patterns = detect_candle_patterns(candles_15m[-5:])
    for p in patterns:
        signals.append({"label": p["name"], "type": p["type"] if p["type"]!="neutral" else "yellow",
                        "weight": p["strength"]//5})
        score += p["strength"] // 5

    # ── 6. Breakout ───────────────────────────────────────────
    breakout = detect_breakout(candles_15m, closes_15m)
    if breakout:
        signals.append({"label": breakout["name"], "type": "green" if breakout["type"]=="bullish" else "red",
                        "weight": breakout["strength"]//5})
        score += breakout["strength"] // 5

    # ── 7. Divergence RSI ─────────────────────────────────────
    rsi_series = []
    for i in range(15, len(closes_15m)+1):
        r = calc_rsi(closes_15m[:i])
        if r: rsi_series.append(r)

    div = detect_divergence(closes_15m, rsi_series)
    if div:
        signals.append({"label": div["name"], "type": "green" if div["type"]=="bullish" else "red",
                        "weight": div["strength"]//5})
        score += div["strength"] // 5

    # ── Score minimum pour être un vrai signal ─────────────────
    # Nécessite au moins 2 critères alignés
    if score < 55 or len(signals) < 3:  # Score min 55, 3 critères minimum
        return None

    # Direction globale
    green_w = sum(s["weight"] for s in signals if s["type"]=="green")
    red_w   = sum(s["weight"] for s in signals if s["type"]=="red")
    direction = "buy" if green_w > red_w else "sell" if red_w > green_w else "neutral"

    # Contexte MA20 : position du prix par rapport à la moyenne mobile
    ma20_ctx = None
    if ma20:
        ma20_diff = (last_price - ma20) / ma20 * 100
        ma20_ctx  = {"value": round(ma20, 6), "diff_pct": round(ma20_diff, 2),
                     "above": last_price > ma20}

    return {
        "symbol":      symbol,
        "price":       last_price,
        "change_pct":  round(price_chg, 2),
        "volume_usdt": volume_usd,
        "vol_ratio":   round(vol_ratio, 2),
        "rsi":         rsi,
        "score":       min(100, score),
        "direction":   direction,
        "tags":        signals,
        "patterns":    patterns,
        "breakout":    breakout,
        "divergence":  div,
        "bb_pos":      round((last_price - bb_low) / (bb_high - bb_low) * 100, 1) if bb_low and bb_high and (bb_high-bb_low)>0 else None,
        "ma20":        ma20_ctx,
        "adr_pct":     round(adr_pct, 2),
    }

def build_telegram_alert(signal, for_role: str = "free"):
    """Construit un message Telegram riche et informatif"""
    sym   = signal["symbol"]
    price = signal["price"]
    chg   = signal["change_pct"]
    score = signal["score"]
    dir_  = signal["direction"]
    rsi   = signal["rsi"]
    vol_r = signal["vol_ratio"]

    # Emoji principal selon direction et score
    if dir_ == "buy":
        main_emoji = "🟢" if score >= 70 else "📈"
        dir_label  = "SIGNAL HAUSSIER"
    elif dir_ == "sell":
        main_emoji = "🔴" if score >= 70 else "📉"
        dir_label  = "SIGNAL BAISSIER"
    else:
        main_emoji = "⚪"
        dir_label  = "SIGNAL NEUTRE"

    sign = "+" if chg > 0 else ""
    lines = [
        f"{main_emoji} <b>{dir_label} — {sym}/USDT</b>",
        f"",
        f"💰 Prix: <b>${price:.4f}</b>",
        f"📊 Variation: <b>{sign}{chg:.2f}%</b>",
        f"⚡ Volume: <b>×{vol_r:.1f}</b> la moyenne",
    ]
    if rsi:
        rsi_label = "🟢 SURVENTE" if rsi < 32 else "🔴 SURACHAT" if rsi > 68 else "⚪"
        lines.append(f"📈 RSI: <b>{rsi:.1f}</b> {rsi_label}")

    # Score de confiance
    score_bar = "█" * (score//10) + "░" * (10-score//10)
    lines.append(f"")
    lines.append(f"🎯 Confiance: <b>{score}/100</b>")
    lines.append(f"<code>{score_bar}</code>")

    if for_role == "free":
        lines.append(f"")
        lines.append(f"WARNING: Educational data only. Not investment advice.")
        from datetime import datetime
        lines.append(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        return "\n".join(lines)


    # Signaux détectés
    if signal.get("tags"):
        lines.append(f"")
        lines.append(f"<b>Signaux confirmés :</b>")
        for tag in signal["tags"][:4]:
            lines.append(f"  • {tag['label']}")

    # Pattern de bougie
    if signal.get("patterns"):
        p = signal["patterns"][0]
        lines.append(f"")
        lines.append(f"🕯️ Pattern: <b>{p['name']}</b>")
        lines.append(f"   {p['desc']}")

    # Breakout
    if signal.get("breakout"):
        b = signal["breakout"]
        lines.append(f"")
        lines.append(f"💥 {b['name']}")
        lines.append(f"   {b['desc']}")

    # Divergence
    if signal.get("divergence"):
        d = signal["divergence"]
        lines.append(f"")
        lines.append(f"🔀 {d['name']}")
        lines.append(f"   {d['desc']}")

    # MA20 contexte
    if signal.get("ma20"):
        m = signal["ma20"]
        pos = "AU-DESSUS ↑" if m["above"] else "EN-DESSOUS ↓"
        lines.append(f"")
        lines.append(f"📏 MA20: <b>{pos}</b> ({m['diff_pct']:+.1f}%)")

    # ADR info
    if signal.get("adr_pct"):
        lines.append(f"📐 ADR 24h: <b>{signal['adr_pct']:.1f}%</b>")

    lines.append(f"")
    lines.append(f"🚫 <i>Ceci ne constitue pas un conseil d'achat ou de vente. CryptoScanner Pro fournit uniquement des données techniques à titre informatif.</i>")
    lines.append(f"🕐 {datetime.now().strftime('%H:%M:%S')}")

    return "\n".join(lines)


# ── Détection de retournement RSI (crossing zones) ───────────

def update_rsi_history(symbol: str, rsi_value: float):
    """Mémorise les 2 dernières valeurs RSI d'un symbol pour détecter les crossings."""
    if symbol not in _rsi_history:
        _rsi_history[symbol] = []
    _rsi_history[symbol].append(round(rsi_value, 2))
    if len(_rsi_history[symbol]) > 3:
        _rsi_history[symbol].pop(0)


def check_rsi_exit(symbol: str, current_rsi: float, rsi_oversold: int = None, rsi_overbought: int = None) -> dict | None:
    """
    Detect RSI exit from extreme zones (overbought/oversold) using admin settings.

    - Exit overbought: RSI was >= rsi_overbought (default 70), now < threshold → bearish retrace signal
    - Exit oversold: RSI was <= rsi_oversold (default 30), now > threshold → bullish rebound signal

    Args:
        symbol: Trading symbol
        current_rsi: Current RSI value
        rsi_oversold: Admin setting for oversold threshold (loads from DB if None)
        rsi_overbought: Admin setting for overbought threshold (loads from DB if None)

    Returns:
        Dict with signal info (direction, name, rsi values, action) or None if no exit detected
    """
    # Load admin settings if not provided (for backward compatibility)
    if rsi_oversold is None or rsi_overbought is None:
        from scanner_engine import load_admin_alert_settings
        settings = load_admin_alert_settings()
        if rsi_oversold is None:
            rsi_oversold = settings.get("rsi_oversold", RSI_OVERSOLD)
        if rsi_overbought is None:
            rsi_overbought = settings.get("rsi_overbought", RSI_OVERBOUGHT)

    hist = _rsi_history.get(symbol, [])
    if len(hist) < 1:
        return None
    prev_rsi = hist[-1]

    # Exit overbought zone (prudence signal / potential retrace)
    if prev_rsi >= rsi_overbought and current_rsi < rsi_overbought:
        return {
            "direction": "bearish",
            "name":      "⚠️ Sortie Zone Surachat",
            "rsi_prev":  prev_rsi,
            "rsi_now":   round(current_rsi, 1),
            "desc":      f"RSI {prev_rsi} → {current_rsi:.1f} (quitte la zone > {rsi_overbought})",
            "action":    "Prudence — retrace possible · envisager sortie partielle"
        }

    # Exit oversold zone (potential rebound signal)
    if prev_rsi <= rsi_oversold and current_rsi > rsi_oversold:
        return {
            "direction": "bullish",
            "name":      "🔔 Sortie Zone Survente",
            "rsi_prev":  prev_rsi,
            "rsi_now":   round(current_rsi, 1),
            "desc":      f"RSI {prev_rsi} → {current_rsi:.1f} (repasse au-dessus de {rsi_oversold})",
            "action":    "Rebond potentiel — surveiller confirmation volume"
        }

    return None


def build_retrace_alert(symbol: str, rsi_exit: dict, price: float,
                        change_pct: float, volume_usd: float = 0,
                        for_role: str = "free", candles_15m=None) -> str:
    """
    Construit un message Telegram dédié aux signaux de retournement RSI.
    Format différent des Smart Signals : focus sur le point de sortie/prudence.
    """
    is_bear = rsi_exit["direction"] == "bearish"
    header  = "⚠️ RETRACE PROBABLE" if is_bear else "🔔 REBOND POSSIBLE"
    emoji   = "📉" if is_bear else "📈"
    sign    = "+" if change_pct > 0 else ""
    vol_str = f"${volume_usd/1e6:.1f}M" if volume_usd >= 1e6 else f"${volume_usd/1e3:.0f}K" if volume_usd >= 1e3 else "—"

    lines = [
        f"{header} — <b>{symbol}/USDT</b>",
        f"",
        f"📊 RSI sort de la zone {'<b>surachat 🔴</b>' if is_bear else '<b>survente 🟢</b>'}",
        f"   Était: <b>{rsi_exit['rsi_prev']}</b>  →  Maintenant: <b>{rsi_exit['rsi_now']}</b>",
        f"",
        f"💰 Prix: <b>${price:.4f}</b>",
        f"{emoji} Variation récente: <b>{sign}{change_pct:.2f}%</b>",
    ]
    if volume_usd:
        lines.append(f"📦 Volume 24H: <b>{vol_str}</b>")
    lines += [
        f"",
        f"🎯 <b>{rsi_exit['action']}</b>",
        f"",
        f"🚫 <i>Ceci ne constitue pas un conseil d'achat ou de vente. CryptoScanner Pro fournit uniquement des données techniques à titre informatif.</i>",
        f"🕐 {datetime.now().strftime('%H:%M:%S')}",
    ]
    return "\n".join(lines)
