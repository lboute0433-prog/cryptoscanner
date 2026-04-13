#!/usr/bin/env python3
"""Configuration centralisee pour CryptoScanner."""

from __future__ import annotations

import os
import sqlite3
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
_DOTENV_LOADED = False
_SQLITE_PATCHED = False
_SQLITE_LOCK = threading.Lock()
_RAW_SQLITE_CONNECT = sqlite3.connect


def load_dotenv() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return

    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            with env_path.open("r", encoding="utf-8") as handle:
                for raw_line in handle:
                    line = raw_line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
        except Exception as exc:
            print(f"[Config] Chargement .env impossible: {exc}")

    _DOTENV_LOADED = True


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


load_dotenv()

IS_RAILWAY = bool(os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT"))
DATABASE_PATH = os.environ.get("DATABASE_PATH") or os.environ.get("DB_PATH") or str(BASE_DIR / "cryptoscanner.db")
SQLITE_TIMEOUT_SECONDS = float(os.environ.get("SQLITE_TIMEOUT_SECONDS", "15"))
SQLITE_ENABLE_WAL = env_bool("SQLITE_ENABLE_WAL", default=not IS_RAILWAY)
RUN_BACKGROUND_JOBS = env_bool("RUN_BACKGROUND_JOBS", default=not IS_RAILWAY)
SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
TELEGRAM_TOKEN    = os.environ.get("TG_TOKEN", "")
TELEGRAM_CHAT     = os.environ.get("TG_CHAT", "")         # canal admin / DM admin
TELEGRAM_CHAT_FREE = os.environ.get("TG_CHAT_FREE", "")   # canal public FREE (alertes basiques)
SITE_URL          = os.environ.get("SITE_URL", "https://cryptoscanner.pro")  # URL du site
SMTP_EMAIL = os.environ.get("SMTP_EMAIL", "")
SMTP_LOGIN = os.environ.get("SMTP_LOGIN", SMTP_EMAIL)
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_EMAIL)
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USE_SSL = env_bool("SMTP_USE_SSL", default=False)
SMTP_USE_STARTTLS = env_bool("SMTP_USE_STARTTLS", default=not SMTP_USE_SSL)
ADMIN_NOTIFY_EMAIL = os.environ.get("ADMIN_NOTIFY_EMAIL", SMTP_EMAIL)
ADMIN_BOOTSTRAP_USER = os.environ.get("MAKE_ADMIN", "").strip().lower()
ADMIN_BOOTSTRAP_PASSWORD = os.environ.get("ADMIN_PASSWORD", "").strip()


def _configure_connection(conn: sqlite3.Connection) -> sqlite3.Connection:
    try:
        conn.execute(f"PRAGMA busy_timeout = {int(SQLITE_TIMEOUT_SECONDS * 1000)}")
    except Exception:
        pass
    try:
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception:
        pass
    if SQLITE_ENABLE_WAL:
        try:
            conn.execute("PRAGMA journal_mode = WAL")
        except Exception:
            pass
    return conn


def connect_sqlite(database: str | None = None, *args, **kwargs) -> sqlite3.Connection:
    db_path = database or DATABASE_PATH
    if db_path == "cryptoscanner.db":
        db_path = DATABASE_PATH
    kwargs.setdefault("timeout", SQLITE_TIMEOUT_SECONDS)
    conn = _RAW_SQLITE_CONNECT(db_path, *args, **kwargs)
    return _configure_connection(conn)


def patch_sqlite() -> None:
    global _SQLITE_PATCHED
    if _SQLITE_PATCHED:
        return

    with _SQLITE_LOCK:
        if _SQLITE_PATCHED:
            return

        original_connect = sqlite3.connect

        def _patched_connect(database, *args, **kwargs):
            db_path = DATABASE_PATH if database == "cryptoscanner.db" else database
            kwargs.setdefault("timeout", SQLITE_TIMEOUT_SECONDS)
            conn = original_connect(db_path, *args, **kwargs)
            return _configure_connection(conn)

        sqlite3.connect = _patched_connect
        _SQLITE_PATCHED = True


patch_sqlite()
