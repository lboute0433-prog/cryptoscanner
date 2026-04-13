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
    "settings":           ("key",),
    "tfa_codes":          ("user_id",),
    "user_exchange_keys": ("user_id", "exchange"),
    "blacklist":          ("symbol",),
    "watchlist":          ("user_id", "symbol"),
    "cot_reports":        ("asset", "report_date"),
    "macro_cache":        ("key",),
    "alert_prefs":        ("user_id",),
    "tg_subscribers":     ("chat_id",),
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
