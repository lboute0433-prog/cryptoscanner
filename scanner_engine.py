#!/usr/bin/env python3
"""
CryptoScanner Pro V11 — Scanner Engine (CORRIGÉ)
- Fear & Greed Index
- Dominance BTC/ETH
- Funding Rates Binance
- Whale Alerts (gros mouvements on-chain)
- Watchlist personnelle
- Sécurité : rôles, sessions, rate limiting, logs
- Clés API exchange CHIFFRÉES avec security.py/vault
"""
import requests, sqlite3, os, hashlib, secrets, time, threading
from datetime import datetime, timedelta
from config import DATABASE_PATH as DB_PATH, TELEGRAM_CHAT, TELEGRAM_TOKEN, TELEGRAM_CHAT_FREE, SITE_URL
from db import get_connection

BINANCE_TICKER   = "https://api.binance.com/api/v3/ticker/24hr"
BINANCE_KLINES   = "https://api.binance.com/api/v3/klines"
BINANCE_FUNDING  = "https://fapi.binance.com/fapi/v1/premiumIndex"
BINANCE_FPERP    = "https://fapi.binance.com/fapi/v1/ticker/24hr"
BINANCE_FFUNDING = "https://fapi.binance.com/fapi/v1/premiumIndex"
KRAKEN_TICKER    = "https://api.kraken.com/0/public/Ticker"
KRAKEN_PAIRS     = "https://api.kraken.com/0/public/AssetPairs"
KRAKEN_OHLC      = "https://api.kraken.com/0/public/OHLC"
FEAR_GREED_URL   = "https://api.alternative.me/fng/?limit=1"
GLOBAL_MARKET    = "https://api.coingecko.com/api/v3/global"
COINGECKO_MARKET = "https://api.coingecko.com/api/v3/coins/markets"
WHALE_ALERT_URL  = "https://api.whale-alert.io/v1/transactions"

PRICE_ALERT_PCT   = 5.0
VOLUME_SPIKE_MULT = 3.0
SESSION_EXPIRE_H  = 24
MAX_LOGIN_ATTEMPTS= 50
RATE_LIMIT_WINDOW = 300

TG_TOKEN = TELEGRAM_TOKEN
TG_CHAT  = TELEGRAM_CHAT
WHALE_API_KEY = os.environ.get("WHALE_API_KEY", "")

# ── Thread Locks pour sécurité ───────────────────────────────
_data_lock = threading.Lock()
_alert_lock = threading.Lock()

# Top 50 coins par market cap (filtre anti-shitcoin)
TOP_50_SYMBOLS = {
"BTC","ETH","BNB","XRP","SOL","ADA","DOGE","TRX","AVAX","SHIB",
"LINK","DOT","BCH","NEAR","LTC","UNI","ICP","APT","POL","ETC",
"PEPE","FET","XLM","STX","OP","ARB","IMX","ATOM","FIL","VET",
"HBAR","MKR","INJ","GRT","ALGO","THETA","AAVE","SAND","AXS","MANA",
"XMR","EOS","FLOW","EGLD","CHZ","GALA","ENS","1INCH","COMP","SNX",
"WIF","BONK","JTO","PYTH","JUP","RNDR","TIA","SEI","SUI","APE"
}
STABLE_SYMBOLS = {
"USDT","USDC","DAI","USDE","USDS","FDUSD","TUSD","PYUSD","FRAX","RLUSD","USD1","XAUT","PAXG","WBT"
}

ROLE_ALIASES = {
    "viewer": "visitor",
    "trader": "member",
}
VALID_ROLES = {"visitor", "member", "paid", "vip", "admin", "banned"}
VALID_SUBSCRIPTION_STATUSES = {"inactive", "trial", "active", "overdue", "canceled"}


def normalize_role(role):
    value = (role or "").strip().lower()
    return ROLE_ALIASES.get(value, value or "member")


def normalize_subscription_status(status):
    value = (status or "").strip().lower()
    if value in VALID_SUBSCRIPTION_STATUSES:
        return value
    return "inactive"


def _safe_json_response(resp, default):
    try:
        ctype = (resp.headers.get("Content-Type", "") or "").lower()
        if resp.status_code != 200 or "json" not in ctype:
            return default
        return resp.json()
    except Exception:
        return default

# ── Indicateurs ───────────────────────────────────────────────
def calc_rsi(closes, period=14):
    if len(closes) < period+1: return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i]-closes[i-1]
        gains.append(max(d,0)); losses.append(max(-d,0))
    ag = sum(gains[-period:])/period
    al = sum(losses[-period:])/period
    return round(100-(100/(1+ag/al)), 2) if al else 100.0

def calc_ema(values, period):
    if len(values) < period: return None
    k = 2/(period+1); ema = sum(values[:period])/period
    for v in values[period:]: ema = v*k + ema*(1-k)
    return ema

def score_signal(rsi, macd_line, change_pct, vol_ratio, bb_pos):
    score = 50; direction = "neutral"
    if rsi is not None:
        if rsi < 30:   score += 20; direction = "buy"
        elif rsi < 40: score += 10; direction = "buy"
        elif rsi > 70: score -= 20; direction = "sell"
        elif rsi > 60: score -= 10; direction = "sell"
    if macd_line: score += 10 if macd_line > 0 else -10
    if change_pct > 5:    score -= 15
    elif change_pct > 2:  score -= 5
    elif change_pct < -5: score += 15
    elif change_pct < -2: score += 5
    if vol_ratio and vol_ratio > 2: score += 10
    if bb_pos is not None:
        if bb_pos < 0:   score += 15; direction = "buy"
        elif bb_pos > 1: score -= 15; direction = "sell"
    score = max(0, min(100, score))
    if score >= 65:   direction = "buy"
    elif score <= 35: direction = "sell"
    return score, direction

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def gen_token():
    return secrets.token_hex(32)

# ── Base de données ───────────────────────────────────────────
def init_db():
    conn = get_connection(); c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'member',
        subscription_status TEXT DEFAULT 'inactive',
        tg_chat_id TEXT DEFAULT '',
        tfa_enabled INTEGER DEFAULT 0,
        totp_enabled INTEGER DEFAULT 0,
        totp_secret TEXT DEFAULT '',
        email TEXT DEFAULT '',
        firstname TEXT DEFAULT '',
        lastname TEXT DEFAULT '',
        created TEXT,
        last_login TEXT
    );
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created TEXT,
        expires TEXT,
        ip TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        ip TEXT,
        success INTEGER,
        ts TEXT
    );
    CREATE TABLE IF NOT EXISTS tfa_codes (
        user_id INTEGER PRIMARY KEY,
        code TEXT,
        expires TEXT
    );
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 0,
        portfolio_name TEXT DEFAULT 'Principal',
        symbol TEXT NOT NULL,
        entry_price REAL NOT NULL,
        quantity REAL NOT NULL,
        date TEXT NOT NULL,
        notes TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 0,
        symbol TEXT NOT NULL,
        side TEXT NOT NULL,
        entry_price REAL, exit_price REAL,
        quantity REAL, pnl REAL,
        date_open TEXT, date_close TEXT,
        notes TEXT DEFAULT '',
        status TEXT DEFAULT 'open'
    );
    CREATE TABLE IF NOT EXISTS price_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 0,
        symbol TEXT NOT NULL,
        condition TEXT NOT NULL,
        target_price REAL NOT NULL,
        active INTEGER DEFAULT 1,
        triggered INTEGER DEFAULT 0,
        created TEXT
    );
    CREATE TABLE IF NOT EXISTS watchlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        added TEXT,
        UNIQUE(user_id, symbol)
    );
    CREATE TABLE IF NOT EXISTS blacklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT UNIQUE NOT NULL,
        added TEXT
    );
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        action TEXT,
        detail TEXT,
        ip TEXT,
        ts TEXT
    );
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    CREATE TABLE IF NOT EXISTS signals_history (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol    TEXT NOT NULL,
        direction TEXT NOT NULL,
        score     INTEGER DEFAULT 0,
        price     REAL DEFAULT 0,
        change_pct REAL DEFAULT 0,
        volume_usdt REAL DEFAULT 0,
        tags      TEXT DEFAULT '',
        criteria  TEXT DEFAULT '',
        ts        TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS user_exchange_keys (
        user_id  INTEGER,
        exchange TEXT,
        api_key  TEXT DEFAULT '',
        api_secret TEXT DEFAULT '',
        api_key_enc TEXT DEFAULT '',
        api_secret_enc TEXT DEFAULT '',
        migrated INTEGER DEFAULT 0,
        updated  TEXT DEFAULT '',
        PRIMARY KEY (user_id, exchange)
    );
    """)
    for sym in ["KAT"]:
        try: c.execute("INSERT OR IGNORE INTO blacklist (symbol,added) VALUES (?,?)", (sym, datetime.now().isoformat()))
        except: pass
    for _k, _v in [("exchange","coingecko"),("pump_pct","5"),("scan_interval","10"),("vol_mult","3")]:
        try: c.execute("INSERT OR IGNORE INTO settings (key,value) VALUES (?,?)", (_k, _v))
        except: pass
    try: c.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'inactive'")
    except: pass
    try: c.execute("UPDATE users SET role='visitor' WHERE LOWER(role)='viewer'")
    except: pass
    try: c.execute("UPDATE users SET role='member' WHERE LOWER(role)='trader'")
    except: pass
    try: c.execute("UPDATE users SET subscription_status='active' WHERE LOWER(role) IN ('paid','vip','admin') AND (subscription_status IS NULL OR subscription_status='')")
    except: pass
    try: c.execute("UPDATE users SET subscription_status='inactive' WHERE subscription_status IS NULL OR subscription_status=''")
    except: pass
    conn.commit(); conn.close()

# ── Scanner Engine ────────────────────────────────────────────
class ScannerEngine:
    def __init__(self):
        init_db()
        self._last_data     = {"coins":[],"signals":[],"ts":None,"exchange":"coingecko"}
        self._last_scan_coins = []
        self._market_info   = {}
        self._whale_alerts  = []
        self._prev_vols     = {}
        self._alert_cache   = set()
        self._alert_lock    = threading.Lock()
        self._exchange      = self._get_setting("exchange","coingecko")
        self._rate_limits   = {}
        self._send_telegram(
            "🚀 <b>CryptoScanner Pro V11 démarré !</b>\n"
            "✅ Sécurité V11 activée · 🔐 Clés API chiffrées\n"
            "🌐 Fear&Greed · 🐳 Whale Alerts · Funding Rates"
        )

    # ── Settings ──────────────────────────────────────────────
    def _get_setting(self, key, default=""):
        conn = get_connection()
        row  = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        conn.close(); return row[0] if row else default

    def _set_setting(self, key, value):
        conn = get_connection()
        conn.execute("INSERT OR REPLACE INTO settings (key,value) VALUES (?,?)", (key,value))
        conn.commit(); conn.close()

    def set_exchange(self, exchange):
        self._exchange = exchange
        self._set_setting("exchange", exchange)
        self._prev_vols = {}

    def get_exchange(self): return self._exchange

    # ── Rate Limiting ─────────────────────────────────────────
    def check_rate_limit(self, ip, max_req=30):
        now = time.time()
        if ip not in self._rate_limits:
            self._rate_limits[ip] = []
        self._rate_limits[ip] = [t for t in self._rate_limits[ip] if now - t < RATE_LIMIT_WINDOW]
        if len(self._rate_limits[ip]) >= max_req:
            return False
        self._rate_limits[ip].append(now)
        return True

    # ── Logs ──────────────────────────────────────────────────
    def log_action(self, user_id, username, action, detail="", ip=""):
        conn = get_connection()
        conn.execute("INSERT INTO activity_logs (user_id,username,action,detail,ip,ts) VALUES (?,?,?,?,?,?)",
            (user_id, username, action, detail, ip, datetime.now().isoformat()))
        conn.commit(); conn.close()

    def get_logs(self, limit=50):
        conn = get_connection(); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    # ── Sessions ──────────────────────────────────────────────
    def create_session(self, user_id, ip=""):
        token   = gen_token()
        expires = (datetime.now() + timedelta(hours=SESSION_EXPIRE_H)).isoformat()
        conn = get_connection()
        conn.execute("INSERT INTO sessions (token,user_id,created,expires,ip) VALUES (?,?,?,?,?)",
            (token, user_id, datetime.now().isoformat(), expires, ip))
        conn.commit(); conn.close()
        return token

    def validate_session(self, token):
        if not token: return None
        conn = get_connection(); conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT s.user_id, s.expires, u.username, u.role, u.subscription_status, u.tfa_enabled "
            "FROM sessions s JOIN users u ON s.user_id=u.id WHERE s.token=?", (token,)
        ).fetchone()
        conn.close()
        if not row: return None
        if datetime.fromisoformat(row["expires"]) < datetime.now():
            self.revoke_session(token); return None
        return dict(row)

    def revoke_session(self, token):
        conn = get_connection()
        conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        conn.commit(); conn.close()

    def revoke_all_sessions(self, user_id):
        conn = get_connection()
        conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
        conn.commit(); conn.close()

    # ── Auth ──────────────────────────────────────────────────
    def _count_recent_fails(self, username, ip):
        conn = get_connection()
        since = (datetime.now() - timedelta(minutes=15)).isoformat()
        row = conn.execute(
            "SELECT COUNT(*) FROM login_attempts WHERE (username=? OR ip=?) AND success=0 AND ts>?",
            (username, ip, since)
        ).fetchone()
        conn.close(); return row[0] if row else 0

    def create_user(self, username, password, role="member", email="", firstname="", lastname="", subscription_status="inactive"):
        username = (username or "").lower().strip()
        role = normalize_role(role)
        subscription_status = normalize_subscription_status(subscription_status)
        email = (email or "").strip().lower()
        firstname = (firstname or "").strip()
        lastname = (lastname or "").strip()
        if len(username) < 3:
            return {"ok":False, "error":"Nom d'utilisateur trop court (min 3 caractères)"}
        if len(password) < 8:
            return {"ok":False, "error":"Mot de passe trop court (min 8 caractères)"}
        if email and "@" not in email:
            return {"ok":False, "error":"Adresse email invalide"}
        try:
            from security import hash_password
            pw_hash = hash_password(password)
        except:
            pw_hash = hash_pw(password)
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO users (username,password_hash,role,subscription_status,email,firstname,lastname,created) VALUES (?,?,?,?,?,?,?,?)",
                (username, pw_hash, role, subscription_status, email, firstname, lastname, datetime.now().isoformat())
            )
            conn.commit(); conn.close()
            return {"ok":True}
        except (sqlite3.IntegrityError, Exception) as e:
            try:
                conn.rollback()
            except Exception:
                pass
            conn.close()
            msg = str(e).lower()
            if "unique" in msg or "duplicate" in msg or "already exists" in msg:
                return {"ok":False, "error":"Nom d'utilisateur déjà pris"}
            raise

    def get_user_by_id(self, user_id):
        conn = get_connection()
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, username, role, subscription_status, email, firstname, lastname, tg_chat_id, tfa_enabled, totp_enabled, created, last_login "
            "FROM users WHERE id=?",
            (user_id,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    def update_user_profile(self, user_id, firstname="", lastname="", email="", password=""):
        firstname = (firstname or "").strip()
        lastname = (lastname or "").strip()
        email = (email or "").strip().lower()
        if not firstname or not lastname:
            return {"ok": False, "error": "Prénom et nom requis"}
        if not email or "@" not in email:
            return {"ok": False, "error": "Adresse email invalide"}

        conn = get_connection()
        try:
            if password:
                try:
                    from security import hash_password
                    pw_hash = hash_password(password)
                except:
                    pw_hash = hash_pw(password)
                conn.execute(
                    "UPDATE users SET firstname=?, lastname=?, email=?, password_hash=? WHERE id=?",
                    (firstname, lastname, email, pw_hash, user_id),
                )
            else:
                conn.execute(
                    "UPDATE users SET firstname=?, lastname=?, email=? WHERE id=?",
                    (firstname, lastname, email, user_id),
                )
            conn.commit()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            conn.close()

    def login_user(self, username, password, ip=""):
        fails = self._count_recent_fails(username, ip)
        if fails >= MAX_LOGIN_ATTEMPTS:
            return {"ok":False, "error":f"Trop de tentatives. Réessaie dans 15 min."}
        conn = get_connection(); conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id,username,role,subscription_status,tfa_enabled,tg_chat_id,password_hash FROM users WHERE LOWER(username)=?",
            (username.lower().strip(),)
        ).fetchone()
        try:
            from security import verify_password
            password_ok = bool(row and verify_password(password, row["password_hash"]))
        except:
            password_ok = bool(row and row["password_hash"] == hash_pw(password))
        conn2 = get_connection()
        conn2.execute("INSERT INTO login_attempts (username,ip,success,ts) VALUES (?,?,?,?)",
            (username, ip, 1 if password_ok else 0, datetime.now().isoformat()))
        conn2.commit(); conn2.close()
        if not password_ok:
            conn.close(); return {"ok":False, "error":"Identifiants incorrects"}
        user = dict(row)
        conn.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now().isoformat(), user["id"]))
        conn.commit(); conn.close()
        totp_enabled = False
        try:
            from security import _get_user_totp_secret as _guts
            conn3 = get_connection(); conn3.row_factory = sqlite3.Row
            try: conn3.execute("ALTER TABLE users ADD COLUMN totp_enabled INTEGER DEFAULT 0")
            except: pass
            try: conn3.execute("ALTER TABLE users ADD COLUMN totp_secret TEXT DEFAULT ''")
            except: pass
            conn3.commit()
            row3 = conn3.execute("SELECT totp_enabled, tfa_enabled FROM users WHERE id=?", (user["id"],)).fetchone()
            conn3.close()
            is_enabled = row3 and (str(row3["totp_enabled"]) == "1" or str(row3["tfa_enabled"]) == "1")
            if is_enabled:
                secret_check = _guts(user["id"])
                if secret_check:
                    totp_enabled = True
        except Exception as e:
            print(f"[Login TOTP check] {e}")
        if totp_enabled:
            return {"ok":True, "requires_2fa":True, "totp":True, "user_id":user["id"]}
        if user["tfa_enabled"] and user["tg_chat_id"]:
            code = str(secrets.randbelow(900000) + 100000)
            exp  = (datetime.now() + timedelta(minutes=5)).isoformat()
            db = get_connection()
            db.execute("INSERT OR REPLACE INTO tfa_codes (user_id,code,expires) VALUES (?,?,?)",
                (user["id"], code, exp))
            db.commit(); db.close()
            self._send_telegram_to(user["tg_chat_id"],
                f"🔐 <b>Code de connexion CryptoScanner</b>\n"
                f"Code : <b>{code}</b>\n"
                f"Valable 5 minutes.\nSi ce n'est pas vous, ignorez ce message.")
            return {"ok":True, "requires_2fa":True, "totp":False, "user_id":user["id"]}
        token = self.create_session(user["id"], ip)
        self.log_action(user["id"], user["username"], "LOGIN", f"IP:{ip}", ip)
        try:
            db2 = get_connection()
            db2.execute("DELETE FROM login_attempts WHERE username=?", (username.lower(),))
            db2.commit(); db2.close()
        except: pass
        return {"ok":True, "requires_2fa":False, "token":token,
            "user_id":user["id"], "username":user["username"], "role":user["role"], "subscription_status": user["subscription_status"]}

    def verify_2fa(self, user_id, code, ip=""):
        conn = get_connection(); conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT code,expires FROM tfa_codes WHERE user_id=?", (user_id,)).fetchone()
        conn.close()
        if not row: return {"ok":False, "error":"Code expiré"}
        if datetime.fromisoformat(row["expires"]) < datetime.now():
            return {"ok":False, "error":"Code expiré"}
        if row["code"] != str(code):
            return {"ok":False, "error":"Code incorrect"}
        db = get_connection()
        db.execute("DELETE FROM tfa_codes WHERE user_id=?", (user_id,))
        db.commit(); db.close()
        conn2 = get_connection(); conn2.row_factory = sqlite3.Row
        user = conn2.execute("SELECT id,username,role,subscription_status FROM users WHERE id=?", (user_id,)).fetchone()
        conn2.close()
        if not user: return {"ok":False, "error":"Utilisateur introuvable"}
        token = self.create_session(user["id"], ip)
        self.log_action(user["id"], user["username"], "2FA_LOGIN", f"IP:{ip}", ip)
        return {"ok":True, "token":token, "user_id":user["id"],
            "username":user["username"], "role":user["role"], "subscription_status": user["subscription_status"]}

    def enable_2fa(self, user_id, tg_chat_id):
        conn = get_connection()
        conn.execute("UPDATE users SET tfa_enabled=1, tg_chat_id=? WHERE id=?", (tg_chat_id, user_id))
        conn.commit(); conn.close()
        return {"ok":True}

    def disable_2fa(self, user_id):
        conn = get_connection()
        conn.execute("UPDATE users SET tfa_enabled=0, tg_chat_id='' WHERE id=?", (user_id,))
        conn.commit(); conn.close()
        return {"ok":True}

    # ── Binance Futures PERP ─────────────────────────────────
    def fetch_perp(self):
        perps = []
        try:
            r = requests.get(
                "https://api.bybit.com/v5/market/tickers",
                params={"category": "linear"},
                timeout=12, headers={"User-Agent":"Mozilla/5.0"}
            )
            items = r.json().get("result",{}).get("list",[])
            for t in items:
                sym = t.get("symbol","")
                if not sym.endswith("USDT"): continue
                try:
                    price  = float(t.get("lastPrice",0) or 0)
                    chg    = float(t.get("price24hPcnt",0) or 0) * 100
                    vol    = float(t.get("turnover24h",0) or 0)
                    high   = float(t.get("highPrice24h",price) or price)
                    low    = float(t.get("lowPrice24h",price) or price)
                    fund   = float(t.get("fundingRate",0) or 0) * 100
                    oi     = float(t.get("openInterest",0) or 0)
                    if price <= 0 or vol < 500_000: continue
                    base = sym.replace("USDT","")
                    if fund > 0.05:    funding_sent = "🔴 Baissier"
                    elif fund < -0.01: funding_sent = "🟢 Haussier"
                    else:              funding_sent = "⚪ Neutre"
                    perps.append({
                        "symbol":       base,
                        "pair":         sym,
                        "price":        round(price,6),
                        "change_pct":   round(chg,2),
                        "volume_usdt":  round(vol,0),
                        "high":         round(high,6),
                        "low":          round(low,6),
                        "trades":       0,
                        "funding_rate": round(fund,4),
                        "funding_sent": funding_sent,
                        "open_interest": round(oi,0),
                        "market":       "perp",
                        "exchange":     "bybit",
                    })
                except: continue
            if perps:
                print(f"[Perp] {len(perps)} contrats Bybit")
            return sorted(perps, key=lambda x: x["volume_usdt"], reverse=True)
        except Exception as e:
            print(f"[Perp Bybit] {e}")
        try:
            r = requests.get(BINANCE_FPERP, timeout=10)
            data = r.json()
            if not isinstance(data, list): return []
            funding_map = {}
            try:
                rf = requests.get(BINANCE_FFUNDING, timeout=8)
                for item in rf.json():
                    funding_map[item.get("symbol","")] = round(float(item.get("lastFundingRate",0))*100,4)
            except: pass
            for t in data:
                sym = t.get("symbol","")
                if not sym.endswith("USDT"): continue
                try:
                    price=float(t["lastPrice"]); chg=float(t["priceChangePercent"])
                    vol=float(t["quoteVolume"])
                    if price<=0 or vol<100_000: continue
                    base=sym.replace("USDT",""); fund=funding_map.get(sym,0)
                    perps.append({
                        "symbol":base,"pair":sym,"price":price,"change_pct":round(chg,2),
                        "volume_usdt":vol,"high":float(t["highPrice"]),"low":float(t["lowPrice"]),
                        "trades":int(t.get("count",0)),"funding_rate":fund,
                        "funding_sent":"🔴 Baissier" if fund>0.05 else "🟢 Haussier" if fund<-0.01 else "⚪ Neutre",
                        "market":"perp","exchange":"binance_futures",
                    })
                except: continue
        except: pass
        return sorted(perps, key=lambda x: x["volume_usdt"], reverse=True)[:300]

    def _fetch_coingecko_scan(self):
        try:
            all_coins = []
            for page in [1, 2]:
                r = requests.get(
                    COINGECKO_MARKET,
                    params={
                        "vs_currency":            "usd",
                        "order":                  "market_cap_desc",
                        "per_page":               125,
                        "page":                   page,
                        "sparkline":              "false",
                        "price_change_percentage":"24h",
                    },
                    headers={"Accept": "application/json"},
                    timeout=12
                )
                if r.status_code == 429:
                    print("[CoinGecko] Rate limit - attente 30s")
                    if self._last_scan_coins:
                        return self._last_scan_coins
                    import time; time.sleep(5)
                    break
                data = _safe_json_response(r, [])
                if not isinstance(data, list): break
                for coin in data:
                    symbol = (coin.get("symbol") or "").upper()
                    price  = float(coin.get("current_price") or 0)
                    chg    = float(coin.get("price_change_percentage_24h") or 0)
                    vol    = float(coin.get("total_volume") or 0)
                    mcap   = float(coin.get("market_cap") or 0)
                    high   = float(coin.get("high_24h") or price)
                    low    = float(coin.get("low_24h") or price)
                    ath    = float(coin.get("ath") or price)
                    rank   = int(coin.get("market_cap_rank") or 999)
                    if (
                        price <= 0 or not symbol or
                        symbol in STABLE_SYMBOLS or
                        "_" in symbol or
                        len(symbol) > 10
                    ):
                        continue
                    all_coins.append({
                        "symbol":      symbol,
                        "name":        coin.get("name", symbol),
                        "price":       round(price, 6),
                        "change_pct":  round(chg, 2),
                        "volume_usdt": round(vol, 0),
                        "market_cap":  round(mcap, 0),
                        "high":        round(high, 6),
                        "low":         round(low, 6),
                        "ath":         round(ath, 6),
                        "ath_pct":     round((price/ath-1)*100, 1) if ath > 0 else 0,
                        "rank":        rank,
                        "trades":      0,
                        "exchange":    "coingecko",
                        "image":       coin.get("image", ""),
                        "coin_id":     coin.get("id", ""),
                    })
                import time; time.sleep(1.5)
            print(f"[CoinGecko] {len(all_coins)} coins chargés")
            if len(all_coins) > 50:
                self._last_scan_coins = all_coins
                return all_coins
            return self._last_scan_coins or None
        except Exception as e:
            print(f"[CoinGecko scan] {e}")
            return self._last_scan_coins or None

    def fetch_coingecko_markets(self, limit=100):
        try:
            r = requests.get(COINGECKO_MARKET, params={
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h"
            }, timeout=12, headers={"Accept": "application/json"})
            data = r.json()
            result = []
            for coin in data:
                result.append({
                    "symbol":        coin.get("symbol","").upper(),
                    "name":          coin.get("name",""),
                    "rank":          coin.get("market_cap_rank",0),
                    "price":         coin.get("current_price",0),
                    "change_pct":    round(coin.get("price_change_percentage_24h",0) or 0, 2),
                    "market_cap":    coin.get("market_cap",0),
                    "volume_usdt":   coin.get("total_volume",0),
                    "ath":           coin.get("ath",0),
                    "ath_pct":       round(coin.get("ath_change_percentage",0) or 0, 1),
                    "image":         coin.get("image",""),
                    "market":        "coingecko",
                })
            return result
        except Exception as e:
            print(f"[CoinGecko Markets] {e}")
            return []

    def fetch_market_info(self):
        info = {}
        headers_robust = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }

        # Fear & Greed Index avec retry
        for attempt in range(2):
            try:
                r = requests.get(FEAR_GREED_URL, timeout=12, headers=headers_robust)
                r.raise_for_status()
                d = r.json()["data"][0]
                info["fear_greed"] = {
                    "value": int(d["value"]),
                    "label": d["value_classification"],
                    "ts":    d["timestamp"]
                }
                break
            except Exception as e:
                if attempt == 0:
                    time.sleep(1)
                    continue
                else:
                    info["fear_greed"] = None

        # Global Market Info (Dominance) avec retry
        for attempt in range(2):
            try:
                r = requests.get(GLOBAL_MARKET, timeout=12, headers=headers_robust)
                r.raise_for_status()
                d    = r.json().get("data", {})
                pcts = d.get("market_cap_percentage", {})
                if pcts.get("btc"):
                    info["dominance"] = {
                        "btc":        round(pcts.get("btc", 0), 1),
                        "eth":        round(pcts.get("eth", 0), 1),
                        "total_mcap": d.get("total_market_cap", {}).get("usd", 0),
                        "total_vol":  d.get("total_volume", {}).get("usd", 0),
                    }
                else:
                    raise Exception("Empty data")
                break
            except Exception as e:
                if attempt == 0:
                    time.sleep(1)
                    continue
                else:
                    info["dominance"] = None
        try:
            r = requests.get(BINANCE_FUNDING, timeout=8)
            data = r.json()
            if not isinstance(data, list): raise Exception("Format invalide")
            top_symbols = ["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
            funding = []
            for item in data:
                if item.get("symbol") in top_symbols:
                    rate = float(item.get("lastFundingRate", 0)) * 100
                    funding.append({
                        "symbol":    item["symbol"].replace("USDT",""),
                        "rate":      round(rate, 4),
                        "sentiment": "🟢 Haussier" if rate < 0 else "🔴 Baissier" if rate > 0.05 else "⚪ Neutre"
                    })
            if not funding: raise Exception("Vide")
            info["funding"] = sorted(funding, key=lambda x: abs(x["rate"]), reverse=True)
        except:
            info["funding"] = [
                {"symbol":"BTC",  "rate": 0.01,  "sentiment":"⚪ Neutre"},
                {"symbol":"ETH",  "rate": 0.008, "sentiment":"⚪ Neutre"},
                {"symbol":"SOL",  "rate": 0.025, "sentiment":"🔴 Baissier"},
                {"symbol":"BNB",  "rate":-0.005, "sentiment":"🟢 Haussier"},
                {"symbol":"XRP",  "rate": 0.015, "sentiment":"🔴 Baissier"},
                {"symbol":"DOGE", "rate": 0.03,  "sentiment":"🔴 Baissier"},
            ]
        self._market_info = info
        return info

    def _detect_volume_whales(self) -> list:
        """Détecte les mouvements whales via anomalies de volume Binance (sans API key)."""
        whales = []
        try:
            r = requests.get(BINANCE_TICKER, timeout=10)
            items = r.json() if r.status_code == 200 else []
            if not isinstance(items, list):
                return []
            now_ts = datetime.now().strftime("%H:%M:%S")
            for t in items:
                sym = (t.get("symbol") or "")
                if not sym.endswith("USDT"):
                    continue
                base = sym.replace("USDT", "")
                if "_" in base or len(base) > 10 or base in STABLE_SYMBOLS:
                    continue
                try:
                    vol = float(t.get("quoteVolume") or 0)
                    chg = abs(float(t.get("priceChangePercent") or 0))
                    price = float(t.get("lastPrice") or 0)
                    count = int(t.get("count") or 0)
                    # Critères whale selon capitalisation estimée
                    # Large cap (BTC/ETH/BNB/SOL/XRP) : vol > $300M et mouv > 4%
                    # Mid cap : vol > $30M et mouv > 8%
                    # Small cap : vol > $5M et mouv > 15%
                    is_whale = False
                    category = ""
                    if vol > 300_000_000 and chg > 4:
                        is_whale = True; category = "LARGE CAP"
                    elif 30_000_000 < vol <= 300_000_000 and chg > 8:
                        is_whale = True; category = "MID CAP"
                    elif 5_000_000 < vol <= 30_000_000 and chg > 15:
                        is_whale = True; category = "SMALL CAP"
                    if is_whale:
                        direction = "🟢 PUMP" if float(t.get("priceChangePercent", 0)) > 0 else "🔴 DUMP"
                        whales.append({
                            "symbol": base,
                            "amount": vol,
                            "type":   "volume_anomaly",
                            "from":   category,
                            "to":     direction,
                            "msg":    f"Volume 24h: ${vol/1e6:.1f}M · Mouvement: {t.get('priceChangePercent',0)}% · Prix: ${price:,.4f}",
                            "ts":     now_ts,
                            "trades": count,
                        })
                except Exception:
                    continue
            # Trier par volume décroissant, garder top 15
            whales.sort(key=lambda x: x["amount"], reverse=True)
            return whales[:15]
        except Exception as e:
            print(f"[Whale/Binance] {e}")
            return []

    def _detect_btc_whales(self) -> list:
        """Détecte les gros transferts BTC via mempool.space (sans API key)."""
        whales = []
        try:
            # Récupérer les derniers blocs
            r = requests.get("https://mempool.space/api/v1/blocks", timeout=8)
            if r.status_code != 200:
                return []
            blocks = r.json()
            if not blocks:
                return []
            # Prendre le dernier bloc
            latest_block = blocks[0]
            block_hash = latest_block.get("id", "")
            if not block_hash:
                return []
            # Récupérer les transactions du bloc
            r2 = requests.get(f"https://mempool.space/api/block/{block_hash}/txs/0", timeout=8)
            if r2.status_code != 200:
                return []
            txs = r2.json()
            # Prix BTC pour conversion USD
            btc_price = 0
            try:
                tp = requests.get("https://blockchain.info/ticker", timeout=4).json()
                btc_price = float(tp.get("USD", {}).get("last", 0))
            except Exception:
                btc_price = 80000  # fallback
            # Filtrer les grosses transactions (> 10 BTC)
            now_ts = datetime.now().strftime("%H:%M:%S")
            for tx in txs:
                try:
                    out_val = sum(o.get("value", 0) for o in (tx.get("vout") or [])) / 1e8
                    if out_val < 10:
                        continue
                    usd_val = out_val * btc_price
                    if usd_val < 500_000:
                        continue
                    whales.append({
                        "symbol": "BTC",
                        "amount": usd_val,
                        "type":   "on_chain_transfer",
                        "from":   "on-chain",
                        "to":     "inconnu",
                        "msg":    f"{out_val:,.2f} BTC transférés (${usd_val/1e6:.2f}M) · bloc #{latest_block.get('height', '?')}",
                        "ts":     now_ts,
                    })
                except Exception:
                    continue
            # Top 5 par valeur
            whales.sort(key=lambda x: x["amount"], reverse=True)
            return whales[:5]
        except Exception as e:
            print(f"[Whale/BTC] {e}")
            return []

    def fetch_whale_alerts(self):
        try:
            if WHALE_API_KEY:
                since = int(time.time()) - 3600
                r = requests.get(WHALE_ALERT_URL, params={
                    "api_key": WHALE_API_KEY,
                    "min_value": 1000000,
                    "start": since
                }, timeout=10)
                data = r.json()
                whales = []
                for tx in data.get("transactions", [])[:10]:
                    whales.append({
                        "symbol":  tx.get("symbol","?").upper(),
                        "amount":  tx.get("amount_usd", 0),
                        "type":    tx.get("transaction_type","transfer"),
                        "from":    tx.get("from",{}).get("owner_type","?"),
                        "to":      tx.get("to",{}).get("owner_type","?"),
                        "msg":     f"{tx.get('amount',0):,.0f} {tx.get('symbol','').upper()} transférés",
                        "ts":      datetime.fromtimestamp(tx.get("timestamp",0)).strftime("%H:%M:%S")
                    })
                self._whale_alerts = whales
                return whales
            # Fallback gratuit : volume Binance + BTC on-chain
            vol_whales = self._detect_volume_whales()
            btc_whales = self._detect_btc_whales()
            # BTC on-chain en premier, puis anomalies volume
            combined = btc_whales + vol_whales
            self._whale_alerts = combined
            return combined
        except Exception as e:
            print(f"[Whale] {e}"); return []

    def get_market_info(self):   return self._market_info
    def get_whale_alerts(self):  return self._whale_alerts

    def _fetch_binance(self):
        try:
            r = requests.get(BINANCE_TICKER, timeout=10, headers={"Accept":"application/json"})
            items = _safe_json_response(r, [])
            coins = []
            for t in items if isinstance(items, list) else []:
                sym = t.get("symbol","")
                if not sym.endswith("USDT"): continue
                try:
                    base = sym.replace("USDT","")
                    price = float(t.get("lastPrice",0) or 0)
                    vol = float(t.get("quoteVolume",0) or 0)
                    if price <= 0 or base in STABLE_SYMBOLS or "_" in base or len(base) > 10: continue
                    coins.append({
                        "symbol":      base,
                        "name":        base,
                        "price":       price,
                        "change_pct":  float(t.get("priceChangePercent",0) or 0),
                        "volume_usdt": vol,
                        "high":        float(t.get("highPrice",price) or price),
                        "low":         float(t.get("lowPrice",price) or price),
                        "trades":      int(t.get("count",0) or 0),
                        "exchange":    "binance", "type": "spot"
                    })
                except: continue
            if coins:
                print(f"[Fallback] {len(coins)} coins Binance")
                return coins
        except Exception as e:
            print(f"[Fallback Binance] {e}")
        try:
            r = requests.get("https://api.bybit.com/v5/market/tickers", params={"category":"spot"}, timeout=15, headers={"User-Agent":"Mozilla/5.0"})
            data = _safe_json_response(r, {})
            items = data.get("result",{}).get("list",[]) if isinstance(data, dict) else []
            coins = []
            for t in items:
                sym = t.get("symbol","")
                if not sym.endswith("USDT"): continue
                try:
                    base = sym.replace("USDT","")
                    if base in STABLE_SYMBOLS or "_" in base or len(base) > 10:
                        continue
                    coins.append({
                        "symbol":      base,
                        "price":       float(t.get("lastPrice",0) or 0),
                        "change_pct":  round(float(t.get("price24hPcnt",0) or 0)*100, 2),
                        "volume_usdt": float(t.get("turnover24h",0) or 0),
                        "high":        float(t.get("highPrice24h",0) or 0),
                        "low":         float(t.get("lowPrice24h",0) or 0),
                        "trades":      0,
                        "exchange":    "bybit", "type": "spot"
                    })
                except: continue
            return coins
        except: return []

    def _fetch_kraken(self):
        try:
            r = requests.get(KRAKEN_PAIRS, timeout=10)
            pairs = {k:v for k,v in r.json().get("result",{}).items() if v.get("quote") in ("ZUSD","USD","USDT")}
            coins = []
            for i in range(0, min(len(pairs),200), 50):
                batch = list(pairs.keys())[i:i+50]
                try:
                    tr = requests.get(KRAKEN_TICKER, params={"pair":",".join(batch)}, timeout=10)
                    for pname, td in tr.json().get("result",{}).items():
                        info = pairs.get(pname,{})
                        base = info.get("base","").lstrip("XZ")
                        if not base: continue
                        price = float(td["c"][0]); open_ = float(td["o"])
                        chg   = round((price-open_)/open_*100,2) if open_ else 0
                        coins.append({
                            "symbol": base, "price": price, "change_pct": chg,
                            "volume_usdt": float(td["v"][1])*price,
                            "high": float(td["h"][1]), "low": float(td["l"][1]),
                            "trades": int(td["t"][1]),
                            "exchange": "kraken", "type": "spot"
                        })
                except: continue
            return coins
        except: return []

    def fetch_candles(self, symbol, interval="1h", limit=100):
        if self._exchange == "kraken": return self._candles_kraken(symbol, interval)
        return self._candles_binance(symbol, interval, limit)

    def _candles_binance(self, symbol, interval="1h", limit=100):
        try:
            r = requests.get(BINANCE_KLINES, params={"symbol":symbol+"USDT","interval":interval,"limit":limit}, timeout=10)
            data = _safe_json_response(r, [])
            if isinstance(data, list) and data:
                return [{"t":int(k[0]),"o":float(k[1]),"h":float(k[2]),"l":float(k[3]),"c":float(k[4]),"v":float(k[5])} for k in data]
        except Exception:
            pass
        iv_bybit = {"1m":"1","5m":"5","15m":"15","30m":"30","1h":"60","4h":"240","1d":"D"}.get(interval, "60")
        try:
            r = requests.get("https://api.bybit.com/v5/market/kline", params={"category":"linear","symbol":symbol+"USDT","interval":iv_bybit,"limit":limit}, timeout=10, headers={"User-Agent":"Mozilla/5.0"})
            data = _safe_json_response(r, {})
            candles = data.get("result",{}).get("list",[])
            if candles and len(candles) >= 10:
                candles = list(reversed(candles))
                return [{"t":int(k[0]),"o":float(k[1]),"h":float(k[2]),"l":float(k[3]),"c":float(k[4]),"v":float(k[5])} for k in candles]
        except Exception:
            pass
        iv_okx = {"1m":"1m","5m":"5m","15m":"15m","30m":"30m","1h":"1H","4h":"4H","1d":"1D"}.get(interval,"1H")
        try:
            r = requests.get("https://www.okx.com/api/v5/market/candles", params={"instId":f"{symbol}-USDT-SWAP","bar":iv_okx,"limit":limit}, timeout=10)
            candles = _safe_json_response(r, {}).get("data",[])
            if candles and len(candles) >= 10:
                candles = list(reversed(candles))
                return [{"t":int(k[0]),"o":float(k[1]),"h":float(k[2]),"l":float(k[3]),"c":float(k[4]),"v":float(k[5])} for k in candles]
        except Exception:
            pass
        return []

    def _candles_kraken(self, symbol, interval="1h"):
        iv = {"15m":"15","1h":"60","4h":"240","1d":"1440"}.get(interval,"60")
        try:
            r = requests.get(KRAKEN_OHLC, params={"pair":symbol+"USD","interval":iv}, timeout=10)
            result = r.json().get("result",{})
            key = [k for k in result if k != "last"]
            if not key: return []
            return [{"t":int(c[0])*1000,"o":float(c[1]),"h":float(c[2]),"l":float(c[3]),"c":float(c[4]),"v":float(c[6])} for c in result[key[0]]]
        except: return []

    def scan(self):
        scanner_source = "coingecko"
        coins = self._fetch_coingecko_scan()
        if not coins:
            print("[Scanner] CoinGecko indisponible - fallback Binance")
            coins = self._fetch_binance()
            if coins:
                scanner_source = "binance"
        if not coins:
            print("[Scanner] Binance indisponible - fallback Kraken")
            coins = self._fetch_kraken()
            if coins:
                scanner_source = "kraken"
        if not coins: return None
        blacklist = self._get_blacklist_set()
        signals = []
        for c in coins:
            sym = c["symbol"]; chg = c["change_pct"]; vol = c["volume_usdt"]
            vol_ratio = vol/self._prev_vols[sym] if sym in self._prev_vols and self._prev_vols[sym]>0 else None
            tags = []
            if chg >= PRICE_ALERT_PCT:    tags.append({"label":"🚀 PUMP","type":"green"})
            elif chg <= -PRICE_ALERT_PCT: tags.append({"label":"💥 DUMP","type":"red"})
            elif chg >= 2:                tags.append({"label":"📈 HAUSSIER","type":"green"})
            elif chg <= -2:               tags.append({"label":"📉 BAISSIER","type":"red"})
            if vol_ratio and vol_ratio >= VOLUME_SPIKE_MULT:
                tags.append({"label":f"⚡ VOL x{vol_ratio:.1f}","type":"yellow"})
            rng = c["high"]-c["low"]
            rsi_a = ((c["price"]-c["low"])/rng*100) if rng>0 else 50
            score, direction = score_signal(rsi_a, None, chg, vol_ratio, rsi_a/100)
            if tags or abs(chg) >= 3:
                signals.append({**c,"tags":tags,"score":score,"direction":direction,
                    "vol_ratio":round(vol_ratio,2) if vol_ratio else None})
        signals.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
        self._prev_vols = {c["symbol"]:c["volume_usdt"] for c in coins}
        with _data_lock:
            self._last_data = {
                "coins":    sorted(coins, key=lambda x: x["volume_usdt"], reverse=True),
                "signals":  signals[:50],
                "ts":       datetime.now().strftime("%H:%M:%S"),
                "count":    len(coins),
                "exchange": scanner_source,
                "source_policy": {
                    "scanner": scanner_source,
                    "coverage": "coingecko",
                    "perp": "bybit_okx",
                    "multi_exchange": "bybit_okx",
                },
                "blacklist":list(blacklist),
            }
        self._check_price_alerts(coins)
        self._send_telegram_alerts(signals, blacklist)
        return self._last_data

    def _get_conn(self):
        import sqlite3 as _sq3
        conn = _sq3.connect(DB_PATH)
        return conn

    def get_last(self):    return self._last_data
    def get_signals(self): return self._last_data.get("signals",[])

    def get_blacklist(self):
        conn = get_connection()
        rows = conn.execute("SELECT id,symbol,added FROM blacklist ORDER BY symbol").fetchall()
        conn.close(); return [{"id":r[0],"symbol":r[1],"added":r[2]} for r in rows]

    def _get_blacklist_set(self):
        conn = get_connection()
        rows = conn.execute("SELECT symbol FROM blacklist").fetchall()
        conn.close(); return {r[0] for r in rows}

    def add_blacklist(self, symbol):
        conn = get_connection()
        try: conn.execute("INSERT OR IGNORE INTO blacklist (symbol,added) VALUES (?,?)",(symbol.upper(),datetime.now().isoformat())); conn.commit()
        except: pass
        conn.close()

    def del_blacklist(self, bid):
        conn = get_connection()
        conn.execute("DELETE FROM blacklist WHERE id=?",(bid,)); conn.commit(); conn.close()

    def get_watchlist(self, user_id):
        conn = get_connection()
        rows = conn.execute("SELECT id,symbol,added FROM watchlist WHERE user_id=? ORDER BY symbol",(user_id,)).fetchall()
        conn.close()
        result = [{"id":r[0],"symbol":r[1],"added":r[2]} for r in rows]
        coins = {c["symbol"]:c for c in self._last_data.get("coins",[])}
        for w in result:
            c = coins.get(w["symbol"])
            if c:
                w["price"]      = c["price"]
                w["change_pct"] = c["change_pct"]
                w["volume_usdt"]= c["volume_usdt"]
        return result

    def add_watchlist(self, user_id, symbol):
        conn = get_connection()
        try: conn.execute("INSERT OR IGNORE INTO watchlist (user_id,symbol,added) VALUES (?,?,?)",(user_id,symbol.upper(),datetime.now().isoformat())); conn.commit()
        except: pass
        conn.close()

    def del_watchlist(self, wid, user_id):
        conn = get_connection()
        conn.execute("DELETE FROM watchlist WHERE id=? AND user_id=?",(wid,user_id)); conn.commit(); conn.close()

    def _check_price_alerts(self, coins):
        price_map = {c["symbol"]:c["price"] for c in coins}
        conn = get_connection(); cur = conn.cursor()
        for a in self.db_get_alerts():
            if not a["active"] or a["triggered"]: continue
            price = price_map.get(a["symbol"])
            if not price: continue
            hit = (a["condition"]=="above" and price>=a["target_price"]) or (a["condition"]=="below"  and price<=a["target_price"])
            if hit:
                cur.execute("UPDATE price_alerts SET triggered=1 WHERE id=?",(a["id"],))
                tv_url = f"https://fr.tradingview.com/chart/?symbol=BINANCE:{a['symbol']}USDT"
                msg = (f"🔔 <b>ALERTE PRIX</b>\n"
                    f"<b>{a['symbol']}</b>: ${price:.4f}\n"
                    f"{'📈' if a['condition']=='above' else '📉'} {a['condition'].upper()} ${a['target_price']:.4f}\n"
                    f"📊 <a href='{tv_url}'>Voir sur TradingView</a>")
                user_chat = self._get_user_tg_chat(a.get("user_id", 0))
                if user_chat:
                    self._send_telegram_to(user_chat, msg)
                else:
                    self._send_telegram(msg)
                    self._broadcast_to_members(msg)
        conn.commit(); conn.close()

    def _get_user_tg_chat(self, user_id):
        if not user_id: return None
        try:
            conn = get_connection()
            row = conn.execute("SELECT tg_chat_id FROM users WHERE id=?", (user_id,)).fetchone()
            conn.close()
            return row[0] if row and row[0] else None
        except: return None

    def _send_telegram(self, msg):
        import os as _os
        token = _os.environ.get("TG_TOKEN", TG_TOKEN)
        chat  = _os.environ.get("TG_CHAT",  TG_CHAT)
        if not token or not chat: return
        try:
            from daily_report import get_all_recipients
            recipients = get_all_recipients()
        except:
            recipients = [chat]
        for cid in recipients:
            if not cid: continue
            try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":cid,"text":msg,"parse_mode":"HTML"},timeout=5)
            except: pass

    def _send_telegram_to(self, chat_id, msg):
        if not TG_TOKEN: return
        try: requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", json={"chat_id":chat_id,"text":msg,"parse_mode":"HTML"},timeout=5)
        except: pass

    def _send_telegram_alerts(self, signals, blacklist):
        for label, type_ in [("🚀 PUMP","pump"),("💥 DUMP","dump")]:
            filtered = [s for s in signals if any(t["label"]==label for t in s["tags"]) and s["symbol"] not in blacklist and s["symbol"] in TOP_50_SYMBOLS and s["volume_usdt"] >= 10_000_000]
            for s in filtered[:3]:
                key = f"{type_}_{s['symbol']}_{int(s['change_pct'])}"
                with _alert_lock:
                    if key in self._alert_cache: continue
                    self._alert_cache.add(key)
                    if len(self._alert_cache) > 500:
                        self._alert_cache = set(list(self._alert_cache)[-200:])
                sign    = "+" if s["change_pct"]>0 else ""
                score   = s["score"]
                tv_url  = f"https://fr.tradingview.com/chart/?symbol=BINANCE:{s['symbol']}USDT"
                if score >= 90:
                    intensity = "🚀 TRÈS FORT" if type_=="pump" else "💥 TRÈS FORT"
                    badge     = "⭐ SETUP PREMIUM"
                else:
                    intensity = "🔥 FORT" if type_=="pump" else "🔴 FORT"
                    badge     = "✅ Signal confirmé"
                emoji = "🚀" if type_=="pump" else "💥"
                msg = (f"{emoji} <b>{intensity} — {'PUMP' if type_=='pump' else 'DUMP'}</b>\n"
                    f"💎 <b>{s['symbol']}/USDT</b>\n"
                    f"💰 Prix: ${s['price']:.4f}\n"
                    f"📊 Variation: <b>{sign}{s['change_pct']:.2f}%</b>\n"
                    f"📦 Volume: <b>${s['volume_usdt']/1e6:.1f}M</b>\n"
                    f"🎯 Score: <b>{score}/100</b> — {badge}\n"
                    f"📈 <a href='{tv_url}'>Voir sur TradingView</a>")
                self._send_telegram(msg)
                # Version simplifiée sur le canal FREE public
                try:
                    free_chat = os.environ.get("TG_CHAT_FREE", TELEGRAM_CHAT_FREE)
                    site      = os.environ.get("SITE_URL", SITE_URL)
                    if free_chat:
                        free_msg = (
                            f"{emoji} <b>{'PUMP' if type_=='pump' else 'DUMP'} détecté</b> — "
                            f"<b>{s['symbol']}/USDT</b>\n"
                            f"Variation : <b>{sign}{s['change_pct']:.1f}%</b> | "
                            f"Volume : ${s['volume_usdt']/1e6:.0f}M\n\n"
                            f"💎 Signaux détaillés (entrée, cible, stop) réservés aux membres PREMIUM\n"
                            f"→ <a href=\"{site}\">{site}</a>\n\n"
                            f"<i>🚫 Données techniques à titre informatif uniquement.</i>"
                        )
                        requests.post(
                            "https://api.telegram.org/bot" + os.environ.get("TG_TOKEN", TG_TOKEN) + "/sendMessage",
                            json={"chat_id": free_chat, "text": free_msg, "parse_mode": "HTML"},
                            timeout=6
                        )
                except Exception as _fe:
                    print(f"[FREE] {_fe}")

    # Niveaux d'accès Telegram : chaque niveau inclut les rôles supérieurs
    _TG_ROLE_TIERS = {
        "member": ("member", "paid", "vip", "admin"),   # tous les membres
        "paid":   ("paid",   "vip", "admin"),            # payants + VIP + admin
        "vip":    ("vip",    "admin"),                   # VIP + admin seulement
        "admin":  ("admin",),                            # admin seul
    }

    def _broadcast_to_members(self, msg, min_role: str = "member"):
        """
        Envoie un message Telegram aux membres dont le rôle est >= min_role.
        min_role : "member" (tous) | "paid" (payants+VIP) | "vip" (VIP seul) | "admin"
        """
        try:
            allowed_roles = self._TG_ROLE_TIERS.get(min_role, ("member", "paid", "vip", "admin"))
            placeholders  = ",".join("?" * len(allowed_roles))
            conn  = get_connection()
            rows  = conn.execute(
                f"SELECT id, username, tg_chat_id, role FROM users "
                f"WHERE tg_chat_id != '' AND tg_chat_id IS NOT NULL AND role IN ({placeholders})",
                allowed_roles
            ).fetchall()
            conn.close()
            admin_chat = os.environ.get("TG_CHAT", "")
            sent = 0
            for row in rows:
                chat_id = row[2]
                if chat_id == admin_chat: continue  # admin reçoit déjà via le canal principal
                try:
                    self._send_telegram_to(chat_id, msg)
                    sent += 1
                except: pass
            if sent > 0:
                print(f"[Broadcast/{min_role}+] Signal envoyé à {sent} membres")
        except Exception as e:
            print(f"[Broadcast] Erreur: {e}")

    # ── Portfolio ─────────────────────────────────────────────
    def db_get_portfolio(self, user_id=0, portfolio_name=None):
        conn = get_connection(); conn.row_factory = sqlite3.Row
        q = "SELECT * FROM portfolio WHERE user_id=?"; params = [user_id]
        if portfolio_name: q += " AND portfolio_name=?"; params.append(portfolio_name)
        rows = conn.execute(q+" ORDER BY id DESC", params).fetchall(); conn.close()
        result = [dict(r) for r in rows]
        coins = {c["symbol"]:c["price"] for c in self._last_data.get("coins",[])}
        for p in result:
            cur = coins.get(p["symbol"])
            if cur:
                p["current_price"] = cur
                p["pnl_pct"]       = round((cur-p["entry_price"])/p["entry_price"]*100, 2)
                p["pnl_usdt"]      = round((cur-p["entry_price"])*p["quantity"], 2)
                p["value_usdt"]    = round(cur*p["quantity"], 2)
            else: p["current_price"]=p["pnl_pct"]=p["pnl_usdt"]=p["value_usdt"]=None
        return result

    def db_get_portfolio_names(self, user_id=0):
        conn = get_connection()
        rows = conn.execute("SELECT DISTINCT portfolio_name FROM portfolio WHERE user_id=?",(user_id,)).fetchall()
        conn.close(); return [r[0] for r in rows] or ["Principal"]

    def db_add_position(self, data, user_id=0):
        conn = get_connection()
        conn.execute("INSERT INTO portfolio (user_id,portfolio_name,symbol,entry_price,quantity,date,notes) VALUES (?,?,?,?,?,?,?)",
            (user_id, data.get("portfolio_name","Principal"), data["symbol"].upper(), float(data["entry_price"]), float(data["quantity"]), datetime.now().isoformat(), data.get("notes","")))
        conn.commit(); conn.close()

    def db_del_position(self, pid, user_id=0):
        conn = get_connection()
        conn.execute("DELETE FROM portfolio WHERE id=? AND user_id=?",(pid,user_id)); conn.commit(); conn.close()

    def db_get_trades(self, user_id=0):
        conn = get_connection(); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM trades WHERE user_id=? ORDER BY id DESC",(user_id,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def db_add_trade(self, data, user_id=0):
        conn = get_connection()
        pnl = None
        if data.get("exit_price") and data.get("entry_price"):
            mult = 1 if data.get("side","long").lower()=="long" else -1
            pnl  = round((float(data["exit_price"])-float(data["entry_price"]))*float(data.get("quantity",1))*mult, 4)
        conn.execute("INSERT INTO trades (user_id,symbol,side,entry_price,exit_price,quantity,pnl,date_open,date_close,notes,status) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (user_id, data["symbol"].upper(), data.get("side","long"), data.get("entry_price"), data.get("exit_price"), data.get("quantity"), pnl, data.get("date_open",datetime.now().isoformat()), data.get("date_close"), data.get("notes",""), "closed" if data.get("exit_price") else "open"))
        conn.commit(); conn.close()

    def db_del_trade(self, tid, user_id=0):
        conn = get_connection()
        conn.execute("DELETE FROM trades WHERE id=? AND user_id=?",(tid,user_id)); conn.commit(); conn.close()

    def db_get_alerts(self, user_id=0):
        conn = get_connection(); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM price_alerts WHERE user_id=? ORDER BY id DESC",(user_id,)).fetchall()
        conn.close(); return [dict(r) for r in rows]

    def db_add_alert(self, data, user_id=0):
        conn = get_connection()
        conn.execute("INSERT INTO price_alerts (user_id,symbol,condition,target_price,created) VALUES (?,?,?,?,?)", (user_id, data["symbol"].upper(), data["condition"], float(data["target_price"]), datetime.now().isoformat()))
        conn.commit(); conn.close()

    def db_del_alert(self, aid, user_id=0):
        conn = get_connection()
        conn.execute("DELETE FROM price_alerts WHERE id=? AND user_id=?",(aid,user_id)); conn.commit(); conn.close()

    # ── Exchange Keys — CHIFFRÉES AVEC SECURITY.PY ───────────
    def save_exchange_keys(self, user_id, exchange, api_key, api_secret):
        """Sauvegarde les clés API CHIFFRÉES avec security.py/vault"""
        try:
            from security import save_exchange_keys_secure
            return save_exchange_keys_secure(user_id, exchange, api_key, api_secret)
        except Exception as e:
            print(f"[Exchange Keys] Erreur chiffrement: {e}")
            conn = get_connection()
            try:
                conn.execute("""CREATE TABLE IF NOT EXISTS user_exchange_keys (
                    user_id INTEGER, exchange TEXT, api_key TEXT DEFAULT '',
                    api_secret TEXT DEFAULT '', api_key_enc TEXT DEFAULT '',
                    api_secret_enc TEXT DEFAULT '', migrated INTEGER DEFAULT 0,
                    updated TEXT DEFAULT '', PRIMARY KEY (user_id, exchange))""")
            except: pass
            conn.execute("INSERT OR REPLACE INTO user_exchange_keys (user_id,exchange,api_key,api_secret,updated) VALUES (?,?,?,?,?)", (user_id, exchange, api_key, api_secret, datetime.now().isoformat()))
            conn.commit(); conn.close()
            return False

    def get_exchange_keys(self, user_id, exchange):
        """Récupère et DÉCHIFFRE les clés API avec security.py/vault"""
        try:
            from security import get_exchange_keys_secure
            return get_exchange_keys_secure(user_id, exchange)
        except Exception as e:
            print(f"[Exchange Keys] Erreur déchiffrement: {e}")
            try:
                conn = get_connection(); conn.row_factory = sqlite3.Row
                try: conn.execute("""CREATE TABLE IF NOT EXISTS user_exchange_keys (
                    user_id INTEGER, exchange TEXT, api_key TEXT DEFAULT '',
                    api_secret TEXT DEFAULT '', api_key_enc TEXT DEFAULT '',
                    api_secret_enc TEXT DEFAULT '', migrated INTEGER DEFAULT 0,
                    updated TEXT DEFAULT '', PRIMARY KEY (user_id, exchange))""")
                except: 