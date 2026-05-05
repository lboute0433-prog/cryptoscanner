"""
Trading Setups Library — Validated setups for VIP users.
Stores proven patterns with entry/exit rules, risk/reward ratios, win rates.
"""
import sqlite3
from datetime import datetime
from db import get_connection

def init_setups_tables():
    """Initialize setups database tables."""
    try:
        conn = get_connection()
        conn.execute("""CREATE TABLE IF NOT EXISTS trading_setups (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            asset TEXT NOT NULL,
            pattern_type TEXT,
            timeframe TEXT,
            entry_rule TEXT,
            exit_rule TEXT,
            stop_loss_rule TEXT,
            take_profit_rule TEXT,
            risk_reward_ratio REAL,
            avg_win_rate REAL,
            total_trades INTEGER,
            winning_trades INTEGER,
            avg_duration_hours INTEGER,
            difficulty TEXT,
            market_condition TEXT,
            created_date TEXT,
            updated_date TEXT,
            vip_only BOOLEAN,
            active BOOLEAN DEFAULT 1
        )""")

        conn.execute("""CREATE TABLE IF NOT EXISTS setup_examples (
            id INTEGER PRIMARY KEY,
            setup_id INTEGER NOT NULL,
            asset TEXT,
            entry_price REAL,
            exit_price REAL,
            stop_price REAL,
            profit_usd REAL,
            duration_hours REAL,
            result TEXT,
            date_traded TEXT,
            notes TEXT,
            FOREIGN KEY(setup_id) REFERENCES trading_setups(id)
        )""")

        conn.commit()
        conn.close()
        print("[Setups] Tables initialized")
    except Exception as e:
        print(f"[Setups] Init error: {e}")

def get_all_setups(vip_only=True):
    """Retrieve all available setups."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row

        query = "SELECT * FROM trading_setups WHERE active = 1"
        if vip_only:
            query += " AND vip_only = 1"
        query += " ORDER BY avg_win_rate DESC"

        rows = conn.execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[Setups] Get all error: {e}")
        return []

def get_setup_by_id(setup_id):
    """Get detailed setup information with examples."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row

        setup = conn.execute(
            "SELECT * FROM trading_setups WHERE id = ?", (setup_id,)
        ).fetchone()

        if not setup:
            conn.close()
            return None

        examples = conn.execute(
            "SELECT * FROM setup_examples WHERE setup_id = ? ORDER BY date_traded DESC",
            (setup_id,)
        ).fetchall()

        conn.close()

        return {
            "setup": dict(setup),
            "examples": [dict(e) for e in examples]
        }
    except Exception as e:
        print(f"[Setups] Get by ID error: {e}")
        return None

def get_setups_by_asset(asset):
    """Get all setups for a specific asset."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT * FROM trading_setups WHERE asset = ? AND active = 1 AND vip_only = 1 ORDER BY avg_win_rate DESC",
            (asset,)
        ).fetchall()

        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[Setups] Get by asset error: {e}")
        return []

def get_setups_by_pattern(pattern_type):
    """Get setups by pattern type (e.g., 'breakout', 'retest', 'divergence')."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT * FROM trading_setups WHERE pattern_type = ? AND active = 1 AND vip_only = 1 ORDER BY avg_win_rate DESC",
            (pattern_type,)
        ).fetchall()

        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[Setups] Get by pattern error: {e}")
        return []

def get_high_probability_setups(min_win_rate=0.6):
    """Get only high-probability setups (>60% win rate by default)."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT * FROM trading_setups WHERE active = 1 AND vip_only = 1 AND avg_win_rate >= ? ORDER BY avg_win_rate DESC",
            (min_win_rate,)
        ).fetchall()

        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[Setups] Get high prob error: {e}")
        return []

def create_setup(name, asset, pattern_type, timeframe, entry_rule, exit_rule,
                 stop_loss_rule, take_profit_rule, risk_reward_ratio, avg_win_rate,
                 total_trades, winning_trades, difficulty, market_condition, description=""):
    """Create a new trading setup."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO trading_setups (
                name, description, asset, pattern_type, timeframe, entry_rule, exit_rule,
                stop_loss_rule, take_profit_rule, risk_reward_ratio, avg_win_rate,
                total_trades, winning_trades, difficulty, market_condition, vip_only,
                created_date, updated_date, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, description, asset, pattern_type, timeframe, entry_rule, exit_rule,
            stop_loss_rule, take_profit_rule, risk_reward_ratio, avg_win_rate,
            total_trades, winning_trades, difficulty, market_condition, 1,
            now, now, 1
        ))

        conn.commit()
        setup_id = cursor.lastrowid
        conn.close()
        print(f"[Setups] Created setup {setup_id}: {name}")
        return setup_id
    except Exception as e:
        print(f"[Setups] Create error: {e}")
        return None

def add_setup_example(setup_id, asset, entry_price, exit_price, stop_price, profit_usd, duration_hours, result, notes=""):
    """Add a real-world example of a setup being executed."""
    try:
        conn = get_connection()
        now = datetime.now().isoformat()

        conn.execute("""
            INSERT INTO setup_examples (
                setup_id, asset, entry_price, exit_price, stop_price, profit_usd,
                duration_hours, result, date_traded, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            setup_id, asset, entry_price, exit_price, stop_price, profit_usd,
            duration_hours, result, now, notes
        ))

        # Update setup statistics
        examples = conn.execute(
            "SELECT result FROM setup_examples WHERE setup_id = ?", (setup_id,)
        ).fetchall()

        total = len(examples)
        winning = sum(1 for e in examples if e[0] == 'win')

        conn.execute(
            "UPDATE trading_setups SET total_trades = ?, winning_trades = ?, avg_win_rate = ?, updated_date = ? WHERE id = ?",
            (total, winning, winning / total if total > 0 else 0, datetime.now().isoformat(), setup_id)
        )

        conn.commit()
        conn.close()
        print(f"[Setups] Added example for setup {setup_id}")
        return True
    except Exception as e:
        print(f"[Setups] Add example error: {e}")
        return False

def get_setup_stats():
    """Get overall statistics about the setups library."""
    try:
        conn = get_connection()
        conn.row_factory = sqlite3.Row

        total = conn.execute("SELECT COUNT(*) as cnt FROM trading_setups WHERE active = 1 AND vip_only = 1").fetchone()
        high_prob = conn.execute("SELECT COUNT(*) as cnt FROM trading_setups WHERE active = 1 AND vip_only = 1 AND avg_win_rate >= 0.6").fetchone()
        by_pattern = conn.execute(
            "SELECT pattern_type, COUNT(*) as cnt FROM trading_setups WHERE active = 1 AND vip_only = 1 GROUP BY pattern_type"
        ).fetchall()

        avg_wr = conn.execute(
            "SELECT AVG(avg_win_rate) as wr FROM trading_setups WHERE active = 1 AND vip_only = 1"
        ).fetchone()

        conn.close()

        return {
            "total_setups": total[0] if total else 0,
            "high_probability_count": high_prob[0] if high_prob else 0,
            "average_win_rate": round(avg_wr[0] if avg_wr[0] else 0, 3),
            "by_pattern": {p["pattern_type"]: p["cnt"] for p in by_pattern}
        }
    except Exception as e:
        print(f"[Setups] Stats error: {e}")
        return {}

# Initialize on import
init_setups_tables()
