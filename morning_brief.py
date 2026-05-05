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
            for c in coins:
                sym = c.get("symbol","").upper()
                cg_id = sym_map.get(sym)
                if cg_id:
                    # Utiliser scanner mais avec fallback à 0 si absent (sera complété par CoinGecko)
                    prices[cg_id] = {
                        "usd": c.get("price", 0),
                        "usd_24h_change": float(c.get("change_pct") or 0),
                        "usd_7d_change": float(c.get("change_7d") or 0),
                        "usd_market_cap": c.get("market_cap", 0),
                    }
                total_mcap += c.get("market_cap", 0)
            if prices:
                data["prices"] = prices
                data["global"] = {
                    "total_market_cap": {"usd": total_mcap},
                    "market_cap_percentage": {
                        "btc": (prices.get("bitcoin",{}).get("usd_market_cap",0) / total_mcap * 100) if total_mcap else 0
                    }
                }
                print(f"[Brief] Scanner cache OK {len(prices)} coins")
    except Exception as e:
        print(f"[Brief] Scanner cache: {e}")

    # ── Priorité 2 : CoinGecko API si pas de cache OU si tous les variations sont zéro ────────────
    should_fetch_cg = False
    if not data.get("prices"):
        should_fetch_cg = True
    else:
        # Vérifier si toutes les variations sont zéro (défaut du scanner)
        prices = data.get("prices", {})
        all_zero_changes = all(
            p.get("usd_24h_change", 0) == 0
            for p in prices.values()
        )
        if all_zero_changes:
            print("[Brief] ⚠️ Toutes les variations sont zéro — tentative CoinGecko...")
            should_fetch_cg = True

    if should_fetch_cg:
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids":"bitcoin,ethereum,solana,binancecoin,ripple,avalanche-2,chainlink,cardano,polkadot,toncoin",
                        "vs_currencies":"usd","include_24hr_change":"true",
                        "include_7d_change":"true","include_market_cap":"true"},
                timeout=12)
            if r.status_code == 200:
                cg_prices = r.json()
                if not data.get("prices"):
                    # Première fois : utiliser complètement CoinGecko
                    data["prices"] = cg_prices
                    print(f"[Brief] CoinGecko OK {len(cg_prices)} coins")
                else:
                    # Merger : garder les prix du scanner, prendre les variations de CoinGecko
                    for coin_id, cg_data in cg_prices.items():
                        if coin_id in data["prices"]:
                            data["prices"][coin_id].update({
                                "usd_24h_change": cg_data.get("usd_24h_change", 0),
                                "usd_7d_change": cg_data.get("usd_7d_change", 0),
                                "usd_market_cap": cg_data.get("usd_market_cap", data["prices"][coin_id].get("usd_market_cap", 0))
                            })
                    print(f"[Brief] CoinGecko Merger OK — variations rafraîchies")
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
    def get_medal(idx):
        medals = ["🥇", "🥈", "🥉"]
        return medals[idx] if idx < len(medals) else f"#{idx+1}"
    def get_perf_width(v, min_val=-50, max_val=50):
        """Normaliser la variation en pourcentage (0-100) pour la barre."""
        v = float(v or 0)
        clamped = max(min_val, min(max_val, v))
        normalized = (clamped - min_val) / (max_val - min_val) * 100
        return int(normalized)

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

    # Construire les rangées altcoins avec medals, performance bars, et right-align prix
    alt_rows = ""
    for idx, a in enumerate(alts):
        medal = get_medal(idx)
        sym = a.get("symbole","")
        nom = a.get("nom","")
        perf = float(a.get("variation_24h",0) or 0)
        perf_pct = pct(perf)
        perf_width = get_perf_width(perf)
        perf_color = clr(perf)

        alt_rows += f'''<tr style="background:{'#1a1a28' if idx % 2 == 0 else '#1e1e30'}">
            <td style="color:#ffd700;font-weight:700;width:30px;text-align:center">{medal}</td>
            <td style="color:#ffd700;font-weight:700;width:60px">{sym}</td>
            <td style="color:#999">{nom}</td>
            <td style="flex:1;min-width:80px">
                <div style="display:flex;align-items:center;gap:6px">
                    <div style="flex:1;height:6px;background:#2a2a40;border-radius:3px;overflow:hidden">
                        <div style="width:{perf_width}%;height:100%;background:linear-gradient(90deg,#f44336,#ffd700,#4caf50);border-radius:3px"></div>
                    </div>
                </div>
            </td>
            <td style="color:{perf_color};font-weight:700;text-align:right;width:60px">{perf_pct}</td>
        </tr>'''

    winners = "".join([f'<div style="color:#4caf50;padding:2px 0;font-size:12px">▸ {t}</div>' for t in analysis.get("top_gagnants",[])])
    losers  = "".join([f'<div style="color:#f44336;padding:2px 0;font-size:12px">▸ {t}</div>' for t in analysis.get("top_perdants",[])])
    news_li = "".join([f'<li style="padding:6px 0;border-bottom:1px solid #1a1a28;color:#ccc;font-size:13px;display:flex;gap:8px"><span style="color:#ffd700;flex-shrink:0">▸</span>{n}</li>' for n in analysis.get("news",[])])
    macro_li = "".join([f'<li style="padding:6px 0;border-bottom:1px solid #1a1a28;color:#ccc;font-size:13px;display:flex;gap:8px"><span style="color:#4caf50;flex-shrink:0">▸</span>{n}</li>' for n in macro_d])

    return f"""<!DOCTYPE html>
<html lang="fr"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Morning Brief — {date_str}</title>
<style>
:root{{--accent-gold:#ffd700;--text-secondary:#888;--bg-dark:#0f1428;--bg-dark-2:#1e1a4a;--bg-card:#1e1e30;--bg-hover:#252540;--text-primary:#e0e0f0;--text-muted:#ccc;--border-light:#1a1a28;--green:#4caf50;--red:#f44336}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:-apple-system,'Segoe UI',Roboto,Oxygen,Ubuntu,Cantarell,sans-serif;background:linear-gradient(135deg,var(--bg-dark) 0%,var(--bg-dark-2) 100%);color:var(--text-primary);min-height:100vh;line-height:1.5}}
.hdr{{background:linear-gradient(135deg,var(--bg-dark),var(--bg-dark-2));padding:20px 24px;border-bottom:3px solid var(--accent-gold);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;box-shadow:0 2px 8px rgba(0,0,0,0.4)}}
.hdr-left{{display:flex;flex-direction:column;gap:4px}}
.hdr-right{{text-align:right;display:flex;flex-direction:column;gap:4px}}
.logo{{font-size:20px;font-weight:700;color:var(--accent-gold)}}
.logo-sub{{color:var(--text-secondary);font-size:11px}}
.date-time{{color:var(--accent-gold);font-weight:700;font-size:13px}}
.time-sub{{color:var(--text-secondary);font-size:11px}}
.expire-badge{{background:#ff5252;color:#fff;font-size:10px;padding:3px 10px;border-radius:12px;margin-top:4px;display:inline-block;font-weight:600}}
.wrap{{max-width:960px;margin:24px auto;padding:0 16px 80px}}
.score-card{{background:linear-gradient(135deg,var(--bg-card),var(--bg-hover));border-radius:14px;padding:24px;margin-bottom:20px;display:flex;gap:24px;align-items:center;flex-wrap:wrap;border:1px solid rgba(255,215,0,0.1);box-shadow:0 4px 16px rgba(0,0,0,0.3)}}
.score-big{{display:flex;flex-direction:column;align-items:center;gap:4px}}
.score-num{{font-size:64px;font-weight:700;color:{sc};line-height:0.9}}
.score-denom{{color:var(--text-secondary);font-size:12px;font-weight:600}}
.score-detail{{flex:1;min-width:250px}}
.signal-label{{font-size:18px;font-weight:700;color:{sc};margin-bottom:10px}}
.signal-bar{{background:rgba(0,0,0,0.4);border-radius:8px;height:12px;overflow:hidden;margin-bottom:12px}}
.signal-fill{{width:{sv}%;height:100%;background:linear-gradient(90deg,#f44336,#ffd700,#4caf50);border-radius:8px;transition:width 0.3s ease}}
.signal-details{{font-size:13px;color:var(--text-secondary);display:flex;gap:20px;flex-wrap:wrap;margin-bottom:8px;line-height:1.4}}
.signal-detail-item{{display:flex;align-items:center;gap:4px}}
.signal-justification{{color:#aaa;font-size:12px;font-style:italic;margin-top:8px;padding:8px;background:rgba(0,0,0,0.2);border-radius:6px;border-left:2px solid var(--accent-gold)}}
.sec{{background:var(--bg-card);border-radius:10px;margin-bottom:12px;overflow:hidden;border:1px solid rgba(255,215,0,0.05);transition:box-shadow 0.2s}}
.sec:hover{{box-shadow:0 4px 12px rgba(255,215,0,0.08)}}
.sec-head{{display:flex;justify-content:space-between;align-items:center;padding:14px 18px;cursor:pointer;font-size:14px;font-weight:600;transition:all 0.15s;border-bottom:2px solid var(--accent-gold);background:linear-gradient(90deg,rgba(255,215,0,0.03),transparent);user-select:none}}
.sec-head:hover{{background:linear-gradient(90deg,rgba(255,215,0,0.08),transparent)}}
.sec-head span:first-child{{display:flex;align-items:center;gap:6px;flex:1}}
.sec-head span:last-child{{flex-shrink:0;margin-left:12px;color:var(--accent-gold);font-size:16px;transition:transform 0.2s}}
.sec.open .sec-head span:last-child{{transform:rotate(0deg)}}
.sec-body{{display:none;padding:12px 18px 16px;background:linear-gradient(135deg,rgba(0,0,0,0.1),rgba(255,215,0,0.02))}}
.sec.open .sec-body{{display:block;animation:slideDown 0.2s ease-out}}
@keyframes slideDown{{from{{opacity:0;max-height:0}}to{{opacity:1;max-height:1000px}}}}
.row{{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border-light);font-size:13px;gap:12px}}
.row:last-child{{border-bottom:none}}
.row-label{{color:var(--text-secondary);flex:1}}
.row-value{{font-weight:700;text-align:right;flex-shrink:0}}
.ccard{{background:linear-gradient(135deg,var(--bg-hover),rgba(255,215,0,0.02));border-radius:10px;padding:16px;flex:1;min-width:200px;border-left:4px solid var(--accent-gold);border:1px solid rgba(255,215,0,0.1);transition:all 0.2s}}
.ccard:hover{{background:linear-gradient(135deg,var(--bg-hover),rgba(255,215,0,0.05));box-shadow:0 6px 20px rgba(255,215,0,0.12);transform:translateY(-2px)}}
.ccard-symbol{{font-size:16px;font-weight:700;color:var(--accent-gold);margin-bottom:4px}}
.ccard-price{{font-size:24px;font-weight:700;margin:6px 0;color:var(--text-primary)}}
.ccard-change{{font-weight:700;font-size:14px;margin-bottom:4px}}
.ccard-7d{{color:var(--text-secondary);font-size:11px}}
.ccard-note{{color:var(--text-muted);font-size:11px;line-height:1.5;margin-top:8px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px;background:rgba(0,0,0,0.2)}}
th{{color:var(--text-secondary);text-align:left;padding:8px;border-bottom:1px solid rgba(255,215,0,0.2);font-weight:600;background:rgba(0,0,0,0.3)}}
td{{padding:8px;border-bottom:1px solid var(--border-light);vertical-align:middle}}
tr{{transition:background 0.15s}}
tr:hover{{background:rgba(255,215,0,0.04) !important}}
.rank-cell{{color:var(--accent-gold);font-weight:700;text-align:center;width:35px}}
.medal-cell{{font-size:18px;text-align:center;width:40px}}
.sym-cell{{color:var(--accent-gold);font-weight:700;width:70px}}
.perf-container{{position:relative;height:6px;background:var(--border-light);border-radius:3px;overflow:hidden;margin:0}}
.perf-fill{{height:100%;background:linear-gradient(90deg,#f44336,#ffd700,#4caf50);border-radius:3px;transition:width 0.3s ease}}
.price-cell{{text-align:right;font-weight:700;white-space:nowrap}}
.note{{color:var(--text-muted);font-size:13px;line-height:1.6;margin-top:10px;padding:10px;background:rgba(0,0,0,0.2);border-radius:6px;border-left:3px solid var(--accent-gold)}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px}}
@media(max-width:768px){{.grid-2{{grid-template-columns:1fr}}.hdr{{flex-direction:column;text-align:center}}.hdr-right{{text-align:center}}.score-card{{flex-direction:column;gap:16px}}.signal-details{{flex-direction:column;gap:8px}}.ccard{{min-width:100%}}}}
@media(max-width:600px){{.wrap{{padding:0 12px 60px}}.sec-head{{font-size:13px;padding:12px 14px}}.score-num{{font-size:48px}}.logo{{font-size:18px}}.hdr{{padding:16px 12px}}}}
.footer{{text-align:center;padding:40px 20px;color:#555;font-size:11px;border-top:1px solid var(--border-light);margin-top:50px;line-height:1.6}}
.footer-text{{margin-bottom:4px}}
</style></head><body>
<div class="hdr">
  <div class="hdr-left">
    <div class="logo">📊 CryptoScanner Pro</div>
    <div class="logo-sub">Morning Brief · Membres</div>
  </div>
  <div class="hdr-right">
    <div class="date-time">{date_str}</div>
    <div class="time-sub">Généré à {time_str}</div>
    <div class="expire-badge">⏰ Expire à minuit</div>
  </div>
</div>
<div class="wrap">
<div class="score-card">
  <div class="score-big">
    <div class="score-num">{sv}</div>
    <div class="score-denom">/100</div>
  </div>
  <div class="score-detail">
    <div class="signal-label">{ss.upper()}</div>
    <div class="signal-bar">
      <div class="signal-fill"></div>
    </div>
    <div class="signal-details">
      <div class="signal-detail-item">
        <span>F&G:</span>
        <span style="color:var(--accent-gold);font-weight:700">{analysis.get('fear_greed',{}).get('valeur',50)} ({analysis.get('fear_greed',{}).get('label','Neutre')})</span>
      </div>
      <div class="signal-detail-item">
        <span>BTC:</span>
        <span style="color:{clr(btc_d.get('variation_24h',0))};font-weight:700">{pct(btc_d.get('variation_24h',0))}</span>
      </div>
    </div>
    <div class="signal-details">
      <div class="signal-detail-item">
        <span>OI:</span>
        <span style="color:var(--text-primary)">{derives.get('open_interest','—')}</span>
      </div>
      <div class="signal-detail-item">
        <span>Funding:</span>
        <span style="color:var(--text-primary)">{derives.get('funding','—')}</span>
      </div>
    </div>
    <div class="signal-justification">{score.get('justification','')}</div>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>🌍 Aperçu global</span><span>▲</span></div>
  <div class="sec-body">
    <div class="row"><span class="row-label">Sentiment</span><span class="row-value" style="color:var(--accent-gold)">{analysis.get('apercu',{}).get('sentiment','—')}</span></div>
    <div class="row"><span class="row-label">Market Cap Total</span><span class="row-value">${mcap_t/1e12:.2f}T</span></div>
    <div class="row"><span class="row-label">BTC Dominance</span><span class="row-value" style="color:#f7931a">{btc_dom:.1f}%</span></div>
    <p class="note">{analysis.get('apercu',{}).get('commentaire','')}</p>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>₿ Bitcoin & Ethereum</span><span>▲</span></div>
  <div class="sec-body" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:12px 0">
    <div class="ccard">
      <div class="ccard-symbol">BTC</div>
      <div class="ccard-price">${btc_d.get('prix',0):,.0f}</div>
      <div class="ccard-change" style="color:{clr(btc_d.get('variation_24h',0))}">{pct(btc_d.get('variation_24h',0))}</div>
      <div class="ccard-7d">7j: {pct(btc_d.get('variation_7j',0))}</div>
      <p class="ccard-note">{btc_d.get('analyse','')}</p>
    </div>
    <div class="ccard">
      <div class="ccard-symbol">ETH</div>
      <div class="ccard-price">${eth_d.get('prix',0):,.0f}</div>
      <div class="ccard-change" style="color:{clr(eth_d.get('variation_24h',0))}">{pct(eth_d.get('variation_24h',0))}</div>
      <div class="ccard-7d">7j: {pct(eth_d.get('variation_7j',0))}</div>
      <p class="ccard-note">{eth_d.get('analyse','')}</p>
    </div>
  </div>
</div>
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>🪙 Altcoins — Top 10</span><span>▼</span></div>
  <div class="sec-body">
    <table>
      <tr>
        <th class="medal-cell">Rang</th>
        <th class="sym-cell">Token</th>
        <th>Nom</th>
        <th style="text-align:center">Performance 24h</th>
        <th style="text-align:right;width:60px">Variation</th>
      </tr>
      {alt_rows}
    </table>
    <div class="grid-2" style="margin-top:14px">
      <div><div style="color:#4caf50;font-weight:700;font-size:12px;margin-bottom:8px">🟢 Top Gagnants</div>{winners}</div>
      <div><div style="color:#f44336;font-weight:700;font-size:12px;margin-bottom:8px">🔴 Top Perdants</div>{losers}</div>
    </div>
  </div>
</div>
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>⚡ Dérivés BTC</span><span>▼</span></div>
  <div class="sec-body">
    <div class="row"><span class="row-label">Funding Rate BTC</span><span class="row-value" style="color:{clr(float(derives.get('funding','0').replace('%','').replace(',','.') or 0))}">{derives.get('funding','—')}</span></div>
    <div class="row"><span class="row-label">Open Interest BTC</span><span class="row-value">{derives.get('open_interest','—')}</span></div>
    <p class="note">{derives.get('analyse','')}</p>
  </div>
</div>
<div class="sec">
  <div class="sec-head" onclick="tog(this)"><span>🏦 ETF Spot BTC / ETH</span><span>▼</span></div>
  <div class="sec-body">
    <div class="row"><span class="row-label">Flux ETF BTC</span><span class="row-value" style="color:{clr(float(etf_d.get('btc','0').replace('M','').replace(',','.') or 0))}">{etf_d.get('btc','—')}</span></div>
    <div class="row"><span class="row-label">Flux ETF ETH</span><span class="row-value" style="color:{clr(float(etf_d.get('eth','0').replace('M','').replace(',','.') or 0))}">{etf_d.get('eth','—')}</span></div>
    <p class="note">{etf_d.get('analyse','')}</p>
  </div>
</div>
<div class="sec">
  <div class="sec-head" onclick="tog(this)">
    <span>📊 COT — Positionnement Institutionnel {'[DÉMO]' if cot_d.get('is_demo') else ''}</span>
    <span style="color:{'var(--green)' if 'HAUSSIER' in str(cot_d.get('signal_btc','')) else 'var(--red)' if 'BAISSIER' in str(cot_d.get('signal_btc','')) else 'var(--accent-gold)'}">{'🟢' if 'HAUSSIER' in str(cot_d.get('signal_btc','')) else '🔴' if 'BAISSIER' in str(cot_d.get('signal_btc','')) else '⚪'} {cot_d.get('signal_btc','N/D')}</span>
  </div>
  <div class="sec-body">
    {'<div style="background:#2a1a1a;border:1px solid var(--red);border-radius:6px;padding:10px 12px;margin-bottom:10px;font-size:11px;color:var(--red)">⚠️ Données COT de démonstration — rapport CFTC non disponible</div>' if cot_d.get('is_demo') else ''}
    <div class="row">
      <span class="row-label">👔 Leveraged Funds (BTC net)</span>
      <span class="row-value" style="color:{'var(--green)' if (cot_d.get('lf_net_btc') or 0) < 0 else 'var(--red)'}">{(cot_d.get('lf_net_btc') or 0):+,}</span>
    </div>
    <div class="row">
      <span class="row-label">🏦 Asset Managers (BTC net)</span>
      <span class="row-value" style="color:{'var(--green)' if (cot_d.get('am_net_btc') or 0) > 0 else 'var(--red)'}">{(cot_d.get('am_net_btc') or 0):+,}</span>
    </div>
    <div class="row">
      <span class="row-label">📈 Open Interest BTC</span>
      <span class="row-value">{(cot_d.get('oi_btc') or 0):,}</span>
    </div>
    <div class="row">
      <span class="row-label">Ξ Signal ETH</span>
      <span class="row-value" style="color:{'var(--green)' if 'HAUSSIER' in str(cot_d.get('signal_eth','')) else 'var(--red)' if 'BAISSIER' in str(cot_d.get('signal_eth','')) else 'var(--text-secondary)'}">{cot_d.get('signal_eth','N/D')}</span>
    </div>
    <p class="note"><strong style="color:var(--accent-gold)">Alignement Institutionnel :</strong> {cot_d.get('alignement','—')}</p>
    <p class="note"><strong style="color:var(--accent-gold)">Verdict :</strong> {cot_d.get('verdict','—')}</p>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>😱 Fear & Greed Index</span><span>▲</span></div>
  <div class="sec-body">
    <div class="grid-2">
      <div style="background:var(--bg-hover);border-radius:10px;padding:16px;text-align:center;border:1px solid rgba(255,215,0,0.1)">
        <div style="color:var(--text-secondary);font-size:10px;font-weight:600;margin-bottom:6px">📈 AUJOURD'HUI</div>
        <div style="font-size:42px;font-weight:700;color:var(--accent-gold)">{fg[0].get('value','?') if fg else fg_d.get('valeur','?')}</div>
        <div style="color:#aaa;font-size:11px;margin-top:4px">{fg[0].get('value_classification','') if fg else fg_d.get('label','')}</div>
      </div>
      <div style="background:var(--bg-hover);border-radius:10px;padding:16px;text-align:center;border:1px solid rgba(255,215,0,0.1)">
        <div style="color:var(--text-secondary);font-size:10px;font-weight:600;margin-bottom:6px">📉 HIER</div>
        <div style="font-size:42px;font-weight:700;color:#666">{fg[1].get('value','—') if len(fg)>1 else '—'}</div>
        <div style="color:#666;font-size:11px;margin-top:4px">{fg[1].get('value_classification','') if len(fg)>1 else ''}</div>
      </div>
    </div>
    <p class="note">{fg_d.get('interpretation','')}</p>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>📅 Économie — Macro du jour</span><span>▲</span></div>
  <div class="sec-body">
    <ul style="list-style:none;margin-top:8px">{macro_li or '<li style="color:var(--text-secondary);font-size:13px;padding:6px 0">Aucun point macro saillant aujourd''hui.</li>'}</ul>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>📰 Flash News — Actualités</span><span>▲</span></div>
  <div class="sec-body">
    <ul style="list-style:none;margin-top:8px">{news_li}</ul>
  </div>
</div>
<div class="sec open">
  <div class="sec-head" onclick="tog(this)"><span>🎯 Résumé Stratégique</span><span>▲</span></div>
  <div class="sec-body">
    <div class="row"><span class="row-label">Biais Directional</span><span class="row-value" style="color:{sigc(resume.get('biais','Neutral'))};font-size:14px;font-weight:700">{resume.get('biais','—')}</span></div>
    <p class="note"><strong style="color:var(--accent-gold)">🔍 Moteurs Principaux :</strong> {resume.get('drivers','—')}</p>
    <p class="note"><strong style="color:var(--red)">⚠️  Risques à Surveiller :</strong> {resume.get('risques','—')}</p>
    <p class="note"><strong style="color:var(--green)">✨ Catalyseurs Potentiels :</strong> {resume.get('catalyseurs','—')}</p>
  </div>
</div>
</div>
<div class="footer">
  <div class="footer-text">📊 <strong>CryptoScanner Pro</strong> · Rapport réservé aux membres</div>
  <div class="footer-text">⏰ Ce brief expire à minuit · Usage personnel et confidentiel</div>
  <div class="footer-text">© {datetime.now().year} CryptoScanner Pro · Données techniques à titre informatif seulement — ne constitue pas un conseil d'achat, de vente ou d'investissement</div>
</div>
<script>
function tog(h){{
  const sec = h.closest('.sec');
  const isOpen = sec.classList.contains('open');
  sec.classList.toggle('open');
  const chevron = h.querySelector('span:last-child');
  if (chevron) {{
    chevron.textContent = isOpen ? '▼' : '▲';
  }}
}}
</script>
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
    print(f"\n{'='*50}\nMORNING BRIEF - {datetime.now(BRIEF_TZ).strftime('%d/%m/%Y %H:%M')}\n{'='*50}")
    try:
        print("  1/4 Données marché...")
        market_data = fetch_brief_data()

        print("  2/4 Analyse...")
        analysis = generate_analysis(market_data)
        sv = analysis.get("score",{}).get("valeur",50)
        ss = analysis.get("score",{}).get("signal","Neutral")
        print(f"  Score: {sv}/100 — {ss}")

        print("  3/4 Génération HTML...")
        token = generate_daily_token()
        html  = build_brief_html(analysis, market_data, token)

        # Sauvegarder en mémoire ET en DB (persistant)
        _current_brief_html   = html
        _current_brief_date   = get_today_str()
        _current_brief_score  = sv
        _current_brief_signal = ss
        _save_brief(html, _current_brief_date, sv, ss)

        print("  4/4 Envoi membres...")
        members  = get_brief_recipients()
        tg_token = TELEGRAM_TOKEN or os.environ.get("TG_TOKEN","")
        admin_ch = TELEGRAM_CHAT  or os.environ.get("TG_CHAT","")
        base_url = os.environ.get("BASE_URL","https://web-production-34b51.up.railway.app")
        sent_e = sent_t = 0

        try:
            from app import _send_system_email as _send_fn
        except: _send_fn = None

        for m in members:
            if m.get("email") and _send_fn:
                try:
                    subj = f"📊 Morning Brief {datetime.now(BRIEF_TZ).strftime('%d/%m/%Y')} — {ss} ({sv}/100)"
                    ok, _ = _send_fn(m["email"], subj, build_brief_email_html(token, sv, ss))
                    if ok: sent_e += 1
                except Exception as e: print(f"  Email error {m.get('email')}: {e}")

            if m.get("tg_chat_id") and m["tg_chat_id"] != admin_ch and tg_token:
                try:
                    requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                        json={"chat_id":m["tg_chat_id"],"text":build_brief_telegram(analysis,token),"parse_mode":"HTML"},
                        timeout=5)
                    sent_t += 1
                except Exception as e: print(f"  Telegram error: {e}")

        if tg_token and admin_ch:
            try:
                requests.post(f"https://api.telegram.org/bot{tg_token}/sendMessage",
                    json={"chat_id":admin_ch,"text":build_brief_telegram(analysis,token),"parse_mode":"HTML"},
                    timeout=5)
            except Exception as e: print(f"  Admin Telegram error: {e}")

        print(f"\n  Done: {sent_e} email(s), {sent_t} Telegram(s)")
        base = os.environ.get("BASE_URL","https://web-production-34b51.up.railway.app")
        print(f"  Link: {base}/brief?token={token}\n")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        import traceback; traceback.print_exc()
