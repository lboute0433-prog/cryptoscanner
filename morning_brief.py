"""
CryptoScanner Pro — Morning Brief IA
Persistance SQLite — survit aux redémarrages Railway
"""
import os, json, hmac, hashlib, sqlite3
from db import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from ai_provider import analyze_text

try:
    from config import DATABASE_PATH, TELEGRAM_TOKEN, TELEGRAM_CHAT
    DB_PATH = DATABASE_PATH
except ImportError:
    DB_PATH = "cryptoscanner.db"
    TELEGRAM_TOKEN = os.environ.get("TG_TOKEN","")
    TELEGRAM_CHAT  = os.environ.get("TG_CHAT","")

# ── Fuseau / Token HMAC quotidien ────────────────────────────
BRIEF_TZ = ZoneInfo(os.environ.get("REPORT_TIMEZONE", "Europe/Paris"))

def get_today_str():
    return datetime.now(BRIEF_TZ).strftime("%Y-%m-%d")

def generate_daily_token(date_str=None):
    secret = os.environ.get("VAULT_SECRET", os.environ.get("SECRET_KEY","cs_brief_2024"))
    d = date_str or get_today_str()
    return hmac.new(secret.encode(), d.encode(), hashlib.sha256).hexdigest()

def is_token_valid(token):
    if not token: return False
    expected = generate_daily_token()
    try: return hmac.compare_digest(token.encode(), expected.encode())
    except: return False

# ── Persistance DB ───────────────────────────────────────────
def _init_brief_table():
    try:
        conn = get_connection()
        conn.execute("""CREATE TABLE IF NOT EXISTS morning_brief_cache (
            id INTEGER PRIMARY KEY, date TEXT, html TEXT,
            score INTEGER, signal TEXT, created TEXT)""")
        conn.commit(); conn.close()
    except: pass

def _save_brief(html, date, score, signal):
    try:
        _init_brief_table()
        conn = get_connection()
        conn.execute("DELETE FROM morning_brief_cache")
        conn.execute(
            "INSERT INTO morning_brief_cache (date,html,score,signal,created) VALUES (?,?,?,?,datetime('now'))",
            (date, html, score, signal))
        conn.commit(); conn.close()
        print("[Brief] Sauvegarde en DB OK")
    except Exception as e:
        print(f"[Brief] Erreur save DB: {e}")

def _load_brief():
    try:
        _init_brief_table()
        conn = get_connection(); conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM morning_brief_cache LIMIT 1").fetchone()
        conn.close()
        return dict(row) if row else None
    except: return None

# ── Variables mémoire ────────────────────────────────────────
_current_brief_html   = None
_current_brief_date   = None
_current_brief_score  = None
_current_brief_signal = None

FR_WEEKDAYS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
FR_MONTHS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]


def format_fr_long(dt=None):
    dt = dt or datetime.now(BRIEF_TZ)
    return f"{FR_WEEKDAYS[dt.weekday()]} {dt.day} {FR_MONTHS[dt.month-1]} {dt.year}"

def _get_brief_html():
    global _current_brief_html, _current_brief_date, _current_brief_score, _current_brief_signal
    if _current_brief_html:
        return _current_brief_html
    # Charger depuis DB si disponible
    cached = _load_brief()
    if cached and cached.get("html"):
        _current_brief_html   = cached["html"]
        _current_brief_date   = cached["date"]
        _current_brief_score  = cached.get("score")
        _current_brief_signal = cached.get("signal")
        print(f"[Brief] Chargé depuis DB ({_current_brief_date})")
        return _current_brief_html
    return None

# ── Collecte données ─────────────────────────────────────────
def fetch_brief_data():
    """Collecte les données en utilisant le scanner existant en priorité,
    puis les APIs externes en fallback."""
    data = {}

    # ── Priorité 1 : données du scanner déjà en mémoire ──────
    try:
        from app import engine
        last = engine._last_data
        coins = last.get("coins", [])
        if coins:
            # Construire prices depuis les données du scanner
            sym_map = {
                "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
                "BNB": "binancecoin", "XRP": "ripple", "AVAX": "avalanche-2",
                "LINK": "chainlink", "ADA": "cardano", "DOT": "polkadot",
                "TON": "toncoin", "MATIC": "matic-network", "ATOM": "cosmos",
            }
            prices = {}
            total_mcap = 0
            has_valid_changes = False
            for c in coins:
                sym = c.get("symbol","").upper()
                cg_id = sym_map.get(sym)
                if cg_id:
                    change = float(c.get("change_pct", 0) or 0)
                    prices[cg_id] = {
                        "usd": c.get("price", 0),
                        "usd_24h_change": change,
                        "usd_7d_change": c.get("change_7d", 0),
                        "usd_market_cap": c.get("market_cap", 0),
                    }
                    if change != 0:
                        has_valid_changes = True
                total_mcap += c.get("market_cap", 0)
            # ✓ Utiliser scanner SEULEMENT si les données ont des changes valides
            if prices and has_valid_changes:
                data["prices"] = prices
                data["global"] = {
                    "total_market_cap": {"usd": total_mcap},
                    "market_cap_percentage": {
                        "btc": (prices.get("bitcoin",{}).get("usd_market_cap",0) / total_mcap * 100) if total_mcap else 0
                    }
                }
                print(f"[Brief] Scanner cache OK {len(prices)} coins (avec changes valides)")
            elif prices:
                print(f"[Brief] Scanner cache incomplet (changes = 0), fallback CoinGecko")
    except Exception as e:
        print(f"[Brief] Scanner cache: {e}")

    # ── Priorité 2 : CoinGecko API si pas de cache ou data incomplète ────────────
    if not data.get("prices"):
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids":"bitcoin,ethereum,solana,binancecoin,ripple,avalanche-2,chainlink,cardano,polkadot,toncoin",
                        "vs_currencies":"usd","include_24hr_change":"true",
                        "include_7d_change":"true","include_market_cap":"true"},
                timeout=12)
            if r.status_code == 200:
                data["prices"] = r.json()
                print(f"[Brief] CoinGecko OK {len(data['prices'])} coins")
        except Exception as e: print(f"[Brief] CoinGecko: {e}")

    if not data.get("global"):
        try:
            r = requests.get("https://api.coingecko.com/api/v3/global", timeout=8)
            if r.status_code == 200: data["global"] = r.json().get("data",{})
        except Exception as e: print(f"[Brief] Global: {e}")

    # ── Fear & Greed ──────────────────────────────────────────
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=2", timeout=6)
        if r.status_code == 200:
            data["fear_greed"] = r.json().get("data",[])
            fg = data["fear_greed"]
            print(f"[Brief] FearGreed OK {fg[0].get('value','?')} ({fg[0].get('value_classification','?')})")
    except Exception as e: print(f"[Brief] FearGreed: {e}")

    # ── Bybit OI/Funding ──────────────────────────────────────
    try:
        r = requests.get("https://api.bybit.com/v5/market/tickers",
                         params={"category":"linear","symbol":"BTCUSDT"}, timeout=6)
        if r.status_code == 200:
            t = r.json().get("result",{}).get("list",[{}])[0]
            data["btc_oi"]      = float(t.get("openInterestValue",0))
            data["btc_funding"]  = float(t.get("fundingRate",0))*100
            print(f"[Brief] Bybit OK OI:{data['btc_oi']/1e9:.1f}B Funding:{data['btc_funding']:+.4f}%")
    except Exception as e: print(f"[Brief] Bybit: {e}")

    # ── ETF BTC / ETH ─────────────────────────────────────────
    try:
        from cot_engine import fetch_etf_flows
        etf = fetch_etf_flows()
        data["etf"] = {
            "btc_total": float(etf.get("total_1d_btc", etf.get("total_1d", 0)) or 0),
            "eth_total": float(etf.get("total_1d_eth", 0) or 0),
            "source": etf.get("source", "mixed"),
        }
    except Exception as e:
        print(f"[Brief] ETF: {e}")

    # ── COT CFTC — BTC & ETH ─────────────────────────────────────
    try:
        from cot_engine import fetch_and_cache_cot
        cot_btc = fetch_and_cache_cot("BTC")
        if cot_btc:
            data["cot_btc"] = cot_btc[0]
        cot_eth = fetch_and_cache_cot("ETH")
        if cot_eth:
            data["cot_eth"] = cot_eth[0]
        print(f"[Brief] COT BTC signal={data.get('cot_btc',{}).get('signal','?')}")
    except Exception as e:
        print(f"[Brief] COT: {e}")

    # ── News FR prioritaires ──────────────────────────────────
    try:
        from news_macro import get_news_from_db, translate_news_batch
        brief_news = get_news_from_db(limit=5, critical_only=True, lang="fr")
        if len(brief_news) < 5:
            mixed_news = get_news_from_db(limit=8, critical_only=True, lang=None, prefer_lang="fr")
            seen = {n.get("url") for n in brief_news}
            for item in mixed_news:
                if item.get("url") in seen:
                    continue
                brief_news.append(item)
                seen.add(item.get("url"))
                if len(brief_news) >= 5:
                    break
        data["brief_news"] = translate_news_batch(brief_news[:5], "fr")
    except Exception as e:
        print(f"[Brief] News: {e}")

    # ── Macro du jour / dernières stats ───────────────────────
    try:
        from news_macro import fetch_economic_calendar
        cal = fetch_economic_calendar(view="day")
        data["macro"] = {
            "recent_releases": (cal.get("recent_releases") or [])[:3],
            "events": (cal.get("events") or [])[:3],
        }
    except Exception as e:
        print(f"[Brief] Macro: {e}")

    print(f"[Brief] Données: BTC=${data.get('prices',{}).get('bitcoin',{}).get('usd',0):,.0f}")
    return data

# ── Analyse (avec ou sans IA) ────────────────────────────────
def generate_analysis(market_data):
    p  = market_data.get("prices",{})
    g  = market_data.get("global",{})
    fg = market_data.get("fear_greed",[{}])
    etf = market_data.get("etf", {})
    brief_news = market_data.get("brief_news", [])
    macro = market_data.get("macro", {})
    cot_btc = market_data.get("cot_btc", {})
    cot_eth = market_data.get("cot_eth", {})
    btc = p.get("bitcoin",{})
    eth = p.get("ethereum",{})
    today = format_fr_long()
    etf_btc = float(etf.get("btc_total", 0) or 0)
    etf_eth = float(etf.get("eth_total", 0) or 0)
    etf_src = etf.get("source", "mixed")
    news_blob = " | ".join([n.get("title", "")[:100] for n in brief_news if n.get("title")]) or "Pas de news prioritaires FR"
    macro_lines = []
    for ev in (macro.get("recent_releases") or [])[:3]:
        macro_lines.append(f"{ev.get('title','?')} ({ev.get('currency','')}) {ev.get('assessment_label','Conforme')}")
    for ev in (macro.get("events") or [])[:2]:
        macro_lines.append(f"A venir {ev.get('time','')} {ev.get('title','?')} ({ev.get('currency','')})")
    macro_blob = " | ".join(macro_lines) or "Pas de stats macro saillantes"
    # ── Bloc COT pour le prompt ───────────────────────────────
    cot_blob = "COT non disponible"
    if cot_btc:
        lf_net  = cot_btc.get("lf_net", 0)
        am_net  = cot_btc.get("am_net", 0)
        oi      = cot_btc.get("open_interest", 0)
        oi_chg  = cot_btc.get("oi_chg", 0)
        sig     = cot_btc.get("signal", "NEUTRE")
        date_r  = cot_btc.get("report_date", "?")
        is_demo = cot_btc.get("demo", False)
        demo_tag = " [DEMO]" if is_demo else ""
        cot_blob = (
            f"BTC COT {date_r}{demo_tag}: LF_net={lf_net:+,} AM_net={am_net:+,} "
            f"OI={oi:,} OI_chg={oi_chg:+,} Signal={sig}"
        )
        if cot_eth:
            lf_e = cot_eth.get("lf_net", 0)
            am_e = cot_eth.get("am_net", 0)
            sig_e = cot_eth.get("signal", "NEUTRE")
            cot_blob += f" | ETH COT: LF_net={lf_e:+,} AM_net={am_e:+,} Signal={sig_e}"
    prompt = f"""Analyste crypto et marchés institutionnels senior. {today}
BTC: ${btc.get('usd',0):,.0f} ({btc.get('usd_24h_change',0):+.2f}% 24h, {btc.get('usd_7d_change',0):+.2f}% 7j)
ETH: ${eth.get('usd',0):,.0f} ({eth.get('usd_24h_change',0):+.2f}% 24h)
MCap: ${g.get('total_market_cap',{}).get('usd',0)/1e12:.2f}T | BTC.D: {g.get('market_cap_percentage',{}).get('btc',0):.1f}%
F&G: {fg[0].get('value','?') if fg else '?'} ({fg[0].get('value_classification','?') if fg else '?'})
OI BTC: ${market_data.get('btc_oi',0)/1e9:.1f}B | Funding: {market_data.get('btc_funding',0):+.4f}%
ETF BTC: {etf_btc:+.1f}M | ETF ETH: {etf_eth:+.1f}M | Source ETF: {etf_src}
COT CFTC: {cot_blob}
News FR: {news_blob}
Macro: {macro_blob}

Réponds UNIQUEMENT en JSON valide sans markdown:
{{"apercu":{{"sentiment":"Risk-on|Neutral|Risk-off","commentaire":"..."}},"btc":{{"prix":0,"variation_24h":0.0,"variation_7j":0.0,"analyse":"..."}},"eth":{{"prix":0,"variation_24h":0.0,"variation_7j":0.0,"analyse":"..."}},"altcoins":[{{"nom":"Solana","symbole":"SOL","variation_24h":0.0}},{{"nom":"BNB","symbole":"BNB","variation_24h":0.0}},{{"nom":"XRP","symbole":"XRP","variation_24h":0.0}},{{"nom":"Avalanche","symbole":"AVAX","variation_24h":0.0}},{{"nom":"Cardano","symbole":"ADA","variation_24h":0.0}}],"top_gagnants":["TOKEN +X%","TOKEN +X%","TOKEN +X%"],"top_perdants":["TOKEN -X%","TOKEN -X%","TOKEN -X%"],"derives":{{"funding":"...","open_interest":"...","analyse":"..."}},"etf":{{"btc":"...","eth":"...","analyse":"..."}},"cot":{{"signal_btc":"...","lf_net_btc":0,"am_net_btc":0,"oi_btc":0,"signal_eth":"...","alignement":"...","verdict":"...","is_demo":false}},"macro":["...","...","..."],"fear_greed":{{"valeur":0,"label":"...","interpretation":"..."}},"news":["...","...","...","...","..."],"resume":{{"biais":"Bullish|Neutral|Bearish","drivers":"...","risques":"...","catalyseurs":"..."}},"score":{{"valeur":0,"signal":"Bullish|Neutral|Bearish","justification":"..."}}}}"""
    result = analyze_text(prompt, max_tokens=1800, temperature=0.25)
    if not result.get("ok"):
        print(f"[Brief] IA: {result.get('error')}")
        return _fallback_analysis(market_data)
    try:
        text = (result.get("analysis") or "").strip().replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[Brief] Parse IA: {e}")
        return _fallback_analysis(market_data)

def _build_cot_fallback(market_data):
    """Construit le bloc COT pour le fallback (sans IA)."""
    cot_btc = market_data.get("cot_btc", {})
    cot_eth = market_data.get("cot_eth", {})
    if not cot_btc:
        return {"signal_btc":"N/D","lf_net_btc":0,"am_net_btc":0,"oi_btc":0,
                "signal_eth":"N/D","alignement":"Données COT non disponibles","verdict":"—","is_demo":True}
    lf_net  = cot_btc.get("lf_net", 0)
    am_net  = cot_btc.get("am_net", 0)
    oi      = cot_btc.get("open_interest", 0)
    sig_btc = cot_btc.get("signal", "NEUTRE")
    sig_eth = cot_eth.get("signal", "N/D") if cot_eth else "N/D"
    verdict = cot_btc.get("signal_detail", "Pas de verdict disponible")
    is_demo = cot_btc.get("demo", False)
    # Déterminer l'alignement macro
    if "HAUSSIER" in sig_btc and am_net > 0:
        alignement = "🟢 Institutionnels alignés à l'achat — accumulation confirmée"
    elif "BAISSIER" in sig_btc or am_net < 0:
        alignement = "🔴 Distribution institutionnelle — prudence"
    else:
        alignement = "⚪ Positionnement neutre — attendre signal directionnel"
    return {
        "signal_btc": sig_btc,
        "lf_net_btc": lf_net,
        "am_net_btc": am_net,
        "oi_btc": oi,
        "signal_eth": sig_eth,
        "alignement": alignement,
        "verdict": verdict,
        "is_demo": is_demo,
    }


def _fallback_analysis(market_data):
    p  = market_data.get("prices",{})
    g  = market_data.get("global",{})
    fg = market_data.get("fear_greed",[{}])
    btc  = p.get("bitcoin",{})
    eth  = p.get("ethereum",{})
    sol  = p.get("solana",{})
    bnb  = p.get("binancecoin",{})
    xrp  = p.get("ripple",{})
    avax = p.get("avalanche-2",{})
    ada  = p.get("cardano",{})
    link = p.get("chainlink",{})
    dot  = p.get("polkadot",{})
    ton  = p.get("toncoin",{})

    fg_val  = int(fg[0].get("value",50)) if fg else 50
    fg_lbl  = fg[0].get("value_classification","Neutre") if fg else "Neutre"
    btc_chg = float(btc.get("usd_24h_change",0) or 0)
    eth_chg = float(eth.get("usd_24h_change",0) or 0)
    score   = max(0, min(100, int(50+(fg_val-50)*0.3+btc_chg*2)))
    signal  = "Bullish" if score>=60 else "Bearish" if score<=40 else "Neutral"

    alts = [("Solana","SOL",sol),("BNB","BNB",bnb),("XRP","XRP",xrp),
            ("Avalanche","AVAX",avax),("Cardano","ADA",ada),
            ("Chainlink","LINK",link),("Polkadot","DOT",dot),("Toncoin","TON",ton)]
    alts_s = sorted([a for a in alts if a[2].get("usd",0)],
                    key=lambda x: float(x[2].get("usd_24h_change",0) or 0), reverse=True)
    altcoins = [{"nom":a[0],"symbole":a[1],"variation_24h":round(float(a[2].get("usd_24h_change",0) or 0),2)} for a in alts_s]
    winners  = [f"{a[1]} {float(a[2].get('usd_24h_change',0) or 0):+.1f}%" for a in alts_s[:3]]
    losers   = [f"{a[1]} {float(a[2].get('usd_24h_change',0) or 0):+.1f}%" for a in alts_s[-3:]]

    if fg_val>=75:   sent,comm = "Risk-on",  f"Marché Risk-On. F&G {fg_val}/100 ({fg_lbl}). BTC {btc_chg:+.1f}%."
    elif fg_val<=25: sent,comm = "Risk-off", f"Marché Risk-Off. F&G {fg_val}/100 ({fg_lbl}). Prudence."
    else:            sent,comm = "Neutral",  f"Consolidation. F&G {fg_val}/100 ({fg_lbl}). BTC {btc_chg:+.1f}%."

    oi  = float(market_data.get("btc_oi",0) or 0)
    fnd = float(market_data.get("btc_funding",0) or 0)
    etf = market_data.get("etf", {})
    macro = market_data.get("macro", {})
    brief_news = market_data.get("brief_news", [])
    mcp = float(g.get("total_market_cap",{}).get("usd",0) or 0)
    dom = float(g.get("market_cap_percentage",{}).get("btc",0) or 0)
    etf_btc = float(etf.get("btc_total", 0) or 0)
    etf_eth = float(etf.get("eth_total", 0) or 0)
    macro_items = []
    for ev in (macro.get("recent_releases") or [])[:2]:
        macro_items.append(f"{ev.get('title','?')} — {ev.get('assessment_label','Conforme')}")
    for ev in (macro.get("events") or [])[:1]:
        macro_items.append(f"A venir {ev.get('time','')} {ev.get('title','?')}")
    news_items = [n.get("title", "")[:90] for n in brief_news[:5] if n.get("title")]

    return {
        "apercu":{"sentiment":sent,"commentaire":comm},
        "btc":{"prix":btc.get("usd",0),"variation_24h":round(btc_chg,2),
               "variation_7j":round(float(btc.get("usd_7d_change",0) or 0),2),
               "analyse":f"BTC à ${btc.get('usd',0):,.0f}. 7j: {float(btc.get('usd_7d_change',0) or 0):+.1f}%."},
        "eth":{"prix":eth.get("usd",0),"variation_24h":round(eth_chg,2),
               "variation_7j":round(float(eth.get("usd_7d_change",0) or 0),2),
               "analyse":f"ETH à ${eth.get('usd',0):,.0f}. 7j: {float(eth.get('usd_7d_change',0) or 0):+.1f}%."},
        "altcoins":altcoins,"top_gagnants":winners,"top_perdants":losers,
        "derives":{"funding":f"{fnd:+.4f}%","open_interest":f"${oi/1e9:.1f}B" if oi else "N/D",
                   "analyse":f"Funding {fnd:+.4f}% — {'longs surexposés' if fnd>0.05 else 'marché équilibré'}."},
        "etf":{"btc":f"{etf_btc:+.1f}M","eth":f"{etf_eth:+.1f}M",
               "analyse":f"Flux ETF BTC {etf_btc:+.1f}M et ETH {etf_eth:+.1f}M."},
        "cot": _build_cot_fallback(market_data),
        "macro": macro_items[:3],
        "fear_greed":{"valeur":fg_val,"label":fg_lbl,
                      "interpretation":f"Hier: {fg[1].get('value','—') if len(fg)>1 else '—'} ({fg[1].get('value_classification','') if len(fg)>1 else ''})."},
        "news":news_items or [f"BTC {btc_chg:+.1f}% 24h — ${btc.get('usd',0):,.0f}",
                f"ETH {eth_chg:+.1f}% 24h — ${eth.get('usd',0):,.0f}",
                f"Fear & Greed: {fg_val}/100 ({fg_lbl})",
                f"Market Cap: ${mcp/1e12:.2f}T | BTC Dom: {dom:.1f}%",
                f"OI BTC: ${oi/1e9:.1f}B | Funding: {fnd:+.4f}%" if oi else "Données dérivés en cours"],
        "resume":{"biais":signal,"drivers":f"F&G {fg_val}, BTC {btc_chg:+.1f}%, ETF BTC {etf_btc:+.1f}M",
                  "risques":"Volatilité, surveiller les niveaux clés",
                  "catalyseurs":"News macro, flux ETF, mouvement BTC >3%"},
        "score":{"valeur":score,"signal":signal,
                 "justification":f"F&G {fg_val}/100 + BTC {btc_chg:+.1f}% + Funding {fnd:+.4f}%"}
    }

# ── HTML du Brief ────────────────────────────────────────────
def build_brief_html(analysis, market_data, token):
    p  = market_data.get("prices",{})
    g  = market_data.get("global",{})
    fg = market_data.get("fear_greed",[{}])
    now      = datetime.now(BRIEF_TZ)
    date_str = format_fr_long(now).capitalize()
    time_str = now.strftime("%H:%M")
    base_url = os.environ.get("BASE_URL","https://web-production-34b51.up.railway.app")

    score  = analysis.get("score",{})
    sv     = score.get("valeur",50)
    ss     = score.get("signal","Neutral")
    sc     = "#4caf50" if sv>=60 else "#f44336" if sv<=40 else "#ffd700"
    def sigc(s): return "#4caf50" if s=="Bullish" else "#f44336" if s=="Bearish" else "#ffd700"
    def clr(v):  return "#4caf50" if float(v or 0)>=0 else "#f44336"
    def pct(v):  return f"{'+' if float(v or 0)>=0 else ''}{float(v or 0):.2f}%"

    btc_d   = analysis.get("btc",{})
    eth_d   = analysis.get("eth",{})
    alts    = analysis.get("altcoins",[])
    derives = analysis.get("derives",{})
    etf_d    = analysis.get("etf",{})
    cot_d    = analysis.get("cot",{})
    macro_d  = analysis.get("macro",[])
    fg_d    = analysis.get("fear_greed",{})
    resume  = analysis.get("resume",{})
    mcap_t  = g.get("total_market_cap",{}).get("usd",0)
    btc_dom = g.get("market_cap_percentage",{}).get("btc",0)

    alt_rows = "".join([
        f'<tr style="border-bottom:1px solid #2a2a40;transition:background .15s">'
        f'<td style="padding:10px 8px;color:#ffd700;font-weight:700;font-size:13px">{a.get("symbole","")}</td>'
        f'<td style="padding:10px 8px;color:#aaa;font-size:12px">{a.get("nom","")}</td>'
        f'<td style="padding:10px 8px;color:{clr(a.get("variation_24h",0))};font-weight:700;font-size:13px;text-align:right">{pct(a.get("variation_24h",0))}</td>'
        f'</tr>'
        for a in alts])
    winners = "".join([f'<div style="color:#4caf50;padding:2px 0;font-size:12px">▸ {t}</div>' for t in analysis.get("top_gagnants",[])])
    losers  = "".join([f'<div style="color:#f44336;padding:2px 0;font-size:12px">▸ {t}</div>' for t in analysis.get("top_perdants",[])])
    news_li = "".join([f'<li style="padding:6px 0;border-bottom:1px solid #1a1a28;color:#ccc;font-size:13px;display:flex;gap:8px"><span style="color:#ffd700;flex-shrink:0">▸</span>{n}</li>' for n in analysis.get("news",[])])
    macro_li = "".join([f'<li style="padding:6px 0;border-bottom:1px solid #1a1a28;color:#ccc;font-size:13px;display:flex;gap:8px"><span style="color:#4caf50;flex-shrink:0">▸</span>{n}</li>' for n in macro_d])

    return f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Brief — {date_str}</title>
<style>
:root{{
  --bg-gradient: linear-gradient(135deg, #0f1428 0%, #1e1a4a 100%);
  --accent-gold: #ffd700;
  --sentiment-green: #4caf50;
  --sentiment-red: #f44336;
  --text-primary: #e0e0f0;
  --text-secondary: #ccc;
  --text-muted: #aaa;
  --text-subtle: #666;
  --card-bg: rgba(37,37,64,0.8);
  --row-alt-1: rgba(255,255,255,0.02);
  --row-alt-2: rgba(0,0,0,0.2);
}}

*{{box-sizing:border-box;margin:0;padding:0}}

body{{font-family:'Segoe UI',Arial,sans-serif;background:var(--bg-gradient);color:var(--text-primary);min-height:100vh}}
.hdr{{background:linear-gradient(135deg,#1a1a2e,#16213e);padding:20px 24px;border-bottom:2px solid var(--accent-gold);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}}

.wrap{{max-width:900px;margin:20px auto;padding:0 16px 60px}}

.score-card{{background:rgba(30,30,48,0.6);border-radius:12px;padding:20px;margin-bottom:14px;display:flex;gap:20px;align-items:center;flex-wrap:wrap;border-left:4px solid var(--accent-gold)}}

.score-card > div:first-child{{display:flex;flex-direction:column;align-items:center}}

.score-value{{font-size:72px;font-weight:700;line-height:1}}

.score-max{{color:var(--text-subtle);font-size:12px}}

.score-signal{{font-size:20px;font-weight:700;margin-bottom:6px}}

.score-bar{{background:#333;border-radius:6px;height:10px;overflow:hidden;margin-bottom:8px;width:100%}}

.score-bar-fill{{height:100%;background:linear-gradient(90deg,#f44336,#ffd700,#4caf50)}}
.sec{{background:#1e1e30;border-radius:10px;margin-bottom:8px;overflow:hidden}}

.sec-head{{display:flex;justify-content:space-between;align-items:center;padding:13px 18px;cursor:pointer;font-size:14px;font-weight:600;transition:background 0.15s;background:rgba(0,0,0,0.3);border-bottom:2px solid var(--accent-gold)}}

.sec-head:hover{{background:rgba(37,37,64,0.5)}}

.sec-body{{display:none;padding:16px 18px}}

.sec.open .sec-body{{display:block}}

.sec-head span:last-child{{transition:transform 0.2s}}

.sec.open .sec-head span:last-child{{transform:scaleY(-1)}}
.row{{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #1a1a28;font-size:13px}}
.row:last-child{{border-bottom:none}}
.rl{{color:#888}}.rv{{font-weight:700}}
.ccard{{background:#252540;border-radius:8px;padding:14px;flex:1;min-width:200px}}
.csym{{font-size:16px;font-weight:700;color:#ffd700}}
.cprice{{font-size:22px;font-weight:700;margin:4px 0}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}}
th{{color:#666;text-align:left;padding:5px 8px;border-bottom:1px solid #2a2a40}}
td{{padding:7px 8px;border-bottom:1px solid #1a1a28}}
.note{{color:#ccc;font-size:13px;line-height:1.6;margin-top:10px}}
.footer{{text-align:center;padding:30px 20px;color:#444;font-size:12px;border-top:1px solid #1a1a28;margin-top:40px}}
@media(max-width:600px){{.hdr{{flex-direction:column}}.ccard{{min-width:100%}}}}
</style></head><body>
<div class="hdr">
  <div>
    <div style="font-size:20px;font-weight:700;color:#ffd700">📊 CryptoScanner Pro</div>
    <div style="color:#888;font-size:11px">Morning Brief · Membres</div>
  </div>
  <div style="text-align:right">
    <div style="color:#ffd700;font-weight:700">{date_str}</div>
    <div style="color:#888;font-size:12px">Généré à {time_str}</div>
    <div style="background:#ff4444;color:#fff;font-size:10px;padding:2px 8px;border-radius:10px;margin-top:4px;display:inline-block">⏰ Expire à minuit</div>
  </div>
</div>
<div class="wrap">
<div class="score-card">
  <div>
    <div style="font-size:54px;font-weight:700;color:{sc};line-height:1">{sv}</div>
    <div style="color:#555;font-size:12px">/100</div>
  </div>
  <div style="flex:1">
    <div style="font-size:20px;font-weight:700;color:{sc};margin-bottom:6px">{ss.upper()}</div>
    <div style="background:#333;border-radius:6px;height:10px;overflow:hidden;margin-bottom:8px">
      <div style="width:{sv}%;height:100%;background:linear-gradient(90deg,#f44336,#ffd700,#4caf50)"></div>
    </div>
    <div style="color:#aaa;font-size:12px">{score.get('justification','')}</div>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>🌍 Aperçu global</span><span>▲</span></div>
  <div class="sec-body">
    <div class="row"><span class="rl">Sentiment</span><span class="rv" style="color:#ffd700">{analysis.get('apercu',{}).get('sentiment','—')}</span></div>
    <div class="row"><span class="rl">Market Cap Total</span><span class="rv">${mcap_t/1e12:.2f}T</span></div>
    <div class="row"><span class="rl">BTC Dominance</span><span class="rv" style="color:#f7931a">{btc_dom:.1f}%</span></div>
    <p class="note">{analysis.get('apercu',{}).get('commentaire','')}</p>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>₿ Bitcoin & Ethereum</span><span>▲</span></div>
  <div class="sec-body">
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px">
      <div class="ccard">
        <div class="csym">BTC</div>
        <div class="cprice">${btc_d.get('prix',0):,.0f}</div>
        <div style="color:{clr(btc_d.get('variation_24h',0))};font-weight:700">{pct(btc_d.get('variation_24h',0))}</div>
        <div style="color:#888;font-size:11px">7j: {pct(btc_d.get('variation_7j',0))}</div>
        <p class="note" style="font-size:11px;margin-top:6px">{btc_d.get('analyse','')}</p>
      </div>
      <div class="ccard">
        <div class="csym">ETH</div>
        <div class="cprice">${eth_d.get('prix',0):,.0f}</div>
        <div style="color:{clr(eth_d.get('variation_24h',0))};font-weight:700">{pct(eth_d.get('variation_24h',0))}</div>
        <div style="color:#888;font-size:11px">7j: {pct(eth_d.get('variation_7j',0))}</div>
        <p class="note" style="font-size:11px;margin-top:6px">{eth_d.get('analyse','')}</p>
      </div>
    </div>
  </div>
</div>
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>🪙 Altcoins</span><span>▼</span></div>
  <div class="sec-body">
    <table style="width:100%;border-collapse:collapse;background:#252540;border-radius:6px;overflow:hidden;margin-bottom:14px">
      <thead><tr style="background:#2a2a40">
        <th style="padding:10px 8px;text-align:left;color:#888;font-weight:600;font-size:11px;text-transform:uppercase;border-bottom:1px solid #1a1a28">Symbole</th>
        <th style="padding:10px 8px;text-align:left;color:#888;font-weight:600;font-size:11px;text-transform:uppercase;border-bottom:1px solid #1a1a28">Nom</th>
        <th style="padding:10px 8px;text-align:right;color:#888;font-weight:600;font-size:11px;text-transform:uppercase;border-bottom:1px solid #1a1a28">24h %</th>
      </tr></thead>
      <tbody>{alt_rows}</tbody>
    </table>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
      <div style="background:#1a2a1a;border-radius:6px;padding:10px;border-left:3px solid #4caf50">
        <div style="color:#4caf50;font-weight:700;font-size:12px;margin-bottom:6px">🟢 Gagnants</div>
        <div style="font-size:12px">{winners or '<div style=\"color:#666\">—</div>'}</div>
      </div>
      <div style="background:#2a1a1a;border-radius:6px;padding:10px;border-left:3px solid #f44336">
        <div style="color:#f44336;font-weight:700;font-size:12px;margin-bottom:6px">🔴 Perdants</div>
        <div style="font-size:12px">{losers or '<div style=\"color:#666\">—</div>'}</div>
      </div>
    </div>
  </div>
</div>
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>⚡ Dérivés</span><span>▼</span></div>
  <div class="sec-body">
    <div class="row"><span class="rl">Funding Rate BTC</span><span class="rv">{derives.get('funding','—')}</span></div>
    <div class="row"><span class="rl">Open Interest BTC</span><span class="rv">{derives.get('open_interest','—')}</span></div>
    <p class="note">{derives.get('analyse','')}</p>
  </div>
</div>
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>🏦 ETF BTC / ETH</span><span>▼</span></div>
  <div class="sec-body">
    <div class="row"><span class="rl">Flux ETF BTC</span><span class="rv">{etf_d.get('btc','—')}</span></div>
    <div class="row"><span class="rl">Flux ETF ETH</span><span class="rv">{etf_d.get('eth','—')}</span></div>
    <p class="note">{etf_d.get('analyse','')}</p>
  </div>
</div>
<div class="sec">
  <div class="sec-head" onclick="tog(this)">
    <span>📊 COT — Positionnement Institutionnel</span>
    <span style="color:{'#4caf50' if 'HAUSSIER' in str(cot_d.get('signal_btc','')) else '#f44336' if 'BAISSIER' in str(cot_d.get('signal_btc','')) else '#ffd700'}">{'🟢' if 'HAUSSIER' in str(cot_d.get('signal_btc','')) else '🔴' if 'BAISSIER' in str(cot_d.get('signal_btc','')) else '⚪'} {cot_d.get('signal_btc','N/D')}</span>
  </div>
  <div class="sec-body">
    {'<div style="background:#2a1a1a;border:1px solid #f44336;border-radius:6px;padding:8px 12px;margin-bottom:10px;font-size:11px;color:#f44336">⚠️ Données COT de démonstration — rapport CFTC non disponible</div>' if cot_d.get('is_demo') else ''}
    <div class="row">
      <span class="rl">👔 Leveraged Funds (BTC net)</span>
      <span class="rv" style="color:{'#4caf50' if (cot_d.get('lf_net_btc') or 0) < 0 else '#f44336'}">{(cot_d.get('lf_net_btc') or 0):+,}</span>
    </div>
    <div class="row">
      <span class="rl">🏦 Asset Managers (BTC net)</span>
      <span class="rv" style="color:{'#4caf50' if (cot_d.get('am_net_btc') or 0) > 0 else '#f44336'}">{(cot_d.get('am_net_btc') or 0):+,}</span>
    </div>
    <div class="row">
      <span class="rl">📈 Open Interest BTC</span>
      <span class="rv">{(cot_d.get('oi_btc') or 0):,} contrats</span>
    </div>
    <div class="row">
      <span class="rl">Ξ Signal ETH</span>
      <span class="rv" style="color:{'#4caf50' if 'HAUSSIER' in str(cot_d.get('signal_eth','')) else '#f44336' if 'BAISSIER' in str(cot_d.get('signal_eth','')) else '#aaa'}">{cot_d.get('signal_eth','N/D')}</span>
    </div>
    <p class="note" style="margin-top:10px;padding:10px;background:#1a2a1a;border-radius:6px;border-left:3px solid #4caf50">
      <strong style="color:#ffd700">Alignement :</strong> {cot_d.get('alignement','—')}
    </p>
    <p class="note">{cot_d.get('verdict','—')}</p>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>😱 Fear & Greed</span><span>▲</span></div>
  <div class="sec-body">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0">
      <div style="background:#252540;border-radius:8px;padding:14px;text-align:center">
        <div style="color:#888;font-size:10px;margin-bottom:4px">AUJOURD'HUI</div>
        <div style="font-size:36px;font-weight:700;color:#ffd700">{fg[0].get('value','?') if fg else fg_d.get('valeur','?')}</div>
        <div style="color:#aaa;font-size:11px">{fg[0].get('value_classification','') if fg else fg_d.get('label','')}</div>
      </div>
      <div style="background:#252540;border-radius:8px;padding:14px;text-align:center">
        <div style="color:#888;font-size:10px;margin-bottom:4px">HIER</div>
        <div style="font-size:36px;font-weight:700;color:#666">{fg[1].get('value','—') if len(fg)>1 else '—'}</div>
        <div style="color:#666;font-size:11px">{fg[1].get('value_classification','') if len(fg)>1 else ''}</div>
      </div>
    </div>
    <p class="note">{fg_d.get('interpretation','')}</p>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>📅 Macro du jour</span><span>▲</span></div>
  <div class="sec-body"><ul style="list-style:none;margin-top:8px">{macro_li or '<li style="color:#888;font-size:13px">Aucun point macro saillant.</li>'}</ul></div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>📰 Actualités</span><span>▲</span></div>
  <div class="sec-body"><ul style="list-style:none;margin-top:8px">{news_li}</ul></div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>🎯 Résumé stratégique</span><span>▲</span></div>
  <div class="sec-body">
    <div class="row"><span class="rl">Biais</span><span class="rv" style="color:{sigc(resume.get('biais','Neutral'))}">{resume.get('biais','—')}</span></div>
    <p class="note"><strong style="color:#ffd700">Moteurs :</strong> {resume.get('drivers','—')}</p>
    <p class="note"><strong style="color:#f44336">Risques :</strong> {resume.get('risques','—')}</p>
    <p class="note"><strong style="color:#4caf50">Catalyseurs :</strong> {resume.get('catalyseurs','—')}</p>
  </div>
</div>
</div>
<div class="footer">
  <div>📊 CryptoScanner Pro · Membres</div>
  <div style="margin-top:4px">Brief expire à minuit · Usage personnel</div>
  <div style="margin-top:4px">© {datetime.now().year} CryptoScanner · Données techniques à titre informatif — ne constitue pas un conseil d'achat ou de vente</div>
</div>
<script>function tog(h){{const s=h.closest('.sec');s.classList.toggle('open');const c=h.querySelector('span:last-child');if(c)c.textContent=s.classList.contains('open')?'▲':'▼';}}</script>
</body></html>"""

# ── Email & Telegram ─────────────────────────────────────────
def build_brief_email_html(token, score, signal):
    base_url = os.environ.get("BASE_URL","https://web-production-34b51.up.railway.app")
    brief_url = f"{base_url}/brief?token={token}"
    today = format_fr_long().capitalize()
    sig_c = "#4caf50" if signal=="Bullish" else "#f44336" if signal=="Bearish" else "#ffd700"
    sig_e = "🟢" if signal=="Bullish" else "🔴" if signal=="Bearish" else "🟡"
    year  = datetime.now().year
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f8;font-family:Arial,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f8;padding:30px 20px">
<tr><td><table width="100%" style="max-width:600px;margin:0 auto;background:#1e1e30;border-radius:14px;overflow:hidden">
<tr><td style="background:linear-gradient(135deg,#1a1a2e,#16213e);padding:24px;text-align:center">
  <div style="font-size:22px;font-weight:700;color:#ffd700">📊 CryptoScanner Pro</div>
  <div style="color:#888;font-size:11px;margin-top:4px">Morning Brief</div>
</td></tr>
<tr><td style="padding:24px 32px">
  <p style="color:#888;font-size:12px;margin:0 0 8px">Bonjour,</p>
  <p style="color:#e0e0f0;font-size:14px;margin:0 0 20px">Votre <strong style="color:#ffd700">Morning Brief du {today}</strong> est disponible.</p>
  <div style="background:#252540;border-radius:10px;padding:16px;margin-bottom:20px;display:flex;gap:16px;align-items:center">
    <div style="text-align:center;min-width:60px">
      <div style="font-size:32px;font-weight:700;color:{sig_c}">{score}</div>
      <div style="color:#555;font-size:10px">/100</div>
    </div>
    <div>
      <div style="font-weight:700;color:{sig_c}">{sig_e} {signal}</div>
      <div style="color:#888;font-size:11px">Signal du marché</div>
    </div>
  </div>
</td></tr>
<tr><td style="padding:0 32px 24px;text-align:center">
  <a href="{brief_url}" style="display:inline-block;background:#ffd700;color:#12121e;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700">📊 Accéder au Brief</a>
  <p style="color:#555;font-size:11px;margin-top:10px">⏰ Expire à minuit</p>
</td></tr>
<tr><td style="background:#12121e;padding:14px;text-align:center">
  <p style="color:#444;font-size:11px;margin:0">© {year} CryptoScanner Pro · Données techniques à titre informatif — ne constitue pas un conseil d'achat ou de vente</p>
</td></tr>
</table></td></tr></table></body></html>"""

def build_brief_telegram(analysis, token):
    """
    Telegram Morning Brief — Style Carte d'État-Major.
    Format structuré en blocs thématiques, lisible sur mobile.
    """
    base_url  = os.environ.get("BASE_URL","https://web-production-34b51.up.railway.app")
    brief_url = f"{base_url}/brief?token={token}"
    score  = analysis.get("score",{})
    btc    = analysis.get("btc",{})
    eth    = analysis.get("eth",{})
    fg     = analysis.get("fear_greed",{})
    etf    = analysis.get("etf",{})
    cot    = analysis.get("cot",{})
    derives = analysis.get("derives",{})
    resume = analysis.get("resume",{})
    apercu = analysis.get("apercu",{})
    alts   = analysis.get("altcoins",[])
    today  = datetime.now(BRIEF_TZ).strftime("%d/%m/%Y")
    week   = FR_WEEKDAYS[datetime.now(BRIEF_TZ).weekday()].capitalize()

    # ── Helpers ──────────────────────────────────────────────
    bv   = float(btc.get("variation_24h",0) or 0)
    ev   = float(eth.get("variation_24h",0) or 0)
    sv   = score.get("valeur",50)
    sig  = score.get("signal","Neutral")
    biais = resume.get("biais","Neutral")

    s_e  = "🟢" if sig=="Bullish" else "🔴" if sig=="Bearish" else "🟡"
    b_e  = "🟢" if biais=="Bullish" else "🔴" if biais=="Bearish" else "🟡"
    fg_v = fg.get("valeur",50) or 50
    fg_e = "🔥" if fg_v>=75 else "😱" if fg_v<=25 else "😐"

    # ── COT bloc ─────────────────────────────────────────────
    cot_sig = cot.get("signal_btc","N/D")
    cot_e   = "🟢" if "HAUSSIER" in str(cot_sig) else "🔴" if "BAISSIER" in str(cot_sig) else "⚪"
    lf_net  = cot.get("lf_net_btc",0) or 0
    am_net  = cot.get("am_net_btc",0) or 0
    oi_btc  = cot.get("oi_btc",0) or 0
    demo_tag = " <i>[démo]</i>" if cot.get("is_demo") else ""
    cot_bloc = (
        f"<b>📊 COT — POSITIONNEMENT INSTITUTIONNEL</b>{demo_tag}\n"
        f"{cot_e} <b>Signal BTC :</b> {cot_sig}\n"
        f"👔 <b>Leveraged Funds net :</b> <code>{lf_net:+,}</code>\n"
        f"🏦 <b>Asset Managers net :</b>  <code>{am_net:+,}</code>\n"
        f"📈 <b>Open Interest :</b> <code>{oi_btc:,}</code> contrats\n"
    )
    if cot.get("signal_eth") and cot.get("signal_eth") != "N/D":
        cot_bloc += f"Ξ  <b>Signal ETH :</b> {cot.get('signal_eth')}\n"
    cot_bloc += f"<i>{cot.get('alignement','')}</i>"

    # ── Top altcoins ─────────────────────────────────────────
    top3 = sorted(alts, key=lambda x: float(x.get("variation_24h",0) or 0), reverse=True)[:3]
    bot3 = sorted(alts, key=lambda x: float(x.get("variation_24h",0) or 0))[:3]
    alt_line = "  ".join([f"<b>{a['symbole']}</b> {float(a.get('variation_24h',0) or 0):+.1f}%" for a in top3])
    bot_line = "  ".join([f"<b>{a['symbole']}</b> {float(a.get('variation_24h',0) or 0):+.1f}%" for a in bot3])

    # ── News ─────────────────────────────────────────────────
    news_items = analysis.get("news",[])
    news_bloc  = "\n".join([f"▸ {n[:100]}" for n in news_items[:3] if n])

    # ── Macro ────────────────────────────────────────────────
    macro_items = analysis.get("macro",[])
    macro_bloc  = "\n".join([f"▸ {m[:100]}" for m in macro_items[:2] if m]) or "▸ Aucun point macro saillant"

    # ── Construction message ─────────────────────────────────
    sep = "─" * 28
    msg = (
        f"📊 <b>MORNING BRIEF — {week} {today}</b>\n"
        f"<i>Rapport Stratégique · CryptoScanner Pro</i>\n"
        f"{sep}\n\n"

        # BLOC 1 — Bilan global
        f"{s_e} <b>BILAN DU MARCHÉ</b>\n"
        f"Score : <b>{sv}/100</b> — {sig.upper()}\n"
        f"Sentiment : {apercu.get('sentiment','—')}\n"
        f"<i>{apercu.get('commentaire','')[:120]}</i>\n\n"

        # BLOC 2 — Prix BTC / ETH
        f"₿ <b>BTC :</b> ${btc.get('prix',0):,.0f}  "
        f"<b>{'▲' if bv>=0 else '▼'} {bv:+.2f}%</b>  "
        f"<i>{btc.get('variation_7j',0):+.1f}% 7j</i>\n"
        f"Ξ <b>ETH :</b> ${eth.get('prix',0):,.0f}  "
        f"<b>{'▲' if ev>=0 else '▼'} {ev:+.2f}%</b>\n"
        f"🟢 Top : {alt_line}\n"
        f"🔴 Bot : {bot_line}\n\n"
        f"{sep}\n\n"

        # BLOC 3 — COT institutionnel
        f"{cot_bloc}\n\n"
        f"{sep}\n\n"

        # BLOC 4 — ETF & Dérivés
        f"<b>🏦 ETF SPOT</b>\n"
        f"BTC : <b>{etf.get('btc','—')}</b>  |  ETH : <b>{etf.get('eth','—')}</b>\n"
        f"<i>{etf.get('analyse','')[:100]}</i>\n\n"
        f"<b>⚡ DÉRIVÉS</b>\n"
        f"Funding : <code>{derives.get('funding','—')}</code>  "
        f"OI : <b>{derives.get('open_interest','—')}</b>\n"
        f"<i>{derives.get('analyse','')[:100]}</i>\n\n"
        f"{sep}\n\n"

        # BLOC 5 — Fear & Greed + Macro
        f"{fg_e} <b>FEAR &amp; GREED :</b> {fg_v}/100 — {fg.get('label','')}\n\n"
        f"<b>📅 MACRO</b>\n"
        f"{macro_bloc}\n\n"
        f"{sep}\n\n"

        # BLOC 6 — News
        f"<b>📰 FLASH NEWS</b>\n"
        f"{news_bloc}\n\n"
        f"{sep}\n\n"

        # BLOC 7 — Résumé stratégique
        f"{b_e} <b>BIAIS STRATÉGIQUE : {biais.upper()}</b>\n"
        f"<b>Moteurs :</b> {resume.get('drivers','—')[:120]}\n"
        f"<b>Risques :</b> {resume.get('risques','—')[:100]}\n"
        f"<b>Catalyseurs :</b> {resume.get('catalyseurs','—')[:100]}\n\n"

        f"<a href='{brief_url}'>📄 Brief complet →</a>\n"
        f"<i>⏰ Expire à minuit · Usage personnel</i>"
    )
    return msg

def get_brief_recipients():
    try:
        conn = get_connection(); conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, username, email, tg_chat_id FROM users WHERE role != 'banned'"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"[Brief] get_recipients: {e}"); return []

# ── Job principal ────────────────────────────────────────────
def run_morning_brief():
    global _current_brief_html, _current_brief_date, _current_brief_score, _current_brief_signal
    print(f"\n{'='*50}\nMORNING BRIEF - {datetime.now(BRIEF_TZ).strftime('%d/%