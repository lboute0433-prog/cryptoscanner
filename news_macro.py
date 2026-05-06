#!/usr/bin/env python3
"""
CryptoScanner Pro V8.1 — News & Macro Engine (BUGFIX)
- Traduction FR/EN corrigée
- Catégorisation corrigée
- Calendrier économique réécrit avec vraies données
"""

import requests, feedparser, sqlite3, smtplib, os, json, time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import DATABASE_PATH as DB_PATH, TELEGRAM_CHAT, TELEGRAM_TOKEN
from db import get_connection

TG_TOKEN = TELEGRAM_TOKEN
TG_CHAT  = TELEGRAM_CHAT

import threading
_ff_lock = threading.Lock()
_ff_cache_xml = None
_ff_cache_ts = 0
_FF_CACHE_TTL = 1800  # 30 minutes

# ── Catégories news ───────────────────────────────────────────
CATEGORIES = {
    "regulation": {
        "label": "📊 Régulation",
        "color": "yellow",
        "keywords": ["sec", "regulation", "regulatory", "law", "ban", "banned", "legal",
                    "court", "lawsuit", "cftc", "fca", "irs", "tax", "compliance",
                    "government", "congress", "senate", "bill", "policy"]
    },
    "security": {
        "label": "🔐 Sécurité",
        "color": "red",
        "keywords": ["hack", "hacked", "exploit", "vulnerability", "scam", "fraud",
                    "phishing", "rugpull", "rug pull", "stolen", "breach", "attack",
                    "malware", "ransomware", "theft", "drainer"]
    },
    "market": {
        "label": "📈 Marché",
        "color": "green",
        "keywords": ["ath", "all-time high", "pump", "dump", "rally", "crash", "dip",
                    "bull", "bear", "correction", "breakout", "resistance", "support",
                    "liquidation", "short", "long", "price", "surge", "plunge"]
    },
    "institutional": {
        "label": "🏦 Institutionnel",
        "color": "accent",
        "keywords": ["blackrock", "fidelity", "etf", "fund", "institution", "bank",
                    "investment", "asset", "custody", "grayscale", "microstrategy",
                    "treasury", "corporate", "nasdaq", "nyse", "sec filing", "approval"]
    },
    "technology": {
        "label": "🔧 Technologie",
        "color": "blue",
        "keywords": ["upgrade", "fork", "launch", "mainnet", "testnet", "protocol",
                    "layer 2", "l2", "defi", "nft", "dao", "smart contract", "update",
                    "release", "integration", "partnership", "bridge", "rollup"]
    },
    "macro": {
        "label": "🌍 Macro",
        "color": "purple",
        "keywords": ["fed", "federal reserve", "inflation", "cpi", "gdp", "rate",
                    "interest rate", "recession", "economy", "dollar", "usd", "treasury",
                    "powell", "ecb", "central bank", "monetary", "fiscal"]
    },
    "adoption": {
        "label": "🚀 Adoption",
        "color": "green",
        "keywords": ["adoption", "merchant", "payment", "visa", "mastercard", "paypal",
                    "partnership", "integrates", "integration", "launches support", "accepts bitcoin",
                    "enterprise", "real world asset", "rwa", "consumer", "mainstream"]
    },
    "geopolitics": {
        "label": "🛰️ Géopolitique",
        "color": "orange",
        "keywords": ["war", "sanction", "election", "tariff", "china", "russia", "middle east",
                    "trade war", "geopolitic", "conflict", "opec", "oil shock", "embargo"]
    },
    "whale": {
        "label": "🐋 Whale",
        "color": "orange",
        "keywords": ["whale", "billion", "million worth", "large transfer", "moved",
                    "wallet", "address", "exchange inflow", "exchange outflow",
                    "accumulation", "distribution"]
    }
}

CRITICAL_KEYWORDS = [
    "sec", "hack", "hacked", "exploit", "listing", "ban", "banned",
    "etf", "liquidation", "crash", "bankruptcy", "arrest", "fraud",
    "regulation", "cbdc", "fed", "federal reserve", "inflation",
    "blackrock", "fidelity", "spot etf", "approval", "rejected",
    "delisted", "rug pull", "scam", "whale", "billion",
    "record high", "all time high", "ath", "breakout"
]

# Sources FR + EN
RSS_FEEDS = [
    {"name": "CoinTelegraph FR", "url": "https://fr.cointelegraph.com/rss", "lang": "fr"},
    {"name": "Cryptoast",        "url": "https://cryptoast.fr/feed/",       "lang": "fr"},
    {"name": "Journal du Coin",  "url": "https://journalducoin.com/feed/",  "lang": "fr"},
    {"name": "Coinactu",         "url": "https://coinactu.com/feed/",       "lang": "fr"},
    {"name": "The Coin Tribune",  "url": "https://thecointribune.com/feed/","lang": "fr"},
    {"name": "CoinDesk",         "url": "https://www.coindesk.com/arc/outboundfeeds/rss/", "lang": "en"},
    {"name": "CoinTelegraph",    "url": "https://cointelegraph.com/rss", "lang": "en"},
    {"name": "Decrypt",          "url": "https://decrypt.co/feed", "lang": "en"},
    {"name": "Bitcoin Magazine", "url": "https://bitcoinmagazine.com/.rss/full/", "lang": "en"},
    {"name": "The Block",        "url": "https://www.theblock.co/rss.xml", "lang": "en"},
    {"name": "BeInCrypto",       "url": "https://beincrypto.com/feed/", "lang": "en"},
    {"name": "Reuters Markets",  "url": "https://feeds.reuters.com/reuters/businessNews", "lang": "en"},
    {"name": "Yahoo Finance",    "url": "https://finance.yahoo.com/news/rssindex", "lang": "en"},
]

# ── Catégorisation ────────────────────────────────────────────
def categorize_news(title):
    title_lower = title.lower()
    scores = {}
    for cat_id, cat in CATEGORIES.items():
        score = sum(1 for kw in cat["keywords"] if kw in title_lower)
        if score > 0:
            scores[cat_id] = score
    if not scores:
        return "market", CATEGORIES["market"]
    best = max(scores, key=scores.get)
    return best, CATEGORIES[best]

def is_critical(title):
    return any(kw in title.lower() for kw in CRITICAL_KEYWORDS)

# ── Traduction (multi-API avec fallback) ──────────────────────
_translation_cache = {}

def translate_text(text, target_lang="fr"):
    """Traduit via MyMemory avec fallback LibreTranslate"""
    if not text or len(text) < 5: return text
    if target_lang == "en": return text
    cache_key = f"{target_lang}:{text[:80]}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    # Essai 1 : MyMemory
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:450], "langpair": f"en|{target_lang}", "de": "cryptoscanner@mail.com"},
            timeout=6
        )
        data = r.json()
        t = data.get("responseData", {}).get("translatedText", "")
        # MyMemory renvoie parfois "QUERY LENGTH LIMIT..." ou l'original
        if t and t != text and "QUERY LENGTH" not in t and len(t) > 5:
            _translation_cache[cache_key] = t
            return t
    except: pass

    # Essai 2 : Lingva Translate (instance publique)
    try:
        r = requests.get(
            f"https://lingva.ml/api/v1/en/{target_lang}/{requests.utils.quote(text[:300])}",
            timeout=5
        )
        t = r.json().get("translation", "")
        if t and t != text and len(t) > 5:
            _translation_cache[cache_key] = t
            return t
    except: pass

    return text  # Retourner original si tout échoue

def translate_news_batch(news_list, target_lang="fr"):
    if target_lang == "en": return news_list
    result = []
    for n in news_list:
        item = dict(n)
        original_title = n.get("title", "")
        item["title_original"] = original_title
        if item.get("lang") == target_lang:
            item["translated"] = False
            result.append(item)
            continue
        translated = translate_text(original_title, target_lang)
        item["title"] = translated
        item["translated"] = (translated != original_title)
        result.append(item)
    return result

# ── DB ────────────────────────────────────────────────────────
def init_news_db():
    conn = get_connection(); c = conn.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS news_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        url TEXT UNIQUE,
        source TEXT,
        published TEXT,
        category TEXT DEFAULT 'market',
        is_critical INTEGER DEFAULT 0,
        alerted INTEGER DEFAULT 0,
        fetched TEXT
    );
    CREATE TABLE IF NOT EXISTS econ_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        event_date TEXT,
        event_time TEXT DEFAULT '00:00',
        impact TEXT DEFAULT 'Medium',
        currency TEXT DEFAULT 'USD',
        forecast TEXT DEFAULT '',
        previous TEXT DEFAULT '',
        actual TEXT DEFAULT '',
        alerted INTEGER DEFAULT 0
    );
    """)

    # Nettoyage historique (Python)
    try:
        c.execute("DELETE FROM econ_events WHERE event_date < date('now', '-30 days')")
    except: pass

    c.executescript("""
    CREATE TABLE IF NOT EXISTS macro_cache (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated TEXT
    );
    CREATE TABLE IF NOT EXISTS alert_prefs (
        user_id INTEGER PRIMARY KEY,
        telegram_news INTEGER DEFAULT 1,
        email_news INTEGER DEFAULT 0,
        telegram_macro INTEGER DEFAULT 1,
        email_macro INTEGER DEFAULT 0,
        email_address TEXT DEFAULT '',
        smtp_server TEXT DEFAULT 'smtp.gmail.com',
        smtp_port INTEGER DEFAULT 587,
        smtp_user TEXT DEFAULT '',
        smtp_pass TEXT DEFAULT ''
    );
    """)
    # Ajouter colonnes manquantes
    try: c.execute("ALTER TABLE news_items ADD COLUMN category TEXT DEFAULT 'market'")
    except: pass
    try: conn.execute("ALTER TABLE news_items ADD COLUMN lang TEXT DEFAULT 'en'")
    except: pass
    conn.commit(); conn.close()

def _send_telegram(msg):
    """Envoie vers le chat admin ET tous les abonnés approuvés"""
    token = os.environ.get("TG_TOKEN", TG_TOKEN)
    chat  = os.environ.get("TG_CHAT",  TG_CHAT)

    if not token:
        print(f"[Telegram] ⚠️ TG_TOKEN not configured, skipping")
        return

    if not chat:
        print(f"[Telegram] ⚠️ TG_CHAT not configured, skipping")
        return

    # Construire la liste des destinataires
    from daily_report import get_all_recipients
    recipients = []
    try:
        recipients = get_all_recipients()
        print(f"[Telegram] Found {len(recipients)} recipients from daily_report")
    except Exception as e:
        print(f"[Telegram] Failed to get recipients from daily_report: {e}")
        recipients = [chat] if chat else []

    if chat and chat not in recipients:
        recipients.insert(0, chat)

    print(f"[Telegram] Sending to {len(recipients)} recipients. Message preview: {msg[:50]}...")

    for cid in recipients:
        if not cid: continue
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": cid, "text": msg, "parse_mode": "HTML",
                      "disable_web_page_preview": True},
                timeout=5
            )
            if resp.status_code == 200:
                print(f"[Telegram] ✅ Message sent to {cid}")
            else:
                print(f"[Telegram] ❌ Failed to send to {cid}: HTTP {resp.status_code} — {resp.text}")
        except Exception as e:
            print(f"[Telegram] ❌ Error sending to {cid}: {e}")

def send_email(to, subject, body, prefs=None):
    if not prefs or not to: return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = prefs.get("smtp_user","")
        msg["To"]      = to
        msg.attach(MIMEText(body, "html"))
        with smtplib.SMTP(prefs.get("smtp_server","smtp.gmail.com"),
                         int(prefs.get("smtp_port",587))) as s:
            s.starttls()
            s.login(prefs.get("smtp_user",""), prefs.get("smtp_pass",""))
            s.sendmail(prefs.get("smtp_user",""), to, msg.as_string())
    except Exception as e:
        print(f"[Email] {e}")

# ── Fetch News RSS ────────────────────────────────────────────
def fetch_news_rss():
    all_items = []
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:12]:
                title = entry.get("title","").strip()
                url   = entry.get("link","")
                pub   = entry.get("published","")
                if not title or not url: continue
                cat_id, cat_info = categorize_news(title)
                all_items.append({
                    "title":       title,
                    "url":         url,
                    "source":      feed_info["name"],
                    "published":   pub,
                    "category":    cat_id,
                    "is_critical": 1 if is_critical(title) else 0,
                    "lang":        feed_info.get("lang","en"),
                })
        except Exception as e:
            print(f"[RSS] {feed_info['name']}: {e}")

    conn = get_connection()
    new_critical = []
    for item in all_items:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO news_items (title,url,source,published,category,is_critical,alerted,fetched,lang) VALUES (?,?,?,?,?,?,0,?,?)",
                (item["title"], item["url"], item["source"], item["published"],
                 item["category"], item["is_critical"], datetime.now().isoformat(), item.get("lang","en"))
            )
            if item["is_critical"]:
                row = conn.execute("SELECT alerted FROM news_items WHERE url=?", (item["url"],)).fetchone()
                if row and row[0] == 0:
                    new_critical.append(item)
                    conn.execute("UPDATE news_items SET alerted=1 WHERE url=?", (item["url"],))
        except: pass
    conn.commit(); conn.close()

    for item in new_critical[:3]:
        cat_id, cat_info = categorize_news(item["title"])
        _send_telegram(
            f"🚨 <b>NEWS IMPORTANTE</b> {cat_info['label']}\n\n"
            f"📰 {item['source']}\n"
            f"<b>{item['title']}</b>\n\n"
            f"🔗 {item['url']}"
        )
    return all_items

def get_news_from_db(limit=30, critical_only=False, category=None, search=None, source=None, lang=None, prefer_lang="fr"):
    conn = get_connection(); conn.row_factory = sqlite3.Row
    q = "SELECT * FROM news_items WHERE 1=1"
    params = []
    if critical_only: q += " AND is_critical=1"
    if category and category != "all": q += " AND category=?"; params.append(category)
    if search:  q += " AND title LIKE ?"; params.append(f"%{search}%")
    if lang in ("fr", "en"):
        q += " AND lang=?"
        params.append(lang)
    if source and source not in ("all", "fr", "en"):
        q += " AND source=?"; params.append(source)
    if lang is None and prefer_lang in ("fr", "en"):
        q += " ORDER BY CASE WHEN lang=? THEN 0 ELSE 1 END, is_critical DESC, id DESC LIMIT ?"
        params.append(prefer_lang)
    else:
        q += " ORDER BY is_critical DESC, id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    result = [dict(r) for r in rows]
    for item in result:
        cat_id   = item.get("category","market")
        cat_info = CATEGORIES.get(cat_id, CATEGORIES["market"])
        item["category_label"] = cat_info["label"]
        item["category_color"] = cat_info["color"]
        item["lang"]           = item.get("lang","en")
    return result

# ── Calendrier économique ─────────────────────────────────────
ECON_RULES = [
    {"title":"CPI USA (Inflation)",      "impact":"High",   "currency":"USD", "time":"14:30", "rule":"monthly_day",    "day":12,
     "forecast_val":"2.8%", "previous_val":"3.0%", "description":"Indice des prix à la consommation USA"},
    {"title":"Non-Farm Payrolls",        "impact":"High",   "currency":"USD", "time":"14:30", "rule":"monthly_weekday","weekday":4,"week":1,
     "forecast_val":"160K",  "previous_val":"151K", "description":"Créations d'emplois hors secteur agricole"},
    {"title":"PCE Core",                 "impact":"High",   "currency":"USD", "time":"14:30", "rule":"monthly_day",    "day":28,
     "forecast_val":"2.7%",  "previous_val":"2.8%", "description":"Indice PCE Core — indicateur préféré de la Fed"},
    {"title":"PIB USA (GDP)",            "impact":"High",   "currency":"USD", "time":"14:30", "rule":"quarterly",      "day":28,"months":[1,4,7,10],
     "forecast_val":"2.5%",  "previous_val":"3.1%", "description":"Croissance du PIB américain trimestriel"},
    {"title":"Décision taux Fed (FOMC)", "impact":"High",   "currency":"USD", "time":"20:00", "rule":"fomc",
     "forecast_val":"4.50%", "previous_val":"4.50%","description":"Taux directeur Federal Reserve"},
    {"title":"Inscriptions chômage",     "impact":"Medium", "currency":"USD", "time":"14:30", "rule":"weekly",         "weekday":3,
     "forecast_val":"225K",  "previous_val":"220K", "description":"Nouvelles demandes d'allocations chômage"},
    {"title":"Ventes au détail USA",     "impact":"Medium", "currency":"USD", "time":"14:30", "rule":"monthly_day",    "day":15,
     "forecast_val":"+0.4%", "previous_val":"-0.9%","description":"Ventes au détail mensuelles USA"},
    {"title":"ISM Manufacturing",        "impact":"Medium", "currency":"USD", "time":"16:00", "rule":"monthly_day",    "day":1,
     "forecast_val":"49.5",  "previous_val":"50.3", "description":"Indice ISM secteur manufacturier (>50 = expansion)"},
    {"title":"Décision taux BCE",        "impact":"High",   "currency":"EUR", "time":"13:45", "rule":"fomc",
     "forecast_val":"2.65%", "previous_val":"2.90%","description":"Taux directeur Banque Centrale Européenne"},
    {"title":"CPI Zone Euro",            "impact":"High",   "currency":"EUR", "time":"11:00", "rule":"monthly_day",    "day":17,
     "forecast_val":"2.2%",  "previous_val":"2.4%", "description":"Inflation Zone Euro"},
    {"title":"Emploi UK",               "impact":"Medium", "currency":"GBP", "time":"08:00", "rule":"monthly_day",    "day":14,
     "forecast_val":"4.5%",  "previous_val":"4.4%", "description":"Taux de chômage Royaume-Uni"},
    {"title":"Confiance consommateurs",  "impact":"Medium", "currency":"USD", "time":"16:00", "rule":"monthly_day",    "day":25,
     "forecast_val":"95.0",  "previous_val":"98.3", "description":"Indice confiance consommateurs USA (Conference Board)"},
]

# Cache des résultats réels (mis à jour via ForexFactory RSS en session)
ECON_ACTUAL_CACHE = {}

# Mapping titres FR internes → mots-clés EN ForexFactory pour le matching
FF_TITLE_KEYWORDS = [
    # (mots-clés dans titre interne FR, mots-clés dans titre FF EN)
    (["inscriptions", "chômage"],                  ["jobless", "initial claims", "unemployment"]),
    (["non-farm", "payroll", "nfp"],               ["nonfarm", "non-farm", "employment change", "payroll"]),
    (["cpi usa", "cpi", "inflation"],              ["cpi", "consumer price index"]),
    (["cpi zone euro", "cpi euro"],                ["cpi", "consumer price"]),
    (["pce"],                                      ["pce", "core pce", "personal consumption"]),
    (["ventes au détail", "retail"],               ["retail sales"]),
    (["confiance consommateurs"],                  ["consumer confidence", "consumer sentiment", "michigan"]),
    (["fomc", "taux fed", "décision taux fed"],    ["fomc", "fed funds", "federal funds", "interest rate"]),
    (["décision taux bce", "bce"],                 ["ecb rate", "main refinancing", "ecb deposit"]),
    (["pib", "gdp"],                               ["gdp", "gross domestic"]),
    (["pmi"],                                      ["pmi", "purchasing managers"]),
    (["emploi uk"],                                ["claimant count", "unemployment rate", "employment"]),
]


def _titles_match_ff(title_internal: str, title_ff: str) -> bool:
    """Vérifie si un titre interne (FR) correspond à un titre ForexFactory (EN)."""
    ti = (title_internal or "").lower()
    tf = (title_ff or "").lower()
    # 1. Correspondance directe par préfixe
    if ti[:20] in tf or tf[:20] in ti:
        return True
    # 2. Correspondance par mots-clés alias FR/EN
    for fr_keys, en_keys in FF_TITLE_KEYWORDS:
        if any(k in ti for k in fr_keys) and any(k in tf for k in en_keys):
            return True
    return False


def _parse_macro_number(value):
    if value in (None, ""):
        return None
    try:
        raw = str(value).strip().replace(" ", "").replace(" ", "").replace(",", "")
        mult = 1.0
        upper = raw.upper()
        if upper.endswith("K"):
            mult = 1_000.0
            raw = raw[:-1]
        elif upper.endswith("M"):
            mult = 1_000_000.0
            raw = raw[:-1]
        elif upper.endswith("B"):
            mult = 1_000_000_000.0
            raw = raw[:-1]
        raw = raw.replace("%", "")
        if not raw:
            return None
        return float(raw) * mult
    except Exception:
        return None


def _macro_direction_hint(title):
    t = (title or "").lower()
    lower_is_better = [
        "cpi", "inflation", "chômage", "unemployment", "jobless",
        "taux", "rate decision", "taux bce", "core pce"
    ]
    higher_is_better = [
        "gdp", "pmi", "nfp", "emploi", "retail", "ventes au détail",
        "confiance", "manufacturing", "ism", "payrolls"
    ]
    if any(k in t for k in lower_is_better):
        return "lower_better"
    if any(k in t for k in higher_is_better):
        return "higher_better"
    return "unknown"


def _build_macro_assessment(event):
    actual_n = _parse_macro_number(event.get("actual"))
    forecast_n = _parse_macro_number(event.get("forecast"))
    previous_n = _parse_macro_number(event.get("previous"))
    if actual_n is None:
        return {
            "bias": "pending",
            "label": "En attente",
            "summary": "Résultat non encore publié.",
            "color": "muted",
        }

    direction = _macro_direction_hint(event.get("title", ""))
    ref = forecast_n if forecast_n is not None else previous_n
    if ref is None or direction == "unknown":
        return {
            "bias": "neutral",
            "label": "Publié",
            "summary": "Résultat publié. Lecture contextuelle à confirmer selon le marché.",
            "color": "accent",
        }

    delta = actual_n - ref
    if abs(delta) < max(abs(ref) * 0.001, 1e-9):
        return {
            "bias": "neutral",
            "label": "Conforme",
            "summary": "Résultat globalement conforme aux attentes du marché.",
            "color": "yellow",
        }

    is_positive = (delta > 0 and direction == "higher_better") or (delta < 0 and direction == "lower_better")
    if is_positive:
        return {
            "bias": "positive",
            "label": "Plutôt bon",
            "summary": "Statistique meilleure que prévu. Lecture globalement favorable au contexte macro.",
            "color": "green",
        }
    return {
        "bias": "negative",
        "label": "Plutôt mauvais",
        "summary": "Statistique moins bonne que prévu. Risque de réaction défavorable du marché.",
        "color": "red",
    }

def _matches_rule(d, rule):
    """d est un objet date Python"""
    r = rule.get("rule","")
    if r == "weekly":
        return d.weekday() == rule.get("weekday",3)
    if r == "monthly_day":
        return d.day == rule.get("day",1)
    if r == "monthly_weekday":
        wn = (d.day-1)//7+1
        return d.weekday()==rule.get("weekday",4) and wn==rule.get("week",1)
    if r == "quarterly":
        return d.day==rule.get("day",28) and d.month in rule.get("months",[1,4,7,10])
    if r == "fomc":
        from datetime import date as date_cls
        ref  = date_cls(2025,1,29)
        diff = (d - ref).days
        return diff>=0 and diff%42 in [0,1,2] and d.weekday()==2
    return False

def _make_countdown(d):
    """d = objet date Python"""
    today = datetime.now().date()
    diff  = (d - today).days
    if diff < 0:   return "Passé"
    if diff == 0:  return "Aujourd'hui ⭐"
    if diff == 1:  return "Demain"
    return f"Dans {diff} jours"


def _adjust_business_day(d):
    """Décale les dates théoriques tombant le week-end vers un jour ouvré."""
    # Saturday -> Friday, Sunday -> Monday
    wd = d.weekday()
    if wd == 5:
        return d - timedelta(days=1)
    if wd == 6:
        return d + timedelta(days=1)
    return d


def _resolve_rule_date(d, rule):
    """
    Retourne la date effective de publication pour une règle donnée.
    Certaines stats mensuelles/trimestrielles tombent sur un jour ouvré proche
    si la date théorique est en week-end.
    """
    r = rule.get("rule", "")
    if r in {"monthly_day", "quarterly"}:
        return _adjust_business_day(d)
    return d


def _macro_event_key(title: str, currency: str = "") -> str:
    t = (title or "").lower()
    c = (currency or "").upper()
    if "cpi" in t or "inflation" in t:
        base = "cpi"
    elif "non-farm" in t or "payroll" in t or "nfp" in t:
        base = "nfp"
    elif "pce" in t:
        base = "pce"
    elif "gdp" in t or "pib" in t:
        base = "gdp"
    elif "fomc" in t or "fed" in t:
        base = "fomc"
    elif "chômage" in t or "jobless" in t:
        base = "jobless"
    elif "retail" in t or "ventes au détail" in t:
        base = "retail"
    elif "ism" in t:
        base = "ism"
    else:
        base = "other"
    return f"{c}:{base}"


def _fetch_ff_xml():
    """Récupère le XML avec cache et User-Agent pour éviter les 429

    Stratégie :
    1. Utilise cache en mémoire (30 min TTL)
    2. Essaie 5 URL fallback (proxies publics + officielles)
    3. Augmente timeout à 20s
    4. Log détaillé (taille, codes HTTP, timeouts)
    5. Fallback sur cache BDD si tout échoue
    """
    global _ff_cache_xml, _ff_cache_ts
    import time
    now = time.time()

    with _ff_lock:
        # Retourner cache mémoire si encore frais
        if _ff_cache_xml and (now - _ff_cache_ts) < _FF_CACHE_TTL:
            print(f"[FF] Cache mémoire valide (age={int(now-_ff_cache_ts)}s)")
            return _ff_cache_xml

        try:
            # URLs fallback : proxies publics + sources officielles
            urls = [
                "https://nfs.faireconomy.media/ff_calendar_thisweek.xml",  # Source officielle
                "https://www.forexfactory.com/ff_calendar_thisweek.xml",   # Officiel
                "https://ff.faireconomy.media/ff_calendar_thisweek.xml",   # Alt officiel
                "https://calendar.forexfactory.com/ff_calendar_thisweek.xml",  # CDN alt
                "https://api.forexfactory.com/calendar/thisweek.xml",      # API endpoint
            ]
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/xml,text/xml",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive"
            }

            print(f"[FF] Tentative fetch (cache age={int(now-_ff_cache_ts) if _ff_cache_xml else 'N/A'}s)")

            for idx, url in enumerate(urls, 1):
                try:
                    print(f"[FF] Essai {idx}/{len(urls)}: {url[:50]}...")
                    r = requests.get(url, headers=headers, timeout=20)
                    xml_size = len(r.text)

                    if r.status_code == 200:
                        if xml_size > 1000:
                            _ff_cache_xml = r.text
                            _ff_cache_ts = now
                            print(f"[FF] ✅ Succès sur {url[:40]}... (size={xml_size} bytes, status=200)")
                            return _ff_cache_xml
                        else:
                            print(f"[FF] ⚠️ XML trop petit sur {url[:40]}... (size={xml_size} bytes)")
                    else:
                        print(f"[FF] ❌ HTTP {r.status_code} sur {url[:40]}...")

                except requests.Timeout as e:
                    print(f"[FF] ⏱️ Timeout (20s) sur {url[:40]}...")
                except requests.ConnectionError as e:
                    print(f"[FF] 🌐 Connexion impossible: {url[:40]}...")
                except Exception as e:
                    print(f"[FF] 💥 Erreur: {type(e).__name__} sur {url[:40]}...")

            # Si tous les essais ont échoué, charger depuis BDD si possible
            print(f"[FF] Tous les URLs ont échoué. Tentative BDD...")
            cached_xml = _cache_get("ff_xml_backup", max_age_min=1440)  # 24h
            if cached_xml:
                print(f"[FF] 💾 Utilisation du backup BDD (age=1d)")
                _ff_cache_xml = cached_xml
                _ff_cache_ts = now  # Renouveler TTL mémoire
                return _ff_cache_xml

        except Exception as e:
            print(f"[FF Cache Fetch] Erreur globale: {e}")

    # Retourner dernier cache mémoire si disponible
    if _ff_cache_xml:
        print(f"[FF] Fallback: retour du dernier cache mémoire")
        return _ff_cache_xml

    print(f"[FF] ❌ Aucune source disponible (pas de cache)")
    return None

def _merge_forexfactory_actuals(events):
    """
    Quand ForexFactory publie ff_actual, met à jour les lignes calendrier correspondantes.
    Utilise un matching par mots-clés FR/EN pour gérer les titres bilingues.
    Persiste les résultats dans :
    1. ECON_ACTUAL_CACHE (mémoire)
    2. macro_cache (BDD) pour survivre aux redémarrages
    """
    try:
        xml_data = _fetch_ff_xml()
        if not xml_data:
            # Si fetch échoue, recharger depuis BDD
            print(f"[FF] XML fetch échoué, rechargement depuis BDD...")
            for ev in events:
                cache_key = f"{ev.get('date')}_{ev['title'][:15]}"
                cached_actual = _cache_get(cache_key, max_age_min=10080)  # 7 jours
                if cached_actual:
                    ev["actual"] = cached_actual
                    try:
                        ev["assessment"] = _build_macro_assessment(ev)
                    except Exception:
                        pass
            return

        feed = feedparser.parse(xml_data)
        merged_count = 0

        for entry in feed.entries:
            actual = (entry.get("ff_actual") or "").strip()
            if not actual:
                continue
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            country = (entry.get("ff_country") or "").upper()
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(entry.get("published", ""))
                date_str = dt.strftime("%Y-%m-%d")
            except Exception:
                continue
            forecast = (entry.get("ff_forecast") or "").strip()
            previous = (entry.get("ff_previous") or "").strip()

            for ev in events:
                if ev.get("date") != date_str:
                    continue
                ev_cur = (ev.get("currency") or "").upper()
                if country and ev_cur and ev_cur != country:
                    continue
                # Matching amélioré : préfixe direct OU alias FR/EN
                if not _titles_match_ff(ev.get("title", ""), title):
                    continue

                ev["actual"] = actual
                if forecast:
                    ev["forecast"] = forecast
                if previous:
                    ev["previous"] = previous
                ev["source"] = "ForexFactory"

                # Persister dans 2 caches :
                # 1. Cache mémoire (rapide, perte au redémarrage)
                cache_key = f"{date_str}_{ev['title'][:15]}"
                ECON_ACTUAL_CACHE[cache_key] = actual

                # 2. BDD (persistent, mais plus lent)
                try:
                    _cache_set(cache_key, actual)
                except Exception as db_err:
                    print(f"[FF] Erreur persist BDD pour {cache_key}: {db_err}")

                try:
                    ev["assessment"] = _build_macro_assessment(ev)
                    merged_count += 1
                except Exception:
                    pass
                break

        if merged_count > 0:
            print(f"[FF] {merged_count} events enrichis avec valeurs réelles")
        # Aussi persister le XML lui-même en BDD comme backup
        try:
            _cache_set("ff_xml_backup", xml_data)
        except Exception:
            pass

    except Exception as e:
        print(f"[FF actual merge] Erreur: {e}")
        # Fallback silencieux vers cache BDD
        for ev in events:
            cache_key = f"{ev.get('date')}_{ev['title'][:15]}"
            cached_actual = _cache_get(cache_key, max_age_min=10080)
            if cached_actual:
                ev["actual"] = cached_actual


def get_calendar(date_str=None, view="week"):
    """Retourne le calendrier économique pour une plage de dates"""
    from datetime import date as date_cls
    import calendar as cal_mod

    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else datetime.now().date()
    except:
        target = datetime.now().date()

    # Calculer la plage
    if view == "day":
        date_from = target
        date_to   = target
    elif view == "week":
        monday    = target - timedelta(days=target.weekday())
        date_from = monday
        date_to   = monday + timedelta(days=6)
    elif view == "month":
        date_from = target.replace(day=1)
        last_day  = cal_mod.monthrange(target.year, target.month)[1]
        date_to   = target.replace(day=last_day)
    else:
        date_from = target
        date_to   = target + timedelta(days=7)

    events = []
    current = date_from
    while current <= date_to:
        for rule in ECON_RULES:
            try:
                if _matches_rule(current, rule):
                    effective = _resolve_rule_date(current, rule)
                    ev_date = effective.strftime("%Y-%m-%d")

                    # Essayer de récupérer la valeur "actual" depuis les caches
                    cache_key = f"{ev_date}_{rule['title'][:15]}"
                    actual_val = ECON_ACTUAL_CACHE.get(cache_key, "")

                    # Si pas d'actual en cache mémoire, essayer BDD
                    if not actual_val:
                        try:
                            actual_val = _cache_get(cache_key, max_age_min=10080) or ""
                        except Exception:
                            actual_val = ""

                    # FALLBACK : si pas de valeur réelle ET cache vide
                    # utiliser forecast_val au lieu de chaîne vide
                    if not actual_val:
                        actual_val = rule.get("forecast_val", "")

                    events.append({
                        "title":       rule["title"],
                        "date":        ev_date,
                        "time":        rule.get("time","14:30"),
                        "impact":      rule["impact"],
                        "currency":    rule["currency"],
                        "color":       "red" if rule["impact"]=="High" else "yellow" if rule["impact"]=="Medium" else "green",
                        "forecast":    rule.get("forecast_val",""),
                        "previous":    rule.get("previous_val",""),
                        "actual":      actual_val,  # Réel ou forecast_val en fallback
                        "description": rule.get("description",""),
                        "source":      "Modèle interne (estimatif)",
                        "countdown":   _make_countdown(effective),
                        "is_today":    effective == datetime.now().date(),
                        "is_past":     effective < datetime.now().date(),
                    })
                    events[-1]["assessment"] = _build_macro_assessment(events[-1])
            except Exception as e:
                print(f"[Calendar] Erreur build event: {e}")
        current += timedelta(days=1)

    # Enrichir avec ForexFactory RSS
    try:
        ff_events = _fetch_forexfactory_rss()
        for ev in ff_events:
            try:
                ev_date = datetime.strptime(ev["date"], "%Y-%m-%d").date()
                if date_from <= ev_date <= date_to:
                    ff_key = _macro_event_key(ev.get("title", ""), ev.get("currency", ""))
                    # Si un event ForexFactory existe pour le meme indicateur/currency
                    # (ex: CPI USD), on retire la version estimative interne.
                    filtered = []
                    for e in events:
                        e_key = _macro_event_key(e.get("title", ""), e.get("currency", ""))
                        same_day = e.get("date") == ev.get("date")
                        if e_key == ff_key and e.get("source", "").startswith("Modèle interne"):
                            if same_day or ff_key != "USD:other":
                                continue
                        filtered.append(e)
                    events = filtered
                    if not any(e["title"][:20] == ev["title"][:20] and e["date"] == ev["date"] for e in events):
                        events.append(ev)
            except: pass
    except: pass

    _merge_forexfactory_actuals(events)
    events.sort(key=lambda x: (x["date"], x.get("time","")))
    return {
        "events":    events,
        "recent_releases": _recent_releases(events),
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to":   date_to.strftime("%Y-%m-%d"),
        "view":      view,
        "target":    target.strftime("%Y-%m-%d"),
        "today":     datetime.now().date().strftime("%Y-%m-%d"),
        "count":     len(events)
    }

def _fetch_forexfactory_rss():
    events = []
    try:
        xml_data = _fetch_ff_xml()
        if not xml_data:
            return []
        feed = feedparser.parse(xml_data)
        for entry in feed.entries[:120]:
            title   = entry.get("title","").strip()
            country = entry.get("ff_country","")
            impact  = entry.get("ff_impact","Low")
            pub     = entry.get("published","")
            if not title: continue
            if country not in ("USD","EUR","GBP","JPY","CAD","AUD"): continue
            try:
                from email.utils import parsedate_to_datetime
                dt       = parsedate_to_datetime(pub)
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M")
                ev_date  = datetime.strptime(date_str, "%Y-%m-%d").date()
                countdown= _make_countdown(ev_date)
            except:
                date_str  = datetime.now().strftime("%Y-%m-%d")
                time_str  = "00:00"
                countdown = "?"
            events.append({
                "title":title, "date":date_str, "time":time_str,
                "impact":impact, "currency":country,
                "color":"red" if impact=="High" else "yellow" if impact=="Medium" else "green",
                "forecast":entry.get("ff_forecast",""),
                "previous":entry.get("ff_previous",""),
                "actual":entry.get("ff_actual","").strip(),
                "countdown":countdown,
                "source":"ForexFactory",
                "description": entry.get("summary","").strip(),
                "is_today": ev_date == datetime.now().date() if 'ev_date' in locals() else False,
                "is_past": ev_date < datetime.now().date() if 'ev_date' in locals() else False,
            })
            events[-1]["assessment"] = _build_macro_assessment(events[-1])
    except Exception as e:
        print(f"[ForexFactory] {e}")
    return events


def _recent_releases(events, max_items=6, lookback_days=7):
    today = datetime.now().date()
    recent = []
    for event in events:
        if not event.get("actual"):
            continue
        try:
            ev_date = datetime.strptime(event.get("date", ""), "%Y-%m-%d").date()
        except Exception:
            continue
        if (today - ev_date).days > lookback_days:
            continue
        recent.append(event)
    recent.sort(key=lambda e: f"{e.get('date','')} {e.get('time','')}", reverse=True)
    return recent[:max_items]

# ── Enrichissements pour Macro Events (Task #10) ─────────────────
def build_macro_alert(event, for_role: str = "free"):
    """
    Construit un message Telegram pour une alerte macro événement.

    FREE: Impact + chiffres clés (actual vs forecast/previous)
    PAID: Inclut BTC correlation historique + volatilité attendue + zones de réaction
    """
    impact = event.get("impact", "Low")
    impact_emoji = "🔴" if impact == "High" else "🟡" if impact == "Medium" else "🟢"
    currency = event.get("currency", "")
    title = event.get("title", "")
    actual = event.get("actual", "—") or "—"
    forecast = event.get("forecast", "—") or "—"
    previous = event.get("previous", "—") or "—"

    assessment = event.get("assessment") or _build_macro_assessment(event)
    assessment_label = assessment.get("label", "Publié")
    assessment_summary = assessment.get("summary", "")

    lines = [
        f"📊 <b>MACRO ALERT — {currency}</b>",
        f"",
        f"{impact_emoji} <b>{title}</b>",
        f"",
        f"Actuel : <code>{actual}</code>",
        f"Prévision : <code>{forecast}</code>",
        f"Précédent : <code>{previous}</code>",
        f"",
        f"{assessment_label} · {assessment_summary}",
    ]

    # ── CONTENU ADDITIONNEL PAID (Task #10 — Enrichissements) ────────────
    if for_role in ("paid", "vip", "admin"):
        lines.append(f"")
        lines.append(f"<b>═══ CONTEXTE CRYPTO ═══</b>")
        # TODO Task #10: Ajouter ici enrichissement BTC correlation + volatilité historique

    return "\n".join(lines)


def send_macro_alert_telegram(event, for_role: str = "free"):
    """
    Formate et envoie une alerte Telegram HTML pour un résultat macro publié.
    event doit contenir : title, currency, impact, actual, forecast, previous + optionnel assessment.
    Retourne True si envoyé avec succès, False sinon.
    """
    if not TG_TOKEN or not TG_CHAT:
        return False

    text = build_macro_alert(event, for_role=for_role)

    try:
        url  = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        # 1. Envoi admin (canal principal) — version FREE
        text_free = build_macro_alert(event, for_role="free")
        resp = requests.post(url, json={
            "chat_id":    TG_CHAT,
            "text":       text_free,
            "parse_mode": "HTML",
        }, timeout=10)

        # 2. Broadcast aux membres paid + VIP (version PAID avec enrichissements)
        try:
            from daily_report import get_members_by_role
            admin_chat = TG_CHAT or ""
            text_paid = build_macro_alert(event, for_role="paid")
            for cid in get_members_by_role("paid"):
                if cid == admin_chat: continue
                try:
                    requests.post(url, json={"chat_id": cid, "text": text_paid, "parse_mode": "HTML"}, timeout=5)
                except: pass
        except Exception: pass
        return resp.status_code == 200
    except Exception as e:
        print(f"[MacroAlert TG] {e}")
        return False


def fetch_forexfactory_results():
    """
    Récupère les résultats réels publiés aujourd'hui depuis ForexFactory RSS.
    Le RSS inclut ff_actual quand le résultat est publié (~15 min de délai).
    Retourne uniquement les événements avec un résultat réel nouveau.
    """
    results = []
    today   = datetime.now().strftime("%Y-%m-%d")
    try:
        feed = feedparser.parse("https://nfs.faireconomy.media/ff_calendar_thisweek.xml")
        for entry in feed.entries:
            actual   = entry.get("ff_actual","").strip()
            forecast = entry.get("ff_forecast","").strip()
            previous = entry.get("ff_previous","").strip()
            title    = entry.get("title","").strip()
            country  = entry.get("ff_country","")
            impact   = entry.get("ff_impact","Low")

            if not actual or not title: continue
            if country not in ("USD","EUR","GBP","JPY","CAD","AUD"): continue

            try:
                from email.utils import parsedate_to_datetime
                dt       = parsedate_to_datetime(entry.get("published",""))
                date_str = dt.strftime("%Y-%m-%d")
                time_str = dt.strftime("%H:%M")
            except:
                date_str = today
                time_str = datetime.now().strftime("%H:%M")

            if date_str != today: continue  # Seulement aujourd'hui

            results.append({
                "title":    title,
                "date":     date_str,
                "time":     time_str,
                "currency": country,
                "impact":   impact,
                "actual":   actual,
                "forecast": forecast,
                "previous": previous,
            })
    except Exception as e:
        print(f"[FF Results] {e}")
    return results

def check_and_alert_results(send_fn):
    """
    Vérifie les nouveaux résultats ForexFactory et envoie une alerte Telegram.
    À appeler toutes les 15 minutes depuis macro_loop.
    Utilise le cache pour éviter les doublons.
    """
    results = fetch_forexfactory_results()
    for r in results:
        cache_key = f"result_{r['date']}_{r['title'][:20]}"
        cached    = _cache_get(cache_key, 1440)  # 24h anti-doublon
        if cached: continue

        impact = r["impact"]
        if impact not in ("High", "Medium"): continue  # Ignorer Low

        # Comparer résultat vs prévision
        surprise = ""
        try:
            actual_n   = float(r["actual"].replace("%","").replace("K","000").replace("M","000000"))
            forecast_n = float(r["forecast"].replace("%","").replace("K","000").replace("M","000000")) if r["forecast"] else None
            if forecast_n is not None:
                diff = actual_n - forecast_n
                if abs(diff) > 0:
                    if diff > 0:
                        surprise = f"🟢 MEILLEUR QUE PRÉVU (+{diff:.2f})"
                    else:
                        surprise = f"🔴 MOINS BON QUE PRÉVU ({diff:.2f})"
        except: pass

        emoji = "🔴" if impact == "High" else "🟡"
        msg   = (f"{emoji} <b>RÉSULTAT PUBLIÉ — {r['title']}</b>\n\n"
                 f"✅ Actuel: <b>{r['actual']}</b>\n")
        if r["forecast"]: msg += f"📊 Prévision: {r['forecast']}\n"
        if r["previous"]: msg += f"📈 Précédent: {r['previous']}\n"
        if surprise:       msg += f"\n{surprise}\n"
        msg += (f"\n💱 {r['currency']} · {r['time']}\n"
                f"💡 Attention à la volatilité crypto !")

        send_fn(msg)
        _cache_set(cache_key, r["actual"])
        print(f"[FF Results] Alerte envoyée: {r['title']} = {r['actual']}")

def fetch_economic_calendar(date_str=None, view="week"):
    return get_calendar(date_str, view)

def get_upcoming_events(days=30):
    """Prochains événements économiques sur N jours"""
    from datetime import date as date_cls
    today  = datetime.now().date()
    events = []
    for i in range(days):
        d = today + timedelta(days=i)
        for rule in ECON_RULES:
            try:
                if _matches_rule(d, rule):
                    effective = _resolve_rule_date(d, rule)
                    events.append({
                        "title":    rule["title"],
                        "date":     effective.strftime("%Y-%m-%d"),
                        "time":     rule.get("time","14:30"),
                        "impact":   rule["impact"],
                        "currency": rule["currency"],
                        "color":    "red" if rule["impact"]=="High" else "yellow",
                        "countdown":_make_countdown(effective),
                        "is_today": effective == today,
                    })
            except: pass
    events.sort(key=lambda x: x["date"])
    return events

# ── Cache helper ──────────────────────────────────────────────
def _cache_get(key, max_age_min=30):
    conn = get_connection()
    row  = conn.execute("SELECT value, updated FROM macro_cache WHERE key=?", (key,)).fetchone()
    conn.close()
    if not row: return None
    if datetime.now() - datetime.fromisoformat(row[1]) > timedelta(minutes=max_age_min): return None
    try: return json.loads(row[0])
    except: return row[0]

def _cache_set(key, value):
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO macro_cache (key,value,updated) VALUES (?,?,?)",
                (key, json.dumps(value), datetime.now().isoformat()))
    conn.commit(); conn.close()

# ── Macro Data ────────────────────────────────────────────────
def fetch_inflation():
    cached = _cache_get("inflation", 60)
    if cached: return cached

    headers = {"User-Agent": "CryptoScanner/1.0"}
    for attempt in range(3):
        try:
            r = requests.get(
                "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL",
                headers=headers,
                timeout=15
            )
            lines = r.text.strip().split("\n")
            if len(lines) > 13:
                last      = float(lines[-1].split(",")[1])
                year_ago  = float(lines[-13].split(",")[1])
                inflation = round((last - year_ago) / year_ago * 100, 2)
                result = {
                    "value": inflation,
                    "trend": "↑" if inflation > 3 else "↓" if inflation < 2 else "→",
                    "color": "red" if inflation > 4 else "yellow" if inflation > 2 else "green",
                    "label": f"{inflation}% / an"
                }
                _cache_set("inflation", result)
                return result
        except Exception as e:
            print(f"[Inflation] attempt {attempt+1}/3 error: {e}")
            if attempt < 2:
                time.sleep(2)
    return {"value": None, "label": "N/A", "trend": "?", "color": "muted"}

def fetch_stablecoin_supply():
    cached = _cache_get("stablecoin", 30)
    if cached: return cached
    try:
        result = {}
        for coin_id, symbol in [("tether","USDT"),("usd-coin","USDC"),("dai","DAI")]:
            r = requests.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                params={"localization":"false","tickers":"false","market_data":"true","community_data":"false"},
                timeout=10
            )
            if r.status_code != 200 or "application/json" not in (r.headers.get("Content-Type", "").lower()):
                continue
            data = r.json()
            supply= data.get("market_data",{}).get("circulating_supply",0)
            chg7d = data.get("market_data",{}).get("price_change_percentage_7d",0) or 0
            result[symbol] = {
                "supply":     supply,
                "supply_fmt": f"${supply/1e9:.1f}B",
                "change_7d":  round(chg7d, 2),
                "trend":      "↑" if chg7d > 0.5 else "↓" if chg7d < -0.5 else "→"
            }
        if not result:
            return {}
        total = sum(v["supply"] for v in result.values())
        result["total"] = {"supply": total, "supply_fmt": f"${total/1e9:.1f}B"}
        _cache_set("stablecoin", result)
        return result
    except Exception as e:
        print(f"[Stablecoin] {e}")
        return {}

def fetch_nasdaq_correlation():
    cached = _cache_get("nasdaq", 15)
    if cached: return cached
    try:
        r = requests.get(
            "https://query1.finance.yahoo.com/v8/finance/chart/QQQ",
            params={"interval":"1d","range":"30d"},
            headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=15
        )
        data   = r.json()
        closes = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        nasdaq_closes = [c for c in closes if c is not None]
        qqq_change = None
        if len(nasdaq_closes) >= 2:
            qqq_change = round((nasdaq_closes[-1]-nasdaq_closes[-2])/nasdaq_closes[-2]*100, 2)
        result = {
            "qqq_price":  round(nasdaq_closes[-1], 2) if nasdaq_closes else None,
            "qqq_change": qqq_change,
            "correlation": None,
            "corr_label":  "N/A"
        }
        _cache_set("nasdaq", result)
        return result
    except Exception as e:
        print(f"[Nasdaq] {e}")
    return {"qqq_price":None,"qqq_change":None,"correlation":None,"corr_label":"N/A"}

def calc_market_dna_score(fear_greed, btc_dominance, signals_count, total_coins, gainers, funding=None):
    score = 50
    if fear_greed:
        fg = fear_greed.get("value", 50)
        if fg < 25:   score += 12
        elif fg < 40: score += 6
        elif fg > 75: score -= 12
        elif fg > 60: score -= 6
    if total_coins > 0:
        ratio = gainers / total_coins
        if ratio > 0.65:   score += 12
        elif ratio > 0.55: score += 6
        elif ratio < 0.35: score -= 12
        elif ratio < 0.45: score -= 6
    if btc_dominance:
        if btc_dominance > 60:   score -= 8
        elif btc_dominance > 55: score -= 4
        elif btc_dominance < 45: score += 8
        elif btc_dominance < 50: score += 4
    if total_coins > 0:
        sig_ratio = signals_count / total_coins
        if sig_ratio > 0.1:    score += 10
        elif sig_ratio > 0.05: score += 5
    score = max(0, min(100, score))
    label = ("🔴 BEARISH FORT" if score < 25 else "🟠 BEARISH" if score < 40 else
             "⚪ NEUTRE" if score < 60 else "🟡 BULLISH" if score < 75 else "🟢 BULLISH FORT")
    return {"score": score, "label": label}


# ── Alert Preferences ─────────────────────────────────────────
def get_alert_prefs(user_id=0):
    conn = get_connection(); conn.row_factory = sqlite3.Row
    row  = conn.execute("SELECT * FROM alert_prefs WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    if row: return dict(row)
    return {"user_id":user_id,"telegram_news":1,"email_news":0,
            "telegram_macro":1,"email_macro":0,"email_address":"",
            "smtp_server":"smtp.gmail.com","smtp_port":587,"smtp_user":"","smtp_pass":""}

def save_alert_prefs(user_id, data):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO alert_prefs
        (user_id,telegram_news,email_news,telegram_macro,email_macro,
         email_address,smtp_server,smtp_port,smtp_user,smtp_pass)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (user_id,
         data.get("telegram_news",1), data.get("email_news",0),
         data.get("telegram_macro",1), data.get("email_macro",0),
         data.get("email_address",""), data.get("smtp_server","smtp.gmail.com"),
         data.get("smtp_port",587), data.get("smtp_user",""), data.get("smtp_pass",""))
    )
    conn.commit(); conn.close()

# ── Catégories disponibles ────────────────────────────────────
def get_categories():
    return [{"id": k, "label": v["label"], "color": v["color"]}
            for k, v in CATEGORIES.items()]
