"""
Couche d'abstraction base de données — CryptoScanner Pro
Supporte SQLite (dev/local) et PostgreSQL (prod/serveur).
Auto-détection via DATABASE_URL env var.

Usage dans les autres modules :
    from db import get_connection, DB_PATH
    conn = get_connection()
    conn.row_factory = ...   # fonctionne dans les deux modes
    conn.execute(sql, params)
    conn.commit()
    conn.close()
"""

from __future__ import annotations

import os
import re
import sqlite3
import threading
from typing import Any, Optional

# ── Détection du mode ─────────────────────────────────────────
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
USE_POSTGRES: bool = DATABASE_URL.startswith(("postgres://", "postgresql://"))

# DB_PATH reste utilisé en mode SQLite (compat avec l'existant)
from config import DATABASE_PATH as DB_PATH  # noqa: E402

try:
    import psycopg2
    import psycopg2.extras
    _PSYCOPG2_OK = True
except ImportError:
    _PSYCOPG2_OK = False

if USE_POSTGRES and not _PSYCOPG2_OK:
    raise RuntimeError(
        "[DB] DATABASE_URL définie mais 'psycopg2-binary' manquant. "
        "Installez-la avec : pip install psycopg2-binary"
    )

# ── Mapping colonnes de conflit pour INSERT OR REPLACE ────────
# table_name (minuscule) → tuple de colonnes PRIMARY KEY / UNIQUE utilisé
# pour générer ON CONFLICT (...) DO UPDATE SET ...
_CONFLICT_COLS: dict[str, tuple[str, ...]] = {
    "settings":                  ("key",),
    "tfa_codes":                 ("user_id",),
    "user_exchange_keys":        ("user_id", "exchange"),
    "user_exchange_settings":    ("user_id", "exchange"),
    "blacklist":                 ("symbol",),
    "watchlist":                 ("user_id", "symbol"),
    "cot_reports":               ("asset", "report_date"),
    "macro_cache":               ("key",),
    "alert_prefs":               ("user_id",),
    "tg_subscribers":            ("chat_id",),
}

# ── Conversions SQL SQLite → PostgreSQL ───────────────────────

# Regex full-statement : capture table, colonnes et VALUES (...) sur une ou plusieurs lignes
# Note : VALUES (...) avec ? ne contient pas de parenthèses imbriquées
_RE_INSERT_IGNORE = re.compile(
    r"INSERT\s+OR\s+IGNORE\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*(VALUES\s*\([^)]*\))",
    re.IGNORECASE | re.DOTALL,
)
_RE_INSERT_REPLACE = re.compile(
    r"INSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*(VALUES\s*\([^)]*\))",
    re.IGNORECASE | re.DOTALL,
)


def _conflict_clause(table: str, cols: list[str]) -> str:
    """Génère la clause ON CONFLICT pour PostgreSQL."""
    conflict = _CONFLICT_COLS.get(table.lower())
    if not conflict:
        # Fallback : DO NOTHING (safe)
        return "ON CONFLICT DO NOTHING"
    non_key = [c for c in cols if c not in conflict]
    if not non_key:
        return f"ON CONFLICT ({', '.join(conflict)}) DO NOTHING"
    updates = ", ".join(f"{c}=EXCLUDED.{c}" for c in non_key)
    return f"ON CONFLICT ({', '.join(conflict)}) DO UPDATE SET {updates}"


def _parse_cols(cols_str: str) -> list[str]:
    return [c.strip().strip('"').strip("'") for c in cols_str.split(",")]


def adapt_query(sql: str) -> str:
    """
    Convertit une requête SQLite en requête PostgreSQL :
    - ? → %s
    - INSERT OR IGNORE → ON CONFLICT DO NOTHING
    - INSERT OR REPLACE → ON CONFLICT DO UPDATE
    - INTEGER PRIMARY KEY AUTOINCREMENT → SERIAL PRIMARY KEY
    - REAL → DOUBLE PRECISION
    - datetime('now') → NOW()
    """
    # INSERT OR IGNORE → ON CONFLICT DO NOTHING
    def _replace_ignore(m: re.Match) -> str:
        table = m.group(1)
        cols_raw = m.group(2).strip()
        values_clause = m.group(3)
        return f"INSERT INTO {table} ({cols_raw}) {values_clause} ON CONFLICT DO NOTHING"

    sql = _RE_INSERT_IGNORE.sub(_replace_ignore, sql)

    # INSERT OR REPLACE → ON CONFLICT DO UPDATE SET
    def _replace_replace(m: re.Match) -> str:
        table = m.group(1)
        cols_raw = m.group(2).strip()
        values_clause = m.group(3)
        cols = _parse_cols(cols_raw)
        clause = _conflict_clause(table, cols)
        return f"INSERT INTO {table} ({cols_raw}) {values_clause} {clause}"

    sql = _RE_INSERT_REPLACE.sub(_replace_replace, sql)

    # Schema: AUTOINCREMENT → SERIAL / BIGSERIAL
    sql = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)
    sql = re.sub(r"BIGINT\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "BIGSERIAL PRIMARY KEY", sql, flags=re.IGNORECASE)

    # REAL → DOUBLE PRECISION
    sql = re.sub(r"\bREAL\b", "DOUBLE PRECISION", sql, flags=re.IGNORECASE)

    # datetime('now') → NOW()
    sql = re.sub(r"datetime\('now'\)", "NOW()", sql, flags=re.IGNORECASE)

    # ? → %s (après toutes les autres transformations)
    sql = sql.replace("?", "%s")

    return sql


# ── Wrapper PostgreSQL compatible sqlite3 ────────────────────

class _PGCursor:
    """Curseur PostgreSQL avec interface sqlite3."""

    def __init__(self, pg_cursor, row_factory=None):
        self._cur = pg_cursor
        self._row_factory = row_factory

    def execute(self, sql: str, params=()) -> "_PGCursor":
        self._cur.execute(adapt_query(sql), params)
        return self

    def executemany(self, sql: str, seq_of_params) -> "_PGCursor":
        self._cur.executemany(adapt_query(sql), seq_of_params)
        return self

    def executescript(self, sql: str) -> None:
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                self._cur.execute(adapt_query(stmt))

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        if self._row_factory:
            return row  # RealDictRow already dict-like
        return row

    def fetchall(self):
        return self._cur.fetchall() or []

    def fetchmany(self, size=None):
        return self._cur.fetchmany(size) if size else self._cur.fetchmany()

    @property
    def lastrowid(self):
        try:
            self._cur.execute("SELECT lastval()")
            return self._cur.fetchone()[0]
        except Exception:
            return None

    @property
    def rowcount(self):
        return self._cur.rowcount

    def __iter__(self):
        return iter(self.fetchall())

    def close(self):
        self._cur.close()


class _PGRow(dict):
    """Émule sqlite3.Row : accès par index ou par nom de colonne."""

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

    def keys(self):
        return list(super().keys())


class _PGConnection:
    """
    Connexion PostgreSQL avec interface sqlite3.
    Supporte : execute(), executemany(), cursor(), row_factory,
               commit(), rollback(), close(), context manager.
    """

    def __init__(self, dsn: str):
        self._conn = psycopg2.connect(dsn)
        self._lock = threading.Lock()
        self._row_factory = None  # sqlite3.Row compatible

    # ── row_factory (propriété) ───────────────────────────────
    @property
    def row_factory(self):
        return self._row_factory

    @row_factory.setter
    def row_factory(self, factory):
        self._row_factory = factory
        # Activer RealDictCursor si row_factory ressemble à sqlite3.Row
        if factory is not None:
            self._conn.cursor_factory = psycopg2.extras.RealDictCursor
        else:
            self._conn.cursor_factory = psycopg2.extensions.cursor

    def cursor(self) -> _PGCursor:
        if self._row_factory:
            cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            cur = self._conn.cursor()
        return _PGCursor(cur, row_factory=self._row_factory)

    def execute(self, sql: str, params=()) -> _PGCursor:
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql: str, seq_of_params) -> None:
        cur = self.cursor()
        cur.executemany(sql, seq_of_params)

    def executescript(self, sql: str) -> None:
        cur = self.cursor()
        cur.executescript(sql)

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()
        return False


# ── API publique ──────────────────────────────────────────────

def get_connection(database: Optional[str] = None) -> Any:
    """
    Retourne une connexion DB selon le mode détecté :
    - PostgreSQL si DATABASE_URL est définie
    - SQLite sinon (comportement habituel)

    Exemple :
        conn = get_connection()
        conn.row_factory = sqlite3.Row   # fonctionne dans les deux modes
        rows = conn.execute("SELECT * FROM users").fetchall()
        conn.close()
    """
    if USE_POSTGRES:
        return _PGConnection(DATABASE_URL)

    # Mode SQLite : utiliser la connexion patchée de config
    from config import connect_sqlite
    db_path = database or DB_PATH
    return connect_sqlite(db_path)


def get_columns(table: str, conn=None) -> list[str]:
    """
    Retourne la liste des noms de colonnes d'une table.
    Remplace PRAGMA table_info() (SQLite-only).
    Compatible SQLite et PostgreSQL.
    """
    close_after = conn is None
    if conn is None:
        conn = get_connection()
    try:
        if USE_POSTGRES:
            rows = conn.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name=%s ORDER BY ordinal_position",
                (table,),
            ).fetchall()
            return [r[0] if isinstance(r, (list, tuple)) else r["column_name"] for r in rows]
        else:
            rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
            return [r[1] for r in rows]
    finally:
        if close_after:
            conn.close()


def is_postgres() -> bool:
    """Retourne True si le mode PostgreSQL est actif."""
    return USE_POSTGRES


def print_db_mode() -> None:
    if USE_POSTGRES:
        host = DATABASE_URL.split("@")[-1].split("/")[0] if "@" in DATABASE_URL else "?"
        print(f"[DB] Mode PostgreSQL — {host}")
    else:
        print(f"[DB] Mode SQLite — {DB_PATH}")


def init_users_db():
    """Initialize users table with subscription schema."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                subscription_tier TEXT DEFAULT 'free',
                subscription_expires DATETIME,
                telegram_id TEXT,
                telegram_verified INTEGER DEFAULT 0,
                role TEXT DEFAULT 'visitor'
            )
        ''')
        conn.commit()
        print("[DB] Users table initialized")
    except Exception as e:
        print(f"[DB] Error initializing users table: {e}")
    finally:
        conn.close()


def migrate_add_subscription_tier():
    """Add subscription_tier column if it doesn't exist."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('ALTER TABLE users ADD COLUMN subscription_tier TEXT DEFAULT "free"')
        cur.execute('ALTER TABLE users ADD COLUMN subscription_expires DATETIME')
        conn.commit()
        print("[DB] Migration: Added subscription_tier columns")
    except Exception:
        pass
    finally:
        conn.close()


def migrate_add_platform_settings():
    """Create platform_settings table for storing admin configuration parameters."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS platform_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("[DB] Migration: Created platform_settings table")
    except Exception as e:
        print(f"[DB] Error creating platform_settings table: {e}")
    finally:
        conn.close()


def get_setting(key: str, default: str = "") -> str:
    """Get a platform setting from the database."""
    conn = get_connection()
    try:
        cur = conn.execute("SELECT value FROM platform_settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row[0] if row else default
    except Exception:
        return default
    finally:
        conn.close()


def set_setting(key: str, value: str) -> bool:
    """Set a platform setting in the database."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO platform_settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            (key, str(value))
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] Error setting platform_settings: {e}")
        return False
    finally:
        conn.close()


# ── Exchange data tables (Phase 1) ────────────────────────────

def create_exchange_data_table() -> bool:
    """
    Create exchange_data table to store OHLCV data from multiple exchanges.

    Table structure:
    - id: Primary key with auto-increment
    - exchange: Exchange name (e.g., 'binance', 'bybit', 'kraken')
    - symbol: Trading pair (e.g., 'BTC/USDT')
    - timestamp: Unix timestamp of OHLCV candle
    - open, high, low, close, volume: OHLCV data
    - created_at: Record creation timestamp

    Constraints:
    - UNIQUE(exchange, symbol, timestamp) prevents duplicate data
    - INDEX on (exchange, symbol) for fast queries

    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS exchange_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(exchange, symbol, timestamp)
            )
        ''')

        # Create index for fast queries
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_exchange_data_exchange_symbol
            ON exchange_data(exchange, symbol)
        ''')

        conn.commit()
        print("[DB] exchange_data table created successfully")
        return True
    except Exception as e:
        print(f"[DB] Error creating exchange_data table: {e}")
        return False
    finally:
        conn.close()


def create_exchange_metadata_table() -> bool:
    """
    Create exchange_metadata table to store exchange capabilities and fees.

    Table structure:
    - id: Primary key with auto-increment
    - exchange: Unique exchange identifier (e.g., 'binance')
    - maker_fee: Maker fee percentage
    - taker_fee: Taker fee percentage
    - min_order_amount: Minimum order amount in quote currency
    - supports_fetch_ticker: Boolean flag for ticker support
    - supports_fetch_ohlcv: Boolean flag for OHLCV support
    - rate_limit: API rate limit (requests per minute)
    - updated_at: Last update timestamp

    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS exchange_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT NOT NULL UNIQUE,
                maker_fee REAL,
                taker_fee REAL,
                min_order_amount REAL,
                supports_fetch_ticker INTEGER DEFAULT 1,
                supports_fetch_ohlcv INTEGER DEFAULT 1,
                rate_limit INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        print("[DB] exchange_metadata table created successfully")
        return True
    except Exception as e:
        print(f"[DB] Error creating exchange_metadata table: {e}")
        return False
    finally:
        conn.close()


def insert_exchange_data(
    exchange: str,
    symbol: str,
    timestamp: int,
    open_price: float,
    high: float,
    low: float,
    close: float,
    volume: float
) -> Optional[int]:
    """
    Insert OHLCV data for an exchange and symbol.

    If the record already exists (same exchange, symbol, timestamp),
    it will be ignored due to UNIQUE constraint.

    Args:
        exchange: Exchange name (e.g., 'binance')
        symbol: Trading pair (e.g., 'BTC/USDT')
        timestamp: Unix timestamp
        open_price: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume

    Returns:
        int: Last inserted row ID, or None if insert failed/ignored

    Example:
        >>> row_id = insert_exchange_data(
        ...     'binance', 'BTC/USDT', 1694000000,
        ...     45000, 45500, 44800, 45200, 1500.5
        ... )
        >>> print(row_id)
        42
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT OR IGNORE INTO exchange_data
            (exchange, symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (exchange, symbol, timestamp, open_price, high, low, close, volume))

        conn.commit()

        # Return lastrowid if insert happened, None if ignored
        if cur.rowcount > 0:
            return cur.lastrowid
        return None
    except Exception as e:
        print(f"[DB] Error inserting exchange_data: {e}")
        return None
    finally:
        conn.close()


def insert_exchange_metadata(
    exchange: str,
    maker_fee: Optional[float] = None,
    taker_fee: Optional[float] = None,
    min_order_amount: Optional[float] = None,
    supports_fetch_ticker: bool = True,
    supports_fetch_ohlcv: bool = True,
    rate_limit: Optional[int] = None
) -> Optional[int]:
    """
    Insert or update metadata for an exchange.

    Uses INSERT OR REPLACE to handle updates to existing exchanges.

    Args:
        exchange: Exchange name (e.g., 'binance')
        maker_fee: Maker fee percentage (optional)
        taker_fee: Taker fee percentage (optional)
        min_order_amount: Minimum order amount (optional)
        supports_fetch_ticker: Whether exchange supports ticker fetching
        supports_fetch_ohlcv: Whether exchange supports OHLCV fetching
        rate_limit: API rate limit in requests per minute (optional)

    Returns:
        int: Row ID of inserted/updated record, or None if failed

    Example:
        >>> metadata_id = insert_exchange_metadata(
        ...     'binance',
        ...     maker_fee=0.001,
        ...     taker_fee=0.001,
        ...     rate_limit=1200,
        ...     supports_fetch_ohlcv=True
        ... )
        >>> print(metadata_id)
        1
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT OR REPLACE INTO exchange_metadata
            (exchange, maker_fee, taker_fee, min_order_amount,
             supports_fetch_ticker, supports_fetch_ohlcv, rate_limit, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            exchange,
            maker_fee,
            taker_fee,
            min_order_amount,
            1 if supports_fetch_ticker else 0,
            1 if supports_fetch_ohlcv else 0,
            rate_limit
        ))

        conn.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"[DB] Error inserting exchange_metadata: {e}")
        return None
    finally:
        conn.close()


def get_exchange_metadata(exchange: str) -> Optional[dict]:
    """
    Retrieve metadata for a specific exchange.

    Args:
        exchange: Exchange name (e.g., 'binance')

    Returns:
        dict: Exchange metadata with keys (id, exchange, maker_fee, taker_fee, etc.)
              or None if exchange not found

    Example:
        >>> metadata = get_exchange_metadata('binance')
        >>> if metadata:
        ...     print(metadata['maker_fee'])
        0.001
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row if not USE_POSTGRES else None
    cur = conn.cursor()
    try:
        cur.execute(
            'SELECT * FROM exchange_metadata WHERE exchange = ?',
            (exchange,)
        )
        row = cur.fetchone()

        if row:
            # Convert sqlite3.Row or dict-like to regular dict
            if isinstance(row, dict):
                return dict(row)
            else:
                return dict(zip([desc[0] for desc in cur.description], row))
        return None
    except Exception as e:
        print(f"[DB] Error retrieving exchange_metadata: {e}")
        return None
    finally:
        conn.close()


def create_user_exchange_settings_table() -> bool:
    """
    Create user_exchange_settings table to store per-user exchange preferences.

    Table structure:
    - id: Primary key with auto-increment
    - user_id: Foreign key to users table
    - exchange: Exchange name (e.g., 'binance', 'bybit')
    - enabled: Boolean flag for whether exchange is enabled for this user
    - created_at: Record creation timestamp
    - updated_at: Last update timestamp

    Constraints:
    - UNIQUE(user_id, exchange) prevents duplicate preferences per user/exchange

    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS user_exchange_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                exchange TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, exchange),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')

        # Create index for fast queries by user
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_user_exchange_settings_user_id
            ON user_exchange_settings(user_id)
        ''')

        conn.commit()
        print("[DB] user_exchange_settings table created successfully")
        return True
    except Exception as e:
        print(f"[DB] Error creating user_exchange_settings table: {e}")
        return False
    finally:
        conn.close()


def toggle_user_exchange_setting(user_id: int, exchange: str, enabled: bool) -> bool:
    """
    Enable or disable an exchange for a specific user.

    Args:
        user_id: User ID
        exchange: Exchange name (e.g., 'binance')
        enabled: Whether to enable (True) or disable (False) the exchange

    Returns:
        bool: True if successful, False otherwise

    Example:
        >>> success = toggle_user_exchange_setting(user_id=1, exchange='binance', enabled=True)
        >>> print(success)
        True
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT OR REPLACE INTO user_exchange_settings
            (user_id, exchange, enabled, updated_at)
            VALUES (?, ?, ?, datetime('now'))
        ''', (user_id, exchange.lower(), 1 if enabled else 0))

        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] Error toggling user exchange setting: {e}")
        return False
    finally:
        conn.close()


def get_user_enabled_exchanges(user_id: int) -> list[str]:
    """
    Get list of enabled exchanges for a user.

    Args:
        user_id: User ID

    Returns:
        List of enabled exchange names, or empty list if error

    Example:
        >>> exchanges = get_user_enabled_exchanges(user_id=1)
        >>> print(exchanges)
        ['binance', 'bybit', 'kraken']
    """
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT exchange FROM user_exchange_settings WHERE user_id = ? AND enabled = 1 ORDER BY exchange",
            (user_id,)
        )
        rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"[DB] Error getting user enabled exchanges: {e}")
        return []
    finally:
        conn.close()


def migrate_add_exchange_tables() -> bool:
    """
    Create exchange_data, exchange_metadata, and user_exchange_settings tables.

    This is the main migration function for Phase 1 Task 2.
    It ensures all exchange-related tables exist and creates them if needed.

    Returns:
        bool: True if all tables created/exist, False if any failed

    Example:
        >>> success = migrate_add_exchange_tables()
        >>> print(success)
        True
    """
    success = True

    if not create_exchange_data_table():
        success = False

    if not create_exchange_metadata_table():
        success = False

    if not create_user_exchange_settings_table():
        success = False

    if success:
        print("[DB] Exchange tables migration completed successfully")

    return success


def migrate_add_watchlist_table():
    """Create watchlist table for user coin tracking."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                added DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, symbol),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
        print("[DB] Migration: Created watchlist table")
    except Exception as e:
        print(f"[DB] Error creating watchlist table: {e}")
    finally:
        conn.close()


# ── Fonction pour charger les paramètres d'alerte ──────────────────────
def load_admin_alert_settings() -> dict:
    """
    Charge les paramètres d'alerte depuis la table platform_settings.
    Retourne un dictionnaire avec la structure attendue par le code.

    Structure retournée:
    {
        'smart_signals': {'score_min': 85, 'max_per_cycle': 3, ...},
        'retrace_rsi': {'rsi_oversold': 30, 'rsi_overbought': 70, ...},
        'macro_events': {...}
    }
    """
    import json

    conn = get_connection()
    cur = conn.cursor()

    try:
        # Charger tous les paramètres depuis platform_settings
        cur.execute('SELECT key, value FROM platform_settings')
        rows = cur.fetchall()

        settings = {}
        for key, value in rows:
            try:
                # Essayer de parser comme JSON
                settings[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Si ce n'est pas du JSON, garder comme string
                settings[key] = value

        # Retourner les paramètres avec les valeurs par défaut si manquantes
        return {
            'smart_signals': settings.get('smart_signals', {
                'score_min': 85,
                'max_per_cycle': 3,
                'cooldown_hours': 24
            }),
            'retrace_rsi': settings.get('retrace_rsi', {
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'cooldown_hours': 12
            }),
            'macro_events': settings.get('macro_events', {
                'importance': 'moyen',
                'enabled': True,
                'cooldown_hours': 6
            })
        }
    except Exception as e:
        print(f"[DB] Erreur chargement settings: {e}")
        # Retourner les valeurs par défaut en cas d'erreur
        return {
            'smart_signals': {'score_min': 85, 'max_per_cycle': 3, 'cooldown_hours': 24},
            'retrace_rsi': {'rsi_oversold': 30, 'rsi_overbought': 70, 'cooldown_hours': 12},
            'macro_events': {'importance': 'moyen', 'enabled': True, 'cooldown_hours': 6}
        }
    finally:
        conn.close()


def init_alert_settings():
    """Initialize JSON-formatted alert settings if they don't exist in the database."""
    import json

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Check if alert settings already exist
        cur.execute("SELECT COUNT(*) FROM platform_settings WHERE key IN ('smart_signals', 'retrace_rsi', 'macro_events')")
        count = cur.fetchone()[0]

        if count >= 3:
            # Settings already initialized
            return

        # Define the alert configuration structure
        smart_signals = {
            'score_min': 50,
            'max_per_cycle': 3,
            'cooldown_hours': 24
        }

        retrace_rsi = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'cooldown_hours': 12
        }

        macro_events = {
            'importance': 'moyen',
            'enabled': True,
            'cooldown_hours': 6
        }

        # Insert or replace these settings
        cur.execute("INSERT OR REPLACE INTO platform_settings (key, value) VALUES (?, ?)",
                    ('smart_signals', json.dumps(smart_signals)))
        cur.execute("INSERT OR REPLACE INTO platform_settings (key, value) VALUES (?, ?)",
                    ('retrace_rsi', json.dumps(retrace_rsi)))
        cur.execute("INSERT OR REPLACE INTO platform_settings (key, value) VALUES (?, ?)",
                    ('macro_events', json.dumps(macro_events)))

        conn.commit()
        print("[DB] Alert settings initialized: smart_signals, retrace_rsi, macro_events")
    except Exception as e:
        print(f"[DB] Error initializing alert settings: {e}")
    finally:
        conn.close()
