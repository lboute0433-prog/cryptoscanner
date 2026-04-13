#!/usr/bin/env python3
"""CryptoScanner Pro V10 - Rapport + Bot Telegram + Abonnes"""

import os, time, threading, requests, sqlite3 as _sq
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config import DATABASE_PATH, TELEGRAM_CHAT, TELEGRAM_TOKEN, TELEGRAM_CHAT_FREE, SITE_URL

TG_TOKEN    = TELEGRAM_TOKEN
TG_CHAT     = TELEGRAM_CHAT
REPORT_HOUR = int(os.environ.get("REPORT_HOUR", "8"))
REPORT_TZ   = ZoneInfo(os.environ.get("REPORT_TIMEZONE", "Europe/Paris"))

FR_MONTHS = ["janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]


def format_fr_date(dt=None):
    dt = dt or datetime.now(REPORT_TZ)
    return f"{dt.day} {FR_MONTHS[dt.month-1]} {dt.year}"

# Systeme abonnes
def _init_subscribers_db():
    try:
        conn = _sq.connect(DATABASE_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tg_subscribers (
                chat_id   TEXT PRIMARY KEY,
                username  TEXT DEFAULT \'\',
                status    TEXT DEFAULT \'pending\',
                requested TEXT DEFAULT \'\',
                approved  TEXT DEFAULT \'\'
            )
        """)
        conn.commit(); conn.close()
    except: pass

_init_subscribers_db()

def get_subscribers(status="approved"):
    try:
        conn = _sq.connect(DATABASE_PATH); conn.row_factory = _sq.Row
        rows = conn.execute("SELECT * FROM tg_subscribers WHERE status=?", (status,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except: return []

def get_all_recipients():
    recipients = set()
    chat = os.environ.get("TG_CHAT", TG_CHAT)
    if chat: recipients.add(chat)
    for s in get_subscribers("approved"): recipients.add(s["chat_id"])
    return list(recipients)

def add_subscriber(chat_id, username=""):
    try:
        conn = _sq.connect(DATABASE_PATH)
        conn.execute(
            "INSERT OR IGNORE INTO tg_subscribers (chat_id,username,status,requested) VALUES (?,?,?,?)",
            (str(chat_id), username, datetime.now(REPORT_TZ).isoformat())
        )
        conn.commit(); conn.close()
        return True
    except: return False

def update_subscriber(chat_id, status):
    try:
        conn = _sq.connect(DATABASE_PATH)
        conn.execute(
            "UPDATE tg_subscribers SET status=?, approved=? WHERE chat_id=?",
            (status, datetime.now(REPORT_TZ).isoformat(), str(chat_id))
        )
        conn.commit(); conn.close()
        return True
    except: return False

# Niveaux d'accès Telegram (synchronisés avec scanner_engine._TG_ROLE_TIERS)
_TG_ROLE_TIERS = {
    "member": ("member", "paid", "vip", "admin"),
    "paid":   ("paid",   "vip", "admin"),
    "vip":    ("vip",    "admin"),
    "admin":  ("admin",),
}

def get_members_by_role(min_role: str = "member"):
    """Retourne les tg_chat_id des membres dont le rôle est >= min_role."""
    allowed = _TG_ROLE_TIERS.get(min_role, _TG_ROLE_TIERS["member"])
    try:
        conn = _sq.connect(DATABASE_PATH); conn.row_factory = _sq.Row
        ph   = ",".join("?" * len(allowed))
        rows = conn.execute(
            f"SELECT tg_chat_id FROM users WHERE tg_chat_id != '' AND tg_chat_id IS NOT NULL AND role IN ({ph})",
            allowed
        ).fetchall()
        conn.close()
        return [r["tg_chat_id"] for r in rows]
    except: return []

# Envoi Telegram
def send_telegram(msg, chat_id=None, broadcast=False, min_role: str = "member"):
    """
    Envoie un message Telegram.
    - chat_id  : envoi direct à un utilisateur
    - broadcast=True : envoi à tous les subscribers approuvés (tg_subscribers)
    - min_role : "member" (tous) | "paid" (payants+VIP) | "vip" (VIP seul)
                 Si broadcast=True, filtre les membres de la table users par rôle.
    """
    token = os.environ.get("TG_TOKEN", TG_TOKEN)
    chat  = os.environ.get("TG_CHAT",  TG_CHAT)
    if not token: return False

    if broadcast:
        # Combinaison : subscribers approuvés + membres par rôle
        targets = set(get_all_recipients())
        for cid in get_members_by_role(min_role):
            targets.add(cid)
    else:
        targets = [chat_id or chat]

    ok = False
    for cid in targets:
        if not cid: continue
        try:
            requests.post(
                "https://api.telegram.org/bot" + token + "/sendMessage",
                json={"chat_id": cid, "text": msg, "parse_mode": "HTML"},
                timeout=8
            )
            ok = True
        except: pass
    return ok

def _send_admin(msg):
    token = os.environ.get("TG_TOKEN", TG_TOKEN)
    chat  = os.environ.get("TG_CHAT",  TG_CHAT)
    if not token or not chat: return
    try:
        requests.post(
            "https://api.telegram.org/bot" + token + "/sendMessage",
            json={"chat_id": chat, "text": msg, "parse_mode": "HTML"},
            timeout=8
        )
    except: pass


def post_to_free_channel(msg: str) -> bool:
    """Poste un message sur le canal Telegram public FREE."""
    token = os.environ.get("TG_TOKEN", TG_TOKEN)
    chat  = os.environ.get("TG_CHAT_FREE", TELEGRAM_CHAT_FREE)
    if not token or not chat:
        return False
    try:
        requests.post(
            "https://api.telegram.org/bot" + token + "/sendMessage",
            json={"chat_id": chat, "text": msg, "parse_mode": "HTML"},
            timeout=8
        )
        return True
    except:
        return False

# Rapport journalier
def build_daily_report(engine, news_fn, etf_fn, cal_fn):
    now   = datetime.now(REPORT_TZ)
    today = format_fr_date(now)
    lines = [
        "Rapport Journalier - CryptoScanner Pro",
        "Date: " + today + " | " + now.strftime("%H:%M"),
        "=" * 30,
    ]
    try:
        market  = engine.get_last()
        coins   = market.get("coins", [])
        signals = market.get("signals", [])
        gainers = len([c for c in coins if c["change_pct"] > 0])
        losers  = len([c for c in coins if c["change_pct"] < 0])
        vol     = sum(c["volume_usdt"] for c in coins)
        top3g   = sorted(coins, key=lambda x: x["change_pct"], reverse=True)[:3]
        top3d   = sorted(coins, key=lambda x: x["change_pct"])[:3]
        minfo   = engine.get_market_info() or {}
        fg      = minfo.get("fear_greed", {}) or {}
        dom     = minfo.get("dominance", {}) or {}
        sent    = "HAUSSIER" if gainers > losers else "BAISSIER"
        lines.append("\nMARCHE CRYPTO")
        lines.append("Sentiment: " + sent)
        lines.append(str(gainers) + " hausse / " + str(losers) + " baisse")
        lines.append("Volume 24h: $" + str(round(vol/1e9,2)) + "B")
        if fg.get("value"):
            lines.append("Fear and Greed: " + str(fg["value"]) + "/100 - " + fg.get("label",""))
        if dom.get("btc"):
            lines.append("BTC Dominance: " + str(dom["btc"]) + "%")
        if top3g:
            lines.append("\nTop Gains:")
            for c in top3g:
                lines.append("  " + c["symbol"] + ": +" + str(round(c["change_pct"],2)) + "%")
        if top3d:
            lines.append("\nTop Pertes:")
            for c in top3d:
                lines.append("  " + c["symbol"] + ": " + str(round(c["change_pct"],2)) + "%")
        if signals:
            lines.append("\nSignaux actifs: " + str(len(signals)))
    except Exception as e:
        lines.append("Erreur marche: " + str(e))

    try:
        etf_data = etf_fn()
        total_btc = etf_data.get("total_1d_btc", etf_data.get("total_1d", 0))
        total_eth = etf_data.get("total_1d_eth", 0)
        btc_sign  = "+" if total_btc >= 0 else ""
        eth_sign  = "+" if total_eth >= 0 else ""
        btc_etfs  = [e for e in etf_data.get("etfs", []) if e.get("asset") in ("", None, "BTC")]
        eth_etfs  = [e for e in etf_data.get("etfs", []) if e.get("asset") == "ETH"]
        lines.append("\nFLUX ETF")
        lines.append("BTC: " + btc_sign + "$" + str(round(total_btc,1)) + "M")
        for etf in btc_etfs[:4]:
            f2 = etf.get("flow_1d",0)
            s2 = "+" if f2 >= 0 else ""
            lines.append("  " + etf.get("ticker","?") + ": " + s2 + "$" + str(round(f2,1)) + "M")
        if eth_etfs or total_eth:
            lines.append("ETH: " + eth_sign + "$" + str(round(total_eth,1)) + "M")
            for etf in eth_etfs[:4]:
                f2 = etf.get("flow_1d",0)
                s2 = "+" if f2 >= 0 else ""
                lines.append("  " + etf.get("ticker","?") + ": " + s2 + "$" + str(round(f2,1)) + "M")
    except Exception as e:
        lines.append("Erreur ETF: " + str(e))

    try:
        if news_fn:
            news = news_fn(limit=5, critical_only=True, lang="fr")
            if news:
                lines.append("\nNEWS CRITIQUES")
                for n in news[:5]:
                    lines.append("  - " + n.get("title","")[:80])
    except Exception as e:
        lines.append("Erreur news: " + str(e))

    try:
        cal_data = cal_fn(view="day")
        events   = cal_data.get("events", [])
        if events:
            lines.append("\nEVENEMENTS AUJOURD\'HUI")
            for ev in events[:6]:
                imp = ev.get("impact","")
                lines.append("  " + ev.get("time","") + " - " + ev["title"] + " (" + ev["currency"] + ")")
        else:
            lines.append("\nAucun evenement majeur aujourd\'hui")
    except Exception as e:
        lines.append("Erreur calendrier: " + str(e))

    # ── Marchés globaux : Or, Pétrole, Dollar, Indices ──────────
    try:
        from indices_engine import fetch_all_indices
        idx  = fetch_all_indices(["GOLD","OIL_WTI","DXY","SP500","VIX"])
        idxd = idx.get("indices", {})
        if idxd:
            lines.append("\nMARCHES GLOBAUX")
            labels = [("GOLD","Or 🥇"),("OIL_WTI","Pétrole WTI 🛢️"),
                      ("DXY","Dollar DXY 💵"),("SP500","S&P 500 📈"),("VIX","VIX 😱")]
            for key, lbl in labels:
                d = idxd.get(key)
                if not d or d.get("demo"): continue
                chg  = d.get("change_pct", 0)
                sign = "+" if chg >= 0 else ""
                arr  = "📈" if chg > 0.2 else "📉" if chg < -0.2 else "➡️"
                lines.append(f"  {arr} {lbl}: ${d.get('price',0):,.2f} ({sign}{round(chg,2)}%)")
    except Exception as e:
        lines.append("Indices: " + str(e))

    # ── Forex ─────────────────────────────────────────────────
    try:
        from forex_engine import fetch_forex_rates
        rates = fetch_forex_rates("USD").get("rates", {})
        if rates:
            lines.append("\nFOREX")
            eur = rates.get("EUR")
            gbp = rates.get("GBP")
            jpy = rates.get("JPY")
            if eur: lines.append(f"  EUR/USD: {round(1/eur,4)}")
            if gbp: lines.append(f"  GBP/USD: {round(1/gbp,4)}")
            if jpy: lines.append(f"  USD/JPY: {round(jpy,2)}")
    except: pass

    lines.append("\n" + "=" * 30)
    lines.append("CryptoScanner Pro V10 - " + now.strftime("%H:%M"))
    return "\n".join(lines)

def build_etf_report(etf_fn):
    now   = datetime.now(REPORT_TZ)
    lines = ["Rapport ETF - " + format_fr_date(now), "=" * 30]
    try:
        etf_data = etf_fn()
        total_btc = etf_data.get("total_1d_btc", etf_data.get("total_1d", 0))
        total_eth = etf_data.get("total_1d_eth", 0)
        btc_etfs  = [e for e in etf_data.get("etfs", []) if e.get("asset") in ("", None, "BTC")]
        eth_etfs  = [e for e in etf_data.get("etfs", []) if e.get("asset") == "ETH"]
        lines.append("\nBILAN JOURNALIER")
        lines.append("BTC Total: " + ("+" if total_btc >= 0 else "") + "$" + str(round(total_btc,1)) + "M")
        for etf in btc_etfs:
            f2   = etf.get("flow_1d", 0)
            s2   = "+" if f2 >= 0 else ""
            aum  = etf.get("aum",0)
            lines.append(etf.get("ticker","?") + " " + etf.get("name","")[:20])
            lines.append("  Flux: " + s2 + "$" + str(round(f2,1)) + "M | AUM: $" + str(round(aum/1e3,1)) + "B")
        if eth_etfs or total_eth:
            lines.append("")
            lines.append("ETH Total: " + ("+" if total_eth >= 0 else "") + "$" + str(round(total_eth,1)) + "M")
            for etf in eth_etfs:
                f2   = etf.get("flow_1d", 0)
                s2   = "+" if f2 >= 0 else ""
                aum  = etf.get("aum",0)
                lines.append(etf.get("ticker","?") + " " + etf.get("name","")[:20])
                lines.append("  Flux: " + s2 + "$" + str(round(f2,1)) + "M | AUM: $" + str(round(aum/1e3,1)) + "B")
    except Exception as e:
        lines.append("Erreur: " + str(e))
    lines.append("\nCryptoScanner Pro V10 - " + now.strftime("%H:%M"))
    return "\n".join(lines)

def _post_daily_summary_to_free(engine):
    """Poste un résumé de marché simplifié sur le canal Telegram FREE."""
    try:
        now    = datetime.now(REPORT_TZ)
        market = engine.get_last()
        coins  = market.get("coins", [])
        gainers = len([c for c in coins if c["change_pct"] > 0])
        losers  = len([c for c in coins if c["change_pct"] < 0])
        vol     = sum(c["volume_usdt"] for c in coins)
        top3g   = sorted(coins, key=lambda x: x["change_pct"], reverse=True)[:3]
        sent    = "🟢 HAUSSIER" if gainers > losers else "🔴 BAISSIER"
        site    = os.environ.get("SITE_URL", SITE_URL)

        gains_lines = ""
        for c in top3g:
            gains_lines += f"  • {c['symbol']}: +{round(c['change_pct'],1)}%\n"

        msg = (
            f"📊 <b>Rapport de marché — {format_fr_date(now)}</b>\n\n"
            f"Sentiment : {sent}\n"
            f"Volume 24h : <b>${round(vol/1e9,1)}B</b>\n"
            f"Hausses / Baisses : {gainers} / {losers}\n\n"
            f"🏆 <b>Top Gains :</b>\n{gains_lines}\n"
            f"📈 Signaux détaillés et alertes PREMIUM :\n"
            f"<a href=\"{site}\">{site}</a>\n\n"
            f"<i>🚫 Données techniques à titre informatif uniquement.</i>"
        )
        post_to_free_channel(msg)
    except Exception as e:
        print(f"[DailyReport] _post_daily_summary_to_free: {e}")


# Scheduler
class DailyReportScheduler:
    def __init__(self, engine, etf_fn, cal_fn):
        self.engine  = engine
        self.etf_fn  = etf_fn
        self.cal_fn  = cal_fn
        self._thread = None
        # Démarrer en différé pour laisser gunicorn/eventlet s'initialiser
        threading.Timer(5.0, self._start).start()

    def _start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        last_date = None
        while True:
            now = datetime.now(REPORT_TZ)
            if now.hour == REPORT_HOUR and now.date() != last_date:
                try:
                    from news_macro import get_news_from_db
                    report = build_daily_report(self.engine, get_news_from_db, self.etf_fn, self.cal_fn)
                    send_telegram(report, broadcast=True)
                    # Résumé simplifié sur le canal FREE public
                    try:
                        _post_daily_summary_to_free(self.engine)
                    except Exception as _fe:
                        print(f"[DailyReport] FREE channel: {_fe}")
                    # Lancer aussi le Morning Brief IA
                    import threading as _thr
                    try:
                        from morning_brief import run_morning_brief
                        _thr.Thread(target=run_morning_brief, daemon=True).start()
                        print("[DailyReport] Morning Brief IA lancé")
                    except Exception as _e:
                        print(f"[DailyReport] Morning Brief erreur: {_e}")
                    last_date = now.date()
                    print("[DailyReport] Envoye a " + now.strftime("%H:%M"))
                except Exception as e:
                    print("[DailyReport] Erreur: " + str(e))
            time.sleep(60)

    def send_now(self, chat_id=None):
        try:
            from news_macro import get_news_from_db
            report = build_daily_report(self.engine, get_news_from_db, self.etf_fn, self.cal_fn)
            send_telegram(report, chat_id=chat_id)
            return True
        except Exception as e:
            print("[DailyReport] send_now: " + str(e))
            return False

    def send_etf_report(self, chat_id=None):
        try:
            report = build_etf_report(self.etf_fn)
            send_telegram(report, chat_id=chat_id)
            return True
        except Exception as e:
            print("[DailyReport] send_etf: " + str(e))
            return False

# Bot Telegram
class TelegramBot:
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self._offset   = 0
        self._thread   = None
        # Démarrer en différé
        threading.Timer(8.0, self._start).start()

    def _start(self):
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def _poll_loop(self):
        while True:
            token = os.environ.get("TG_TOKEN", TG_TOKEN)
            if not token: time.sleep(15); continue
            try:
                r = requests.get(
                    "https://api.telegram.org/bot" + token + "/getUpdates",
                    params={"offset": self._offset, "timeout": 30},
                    timeout=35
                )
                for update in r.json().get("result", []):
                    self._offset = update["update_id"] + 1
                    self._handle(update)
            except Exception as e:
                print("[TGBot] " + str(e))
                time.sleep(5)

    def _handle(self, update):
        msg      = update.get("message", {})
        text     = msg.get("text", "").strip().lower()
        chat_id  = str(msg.get("chat", {}).get("id", ""))
        sender   = msg.get("from", {})
        username = sender.get("username","") or sender.get("first_name","Inconnu")
        if not text or not chat_id: return

        if text in ("/rapport", "/report", "/daily"):
            send_telegram("Generation du rapport...", chat_id=chat_id)
            self.scheduler.send_now(chat_id)

        elif text in ("/etf", "/fluxetf"):
            send_telegram("Rapport ETF...", chat_id=chat_id)
            self.scheduler.send_etf_report(chat_id)

        elif text in ("/news", "/actu"):
            send_telegram("Resume news...", chat_id=chat_id)
            try:
                from news_macro import get_news_from_db, translate_news_batch
                news = get_news_from_db(limit=12, lang="fr")
                if len(news) < 8:
                    mixed = get_news_from_db(limit=8, lang=None, prefer_lang="fr")
                    seen = {n.get("url") for n in news}
                    for item in mixed:
                        if item.get("url") not in seen:
                            news.append(item)
                            seen.add(item.get("url"))
                        if len(news) >= 15:
                            break
                news = translate_news_batch(news[:15], "fr")
                if not news:
                    send_telegram("Aucune news.", chat_id=chat_id)
                else:
                    cats = {}
                    for n in news:
                        cat = n.get("category","general")
                        cats.setdefault(cat,[]).append(n)
                    labels = {
                        "critical":"CRITIQUES","market":"MARCHE",
                        "regulation":"REGULATION","institutional":"INSTITUTIONNEL",
                        "technology":"TECH","macro":"MACRO",
                        "security":"SECURITE","whale":"WHALE","general":"GENERAL",
                        "adoption":"ADOPTION","geopolitics":"GEOPOLITIQUE"
                    }
                    out = ["DERNIERES NEWS CRYPTO - PRIORITE FR\n"]
                    for cat, items in list(cats.items())[:5]:
                        out.append("\n" + labels.get(cat, cat.upper()))
                        for n in items[:3]:
                            title = n.get("title","")
                            out.append("- " + title[:100])
                            out.append("  " + n.get("source","") + " " + n.get("published","")[:10])
                    send_telegram("\n".join(out), chat_id=chat_id)
            except Exception as e:
                send_telegram("Erreur: " + str(e), chat_id=chat_id)

        elif text in ("/subscribe", "/abonner"):
            try:
                conn = _sq.connect(DATABASE_PATH); conn.row_factory = _sq.Row
                existing = conn.execute("SELECT * FROM tg_subscribers WHERE chat_id=?", (chat_id,)).fetchone()
                conn.close()
            except: existing = None

            if existing:
                status = dict(existing).get("status","pending")
                msgs = {"approved":"Tu es deja abonne!","pending":"Demande en attente.","rejected":"Demande refusee."}
                send_telegram(msgs.get(status,"?"), chat_id=chat_id)
            else:
                add_subscriber(chat_id, username)
                send_telegram("Demande envoyee! L\'admin doit valider.", chat_id=chat_id)
                _send_admin(
                    "Nouvelle demande abonnement\n" +
                    "Utilisateur: " + username + "\n" +
                    "Chat ID: " + chat_id + "\n\n" +
                    "Approuver: /approve " + chat_id + "\n" +
                    "Refuser: /reject " + chat_id
                )

        elif text.startswith("/approve "):
            if chat_id != TG_CHAT:
                send_telegram("Reserve a l\'admin.", chat_id=chat_id)
            else:
                target = text.split(" ", 1)[1].strip()
                if update_subscriber(target, "approved"):
                    send_telegram("Approuve: " + target, chat_id=chat_id)
                    send_telegram(
                        "Abonnement approuve! Tu vas recevoir les alertes.\nTape /aide pour les commandes.",
                        chat_id=target
                    )
                else:
                    send_telegram("Erreur pour " + target, chat_id=chat_id)

        elif text.startswith("/reject "):
            if chat_id != TG_CHAT:
                send_telegram("Reserve a l\'admin.", chat_id=chat_id)
            else:
                target = text.split(" ", 1)[1].strip()
                if update_subscriber(target, "rejected"):
                    send_telegram("Rejete: " + target, chat_id=chat_id)
                    send_telegram("Ta demande a ete refusee.", chat_id=target)
                else:
                    send_telegram("Erreur pour " + target, chat_id=chat_id)

        elif text in ("/subscribers", "/abonnes"):
            if chat_id != TG_CHAT:
                send_telegram("Reserve a l\'admin.", chat_id=chat_id)
            else:
                approved = get_subscribers("approved")
                pending  = get_subscribers("pending")
                out = ["ABONNES (" + str(len(approved)) + " approuves)\n"]
                for s in approved:
                    out.append("OK " + s.get("username","?") + " - " + s["chat_id"])
                if not approved:
                    out.append("Aucun abonne approuve.")
                if pending:
                    out.append("\nEN ATTENTE (" + str(len(pending)) + ")")
                    for s in pending:
                        out.append("- " + s.get("username","?") + " - " + s["chat_id"])
                        out.append("  /approve " + s["chat_id"] + " | /reject " + s["chat_id"])
                send_telegram("\n".join(out), chat_id=chat_id)

        elif text.startswith("/broadcast "):
            if chat_id != TG_CHAT:
                send_telegram("Reserve a l\'admin.", chat_id=chat_id)
            else:
                bcast = text[len("/broadcast "):].strip()
                if bcast:
                    send_telegram("Message admin:\n\n" + bcast, broadcast=True)
                    send_telegram("Message envoye a tous.", chat_id=chat_id)

        elif text.startswith("/backtest "):
            # /backtest BTC rsi 1h — lance un backtest rapide
            send_telegram("⏳ Backtest en cours...", chat_id=chat_id)
            try:
                parts    = text.split()
                symbol   = parts[1].upper() if len(parts)>1 else "BTC"
                strategy = parts[2].lower()  if len(parts)>2 else "rsi_reversal"
                interval = parts[3]           if len(parts)>3 else "1h"
                from backtest_engine import run_backtest
                r = run_backtest(symbol, strategy, interval, 1000.0)
                if r.get("ok"):
                    s = r["stats"]
                    pnl_col = "📈" if s["pnl_pct"] >= 0 else "📉"
                    msg = (
                        f"📊 <b>BACKTEST — {symbol}/USDT</b>\n"
                        f"Stratégie: <b>{r['strategy']}</b> ({interval})\n"
                        f"Période: {r['period']}\n\n"
                        f"{pnl_col} PnL: <b>{'+'if s['pnl_pct']>=0 else ''}{s['pnl_pct']}%</b>\n"
                        f"🎯 Win Rate: <b>{s['win_rate']}%</b>\n"
                        f"📦 Trades: {s['total_trades']} ({s['winners']}W / {s['losers']}L)\n"
                        f"💧 Max Drawdown: -{s['max_drawdown']}%\n"
                        f"📐 Sharpe: {s['sharpe']}\n"
                        f"💰 Capital final: ${s['final_capital']:,.0f}\n\n"
                        f"<i>⚠️ Backtest ne garantit pas les performances futures</i>"
                    )
                    send_telegram(msg, chat_id=chat_id)
                else:
                    send_telegram("❌ " + r.get("error","Erreur backtest"), chat_id=chat_id)
            except Exception as e:
                send_telegram("❌ Erreur: "+str(e), chat_id=chat_id)

        elif text in ("/start", "/aide", "/help"):
            site = os.environ.get("SITE_URL", SITE_URL)
            send_telegram(
                "👋 <b>Bienvenue sur CryptoScanner Pro</b>\n\n"
                "📊 Signaux crypto en temps réel — Smart Signals, Retrace RSI, Flux ETF, Macro.\n\n"
                "<b>🆓 Accès FREE (ce canal public)</b>\n"
                "→ News crypto importantes\n"
                "→ Alertes PUMP / DUMP basiques\n"
                "→ Rapport de marché quotidien\n\n"
                "<b>💎 Accès PREMIUM (DM direct)</b>\n"
                "→ Smart Signals détaillés (entrée, cible, stop)\n"
                "→ Retrace RSI — sortie de surachat/survente\n"
                "→ Alertes macro ForexFactory\n"
                "→ Toutes les alertes en avant-première\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "🔗 <b>Créer votre compte :</b>\n"
                f"<a href=\"{site}/register\">{site}/register</a>\n\n"
                "Après inscription, utilisez <b>/lier</b> pour recevoir vos alertes personnalisées.\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "<b>COMMANDES DISPONIBLES</b>\n"
                "/rapport — Rapport journalier complet\n"
                "/etf — Flux ETF Bitcoin & Ethereum\n"
                "/news — Dernières news crypto FR\n"
                "/backtest BTC rsi 1h — Backtest rapide\n"
                "/lier — Lier ce Telegram à votre compte site\n\n"
                "<i>🚫 Ceci ne constitue pas un conseil d\'achat ou de vente. "
                "CryptoScanner Pro fournit uniquement des données techniques à titre informatif.</i>",
                chat_id=chat_id
            )

        elif text in ("/lier", "/link", "/connect"):
            site = os.environ.get("SITE_URL", SITE_URL)
            send_telegram(
                "🔗 <b>Lier votre compte CryptoScanner Pro</b>\n\n"
                "Votre <b>Chat ID Telegram</b> :\n"
                f"<code>{chat_id}</code>\n\n"
                "<b>Étapes :</b>\n"
                f"1️⃣ Connectez-vous sur <a href=\"{site}\">{site}</a>\n"
                "2️⃣ Allez dans <b>Profil → Notifications Telegram</b>\n"
                "3️⃣ Collez votre Chat ID ci-dessus\n"
                "4️⃣ Enregistrez — vos alertes PREMIUM seront activées\n\n"
                "✅ Une fois lié, vous recevrez automatiquement les signaux selon votre niveau d'accès.\n\n"
                "<i>Pas encore de compte ? → /start</i>",
                chat_id=chat_id
            )
