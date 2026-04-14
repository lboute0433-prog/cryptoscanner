#!/usr/bin/env python3
"""
CryptoScanner Pro V11 — Backtest Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5 stratégies de trading automatique :
  1. RSI Reversal    — Achat survente / Vente surachat
  2. EMA Crossover   — Croisement EMA rapide/lente
  3. Bollinger Bands — Rebond sur bandes
  4. MACD            — Croisement signal/MACD
  5. Smart Signal    — Algo multi-critères CryptoScanner

Modes :
  - Backtest historique (données Binance)
  - Simulation temps réel (paper trading)
  - Comparaison multi-stratégies

Métriques :
  - PnL total, Win rate, Sharpe Ratio
  - Max Drawdown, Profit Factor
  - Courbe equity, liste des trades
"""

import requests, sqlite3, time, math
from datetime import datetime, timedelta
from typing import Optional
from config import DATABASE_PATH as DB_PATH
from db import get_connection

BINANCE_KLINES = "https://api.binance.com/api/v3/klines"

# ── Intervalles Binance ───────────────────────────────────────
INTERVALS = {
    "15m": {"binance": "15m",  "ms": 900_000,    "label": "15 minutes"},
    "1h":  {"binance": "1h",   "ms": 3_600_000,  "label": "1 heure"},
    "4h":  {"binance": "4h",   "ms": 14_400_000, "label": "4 heures"},
    "1d":  {"binance": "1d",   "ms": 86_400_000, "label": "1 jour"},
}

# ── Indicateurs ───────────────────────────────────────────────
def calc_rsi(closes, period=14):
    if len(closes) < period + 2: return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0)); losses.append(max(-d, 0))
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    if al == 0: return 100.0
    return round(100 - (100 / (1 + ag/al)), 2)

def calc_ema(values, period):
    if len(values) < period: return None
    k = 2 / (period + 1)
    ema = sum(values[:period]) / period
    for v in values[period:]:
        ema = v * k + ema * (1 - k)
    return ema

def calc_macd(closes, fast=12, slow=26, signal=9):
    if len(closes) < slow + signal: return None, None
    ema_fast = calc_ema(closes, fast)
    ema_slow = calc_ema(closes, slow)
    if ema_fast is None or ema_slow is None: return None, None
    macd_line = ema_fast - ema_slow
    # Signal line : EMA du MACD sur les dernières bougies
    macd_series = []
    for i in range(slow, len(closes) + 1):
        ef = calc_ema(closes[:i], fast)
        es = calc_ema(closes[:i], slow)
        if ef and es:
            macd_series.append(ef - es)
    signal_line = calc_ema(macd_series, signal) if len(macd_series) >= signal else None
    return round(macd_line, 6), round(signal_line, 6) if signal_line else None

def calc_bollinger(closes, period=20, std_mult=2.0):
    if len(closes) < period: return None, None, None
    w   = closes[-period:]
    avg = sum(w) / period
    std = math.sqrt(sum((x - avg) ** 2 for x in w) / period)
    return round(avg - std_mult * std, 6), round(avg, 6), round(avg + std_mult * std, 6)

def calc_atr(candles, period=14):
    if len(candles) < period + 1: return None
    trs = []
    for i in range(1, len(candles)):
        h, l, pc = candles[i]["h"], candles[i]["l"], candles[i-1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-period:]) / period

def calc_sharpe(returns, risk_free=0.0):
    if len(returns) < 2: return 0.0
    avg = sum(returns) / len(returns)
    std = math.sqrt(sum((r - avg)**2 for r in returns) / len(returns))
    return round((avg - risk_free) / std * math.sqrt(365), 2) if std > 0 else 0.0

def calc_max_drawdown(equity_curve):
    if len(equity_curve) < 2: return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak: peak = val
        dd = (peak - val) / peak * 100
        if dd > max_dd: max_dd = dd
    return round(max_dd, 2)

# ── Fetch bougies historiques ─────────────────────────────────
def fetch_historical_candles(symbol: str, interval: str, limit: int = 500) -> list:
    """Récupère les bougies depuis Binance."""
    try:
        iv = INTERVALS.get(interval, {}).get("binance", interval)
        r  = requests.get(
            BINANCE_KLINES,
            params={"symbol": symbol.upper() + "USDT", "interval": iv, "limit": min(limit, 1000)},
            timeout=12
        )
        data = r.json()
        if not isinstance(data, list): return []
        return [{
            "t": int(k[0]),
            "o": float(k[1]),
            "h": float(k[2]),
            "l": float(k[3]),
            "c": float(k[4]),
            "v": float(k[5]),
            "ts": datetime.fromtimestamp(int(k[0])/1000).strftime("%Y-%m-%d %H:%M"),
        } for k in data]
    except Exception as e:
        print(f"[Backtest] fetch_historical_candles error: {e}")
        return []

# ══════════════════════════════════════════════════════════════
# STRATÉGIES
# ══════════════════════════════════════════════════════════════

def strategy_rsi_reversal(candles: list, params: dict) -> Optional[str]:
    """
    RSI Reversal : achète en survente, vend en surachat.
    Params : rsi_buy (défaut 30), rsi_sell (défaut 70), period (défaut 14)
    """
    if len(candles) < 20: return None
    closes = [c["c"] for c in candles]
    rsi    = calc_rsi(closes, params.get("period", 14))
    if rsi is None: return None
    if rsi <= params.get("rsi_buy", 30):  return "buy"
    if rsi >= params.get("rsi_sell", 70): return "sell"
    return None

def strategy_ema_crossover(candles: list, params: dict) -> Optional[str]:
    """
    EMA Crossover : signal au croisement EMA rapide/lente.
    Params : ema_fast (défaut 9), ema_slow (défaut 21)
    """
    if len(candles) < 30: return None
    closes    = [c["c"] for c in candles]
    fast      = params.get("ema_fast", 9)
    slow      = params.get("ema_slow", 21)
    ema_f_now = calc_ema(closes, fast)
    ema_s_now = calc_ema(closes, slow)
    ema_f_prev= calc_ema(closes[:-1], fast)
    ema_s_prev= calc_ema(closes[:-1], slow)
    if None in (ema_f_now, ema_s_now, ema_f_prev, ema_s_prev): return None
    # Croisement haussier
    if ema_f_prev <= ema_s_prev and ema_f_now > ema_s_now: return "buy"
    # Croisement baissier
    if ema_f_prev >= ema_s_prev and ema_f_now < ema_s_now: return "sell"
    return None

def strategy_bollinger(candles: list, params: dict) -> Optional[str]:
    """
    Bollinger Bands : achat sous BB basse, vente sur BB haute.
    Params : period (défaut 20), std (défaut 2.0)
    """
    if len(candles) < 25: return None
    closes = [c["c"] for c in candles]
    bb_low, bb_mid, bb_high = calc_bollinger(closes,
        params.get("period", 20), params.get("std", 2.0))
    if bb_low is None: return None
    price = closes[-1]
    if price <= bb_low:  return "buy"
    if price >= bb_high: return "sell"
    return None

def strategy_macd(candles: list, params: dict) -> Optional[str]:
    """
    MACD : achat quand MACD croise au-dessus du signal, vente en-dessous.
    Params : fast (12), slow (26), signal (9)
    """
    if len(candles) < 40: return None
    closes = [c["c"] for c in candles]
    fast   = params.get("fast", 12)
    slow   = params.get("slow", 26)
    sig    = params.get("signal", 9)
    macd_now,  sig_now  = calc_macd(closes, fast, slow, sig)
    macd_prev, sig_prev = calc_macd(closes[:-1], fast, slow, sig)
    if None in (macd_now, sig_now, macd_prev, sig_prev): return None
    if macd_prev <= sig_prev and macd_now > sig_now: return "buy"
    if macd_prev >= sig_prev and macd_now < sig_now: return "sell"
    return None

def strategy_smart(candles: list, params: dict) -> Optional[str]:
    """
    Smart Signal : algo multi-critères CryptoScanner.
    Combine RSI + Bollinger + Volume + EMA.
    """
    if len(candles) < 30: return None
    closes  = [c["c"] for c in candles]
    volumes = [c["v"] for c in candles]
    price   = closes[-1]
    rsi     = calc_rsi(closes, 14)
    ema20   = calc_ema(closes, 20)
    ema50   = calc_ema(closes, 50) if len(closes) >= 50 else None
    bb_low, bb_mid, bb_high = calc_bollinger(closes, 20)
    avg_vol = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else None
    vol_ratio = volumes[-1] / avg_vol if avg_vol and avg_vol > 0 else 1

    buy_score = sell_score = 0

    if rsi is not None:
        if rsi < 30:  buy_score += 3
        elif rsi < 40: buy_score += 1
        if rsi > 70:  sell_score += 3
        elif rsi > 60: sell_score += 1

    if bb_low and bb_high:
        if price <= bb_low:  buy_score += 2
        if price >= bb_high: sell_score += 2

    if ema20 and ema50:
        if ema20 > ema50: buy_score += 1
        else:             sell_score += 1

    if vol_ratio > 2: buy_score += 1 if buy_score > sell_score else 0

    min_score = params.get("min_score", 4)
    if buy_score >= min_score and buy_score > sell_score:  return "buy"
    if sell_score >= min_score and sell_score > buy_score: return "sell"
    return None

STRATEGIES = {
    "rsi_reversal":  {"fn": strategy_rsi_reversal,  "name": "RSI Reversal",    "emoji": "📊",
                      "desc": "Achat RSI < 30, Vente RSI > 70",
                      "params": {"rsi_buy": 30, "rsi_sell": 70, "period": 14}},
    "ema_crossover": {"fn": strategy_ema_crossover, "name": "EMA Crossover",   "emoji": "📈",
                      "desc": "Croisement EMA 9 / EMA 21",
                      "params": {"ema_fast": 9, "ema_slow": 21}},
    "bollinger":     {"fn": strategy_bollinger,     "name": "Bollinger Bands", "emoji": "📏",
                      "desc": "Rebond sur bandes de Bollinger",
                      "params": {"period": 20, "std": 2.0}},
    "macd":          {"fn": strategy_macd,          "name": "MACD Signal",     "emoji": "🔀",
                      "desc": "Croisement MACD / Signal (12/26/9)",
                      "params": {"fast": 12, "slow": 26, "signal": 9}},
    "smart":         {"fn": strategy_smart,         "name": "Smart Signal",    "emoji": "🧠",
                      "desc": "Multi-critères RSI + BB + EMA + Volume",
                      "params": {"min_score": 4}},
}

# ══════════════════════════════════════════════════════════════
# MOTEUR DE BACKTEST
# ══════════════════════════════════════════════════════════════

def run_backtest(symbol: str, strategy_id: str, interval: str = "1h",
                 capital: float = 1000.0, params: dict = None,
                 stop_loss_pct: float = 3.0, take_profit_pct: float = 6.0,
                 candles_limit: int = 500) -> dict:
    """
    Lance un backtest complet.

    Args:
        symbol          : ex "BTC", "ETH", "SOL"
        strategy_id     : "rsi_reversal", "ema_crossover", "bollinger", "macd", "smart"
        interval        : "15m", "1h", "4h", "1d"
        capital         : capital de départ en USDT
        params          : paramètres de la stratégie (optionnel)
        stop_loss_pct   : stop loss en % (ex 3.0 = -3%)
        take_profit_pct : take profit en % (ex 6.0 = +6%)
        candles_limit   : nombre de bougies à utiliser

    Returns:
        dict avec stats, trades, courbe equity
    """
    strat = STRATEGIES.get(strategy_id)
    if not strat:
        return {"ok": False, "error": f"Stratégie inconnue: {strategy_id}"}

    candles = fetch_historical_candles(symbol, interval, candles_limit)
    if len(candles) < 50:
        return {"ok": False, "error": f"Pas assez de données pour {symbol} ({len(candles)} bougies)"}

    strategy_fn = strat["fn"]
    p           = {**strat["params"], **(params or {})}

    # ── Simulation ────────────────────────────────────────────
    cash        = capital
    position    = 0.0   # quantité détenue
    entry_price = 0.0
    trades      = []
    equity_curve= [capital]
    returns     = []
    warmup      = 50    # bougies de warmup

    for i in range(warmup, len(candles)):
        window = candles[:i+1]
        price  = candles[i]["c"]
        ts     = candles[i]["ts"]

        # ── Gestion position ouverte ─────────────────────────
        if position > 0:
            pnl_pct = (price - entry_price) / entry_price * 100
            # Stop Loss
            if pnl_pct <= -stop_loss_pct:
                cash      += position * price * 0.999  # 0.1% frais
                pnl_usdt   = (price - entry_price) * position
                trades.append({
                    "type": "STOP LOSS", "buy": round(entry_price, 4),
                    "sell": round(price, 4), "qty": round(position, 6),
                    "pnl_usdt": round(pnl_usdt, 2),
                    "pnl_pct":  round(pnl_pct, 2), "time": ts
                })
                returns.append(pnl_pct / 100)
                equity_curve.append(round(cash, 2))
                position = 0.0; entry_price = 0.0
                continue
            # Take Profit
            if pnl_pct >= take_profit_pct:
                cash      += position * price * 0.999
                pnl_usdt   = (price - entry_price) * position
                trades.append({
                    "type": "TAKE PROFIT", "buy": round(entry_price, 4),
                    "sell": round(price, 4), "qty": round(position, 6),
                    "pnl_usdt": round(pnl_usdt, 2),
                    "pnl_pct":  round(pnl_pct, 2), "time": ts
                })
                returns.append(pnl_pct / 100)
                equity_curve.append(round(cash, 2))
                position = 0.0; entry_price = 0.0
                continue

        # ── Signal de la stratégie ───────────────────────────
        signal = strategy_fn(window, p)

        if signal == "buy" and position == 0 and cash > 10:
            # Entrer en position (100% du capital disponible)
            position    = (cash * 0.999) / price  # 0.1% frais
            entry_price = price
            cash        = 0.0

        elif signal == "sell" and position > 0:
            # Sortir de la position
            cash      = position * price * 0.999
            pnl_usdt  = (price - entry_price) * position
            pnl_pct   = (price - entry_price) / entry_price * 100
            trades.append({
                "type": "SIGNAL", "buy": round(entry_price, 4),
                "sell": round(price, 4), "qty": round(position, 6),
                "pnl_usdt": round(pnl_usdt, 2),
                "pnl_pct":  round(pnl_pct, 2), "time": ts
            })
            returns.append(pnl_pct / 100)
            equity_curve.append(round(cash, 2))
            position = 0.0; entry_price = 0.0

        # Valeur totale du portefeuille
        total = cash + position * price
        equity_curve.append(round(total, 2))

    # ── Clôturer la position finale si ouverte ────────────────
    if position > 0:
        last_price = candles[-1]["c"]
        cash      += position * last_price * 0.999
        pnl_usdt   = (last_price - entry_price) * position
        pnl_pct    = (last_price - entry_price) / entry_price * 100
        trades.append({
            "type": "CLOSE", "buy": round(entry_price, 4),
            "sell": round(last_price, 4), "qty": round(position, 6),
            "pnl_usdt": round(pnl_usdt, 2),
            "pnl_pct":  round(pnl_pct, 2), "time": candles[-1]["ts"]
        })

    # ── Statistiques finales ──────────────────────────────────
    final_capital = round(cash, 2)
    total_pnl     = round(final_capital - capital, 2)
    total_pnl_pct = round((final_capital - capital) / capital * 100, 2)

    winners = [t for t in trades if t["pnl_pct"] > 0]
    losers  = [t for t in trades if t["pnl_pct"] <= 0]
    win_rate= round(len(winners) / len(trades) * 100, 1) if trades else 0

    gross_profit = sum(t["pnl_usdt"] for t in winners) if winners else 0
    gross_loss   = abs(sum(t["pnl_usdt"] for t in losers)) if losers else 0
    profit_factor= round(gross_profit / gross_loss, 2) if gross_loss > 0 else (99.0 if gross_profit > 0 else 0.0)

    max_dd   = calc_max_drawdown(equity_curve)
    sharpe   = calc_sharpe(returns)

    best_trade  = round(max((t["pnl_pct"] for t in trades), default=0), 2)
    worst_trade = round(min((t["pnl_pct"] for t in trades), default=0), 2)
    avg_trade   = round(sum(t["pnl_pct"] for t in trades) / len(trades), 2) if trades else 0

    # Courbe equity pour le graphique (1 point par 10 bougies max)
    step = max(1, len(equity_curve) // 200)
    chart_curve = [{"x": i, "y": v} for i, v in enumerate(equity_curve[::step])]

    return {
        "ok":      True,
        "symbol":  symbol.upper(),
        "strategy":strat["name"],
        "interval":interval,
        "period":  f"{candles[warmup]['ts'][:10]} → {candles[-1]['ts'][:10]}",
        "candles": len(candles),
        "params":  p,
        "stats": {
            "initial_capital": capital,
            "final_capital":   final_capital,
            "total_pnl":       total_pnl,
            "pnl_pct":         total_pnl_pct,
            "win_rate":        win_rate,
            "total_trades":    len(trades),
            "winners":         len(winners),
            "losers":          len(losers),
            "profit_factor":   profit_factor,
            "max_drawdown":    max_dd,
            "sharpe":          sharpe,
            "best_trade":      best_trade,
            "worst_trade":     worst_trade,
            "avg_trade":       avg_trade,
        },
        "trades":       trades[-50:],  # 50 derniers trades
        "equity_curve": chart_curve,
    }


def compare_strategies(symbol: str, interval: str = "1h",
                       capital: float = 1000.0, candles_limit: int = 500) -> dict:
    """
    Compare toutes les stratégies sur le même symbole.
    Retourne un classement par performance.
    """
    results = []
    candles = fetch_historical_candles(symbol, interval, candles_limit)
    if len(candles) < 50:
        return {"ok": False, "error": "Pas assez de données"}

    for strat_id, strat in STRATEGIES.items():
        try:
            r = run_backtest(symbol, strat_id, interval, capital,
                             candles_limit=candles_limit)
            if r.get("ok"):
                results.append({
                    "strategy_id": strat_id,
                    "name":        strat["name"],
                    "emoji":       strat["emoji"],
                    "desc":        strat["desc"],
                    "pnl_pct":     r["stats"]["pnl_pct"],
                    "win_rate":    r["stats"]["win_rate"],
                    "total_trades":r["stats"]["total_trades"],
                    "sharpe":      r["stats"]["sharpe"],
                    "max_drawdown":r["stats"]["max_drawdown"],
                    "profit_factor":r["stats"]["profit_factor"],
                    "final_capital":r["stats"]["final_capital"],
                })
        except Exception as e:
            print(f"[Backtest] compare {strat_id}: {e}")

    results.sort(key=lambda x: x["pnl_pct"], reverse=True)
    return {
        "ok":      True,
        "symbol":  symbol.upper(),
        "interval":interval,
        "period":  f"{candles[50]['ts'][:10]} → {candles[-1]['ts'][:10]}",
        "results": results,
    }


# ── DB Backtests sauvegardés ──────────────────────────────────
def init_backtest_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS backtests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER DEFAULT 0,
            symbol TEXT, strategy TEXT, interval TEXT,
            pnl_pct REAL, win_rate REAL, total_trades INTEGER,
            sharpe REAL, max_drawdown REAL,
            params_json TEXT, created TEXT
        )
    """)
    conn.commit(); conn.close()

def save_backtest_result(user_id, result):
    """Sauvegarde un résultat de backtest en DB."""
    import json
    try:
        init_backtest_db()
        conn = get_connection()
        stats = result.get("stats", {})
        conn.execute("""
            INSERT INTO backtests
            (user_id,symbol,strategy,interval,pnl_pct,win_rate,
             total_trades,sharpe,max_drawdown,params_json,created)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            user_id,
            result.get("symbol",""),
            result.get("strategy",""),
            result.get("interval",""),
            stats.get("pnl_pct",0),
            stats.get("win_rate",0),
            stats.get("total_trades",0),
            stats.get("sharpe",0),
            stats.get("max_drawdown",0),
            json.dumps(result.get("params",{})),
            datetime.now().isoformat()
        ))
        conn.commit(); conn.close()
        return True
    except Exception as e:
        print(f"[Backtest] save error: {e}")
        return False

def get_backtest_history(user_id, limit=20):
    """Récupère l'historique des backtests d'un utilisateur."""
    try:
        init_backtest_db()
        conn = get_connection(); conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM backtests WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except:
        return []
