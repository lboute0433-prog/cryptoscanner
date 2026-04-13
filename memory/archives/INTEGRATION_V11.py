#!/usr/bin/env python3
"""
CryptoScanner Pro V11 — Patch d'intégration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ce fichier contient :
1. Les modifications à apporter à app.py
2. Les modifications à apporter à scanner_engine.py
3. Le fichier requirements_v11.txt à utiliser
4. Instructions de migration complètes

INSTRUCTIONS D'INSTALLATION
════════════════════════════

1. Copier les 3 nouveaux fichiers à la racine du projet :
   → security.py
   → forex_engine.py
   → indices_engine.py

2. Installer les nouvelles dépendances :
   pip install bcrypt cryptography pyotp qrcode[pil] yfinance

3. Appliquer les MODIFICATIONS ci-dessous dans app.py

4. Appliquer les MODIFICATIONS ci-dessous dans scanner_engine.py

5. Relancer l'application — les migrations DB s'appliquent automatiquement

"""

# ═══════════════════════════════════════════════════════════════
# MODIFICATIONS app.py
# ═══════════════════════════════════════════════════════════════
"""
──────────────────────────────────────────────────────────────
ÉTAPE 1 : Ajouter les imports (après les imports existants)
──────────────────────────────────────────────────────────────
Ajouter à la fin du bloc d'imports de app.py :

    from security import (
        init_security, apply_security_headers,
        hash_password, verify_password, needs_rehash, migrate_password_hash,
        check_rate_limit as sec_rate_limit,
        validate_username, validate_password,
        sanitize_symbol, sanitize_text,
        setup_totp, confirm_totp, verify_totp_login, disable_totp,
        save_exchange_keys_secure, get_exchange_keys_secure,
        get_security_events, vault,
    )
    from forex_engine import (
        forex_full_scan, fetch_all_pairs, analyze_forex_pair,
        get_session_overview, get_active_sessions,
        get_crypto_forex_correlations, init_forex_db,
    )
    from indices_engine import (
        fetch_all_indices, fetch_single_index,
        fetch_bybit_spot, fetch_bybit_perp, fetch_bybit_candles,
        fetch_okx_spot, fetch_okx_perp, fetch_okx_candles,
        fetch_multi_exchange, get_cross_market_analysis,
        calc_market_mood_score, init_indices_db,
    )

──────────────────────────────────────────────────────────────
ÉTAPE 2 : Modifier le démarrage de l'app (après init_cot_db())
──────────────────────────────────────────────────────────────
Remplacer :
    app = Flask(__name__)
    ...
    init_news_db()
    init_cot_db()

Par :
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "cryptoscanner_v11_" + os.urandom(16).hex()
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
    engine   = ScannerEngine()
    init_news_db()
    init_cot_db()
    init_forex_db()
    init_indices_db()
    # ── SÉCURITÉ V11 ──────────────────────────────────────────
    init_security()
    app.after_request(apply_security_headers)

──────────────────────────────────────────────────────────────
ÉTAPE 3 : Modifier le login pour bcrypt (dans /api/auth/login)
──────────────────────────────────────────────────────────────
Dans la méthode login_user() de scanner_engine.py :
Voir section "MODIFICATIONS scanner_engine.py" ci-dessous.

──────────────────────────────────────────────────────────────
ÉTAPE 4 : Modifier les routes exchange pour utiliser KeyVault
──────────────────────────────────────────────────────────────
Remplacer la route /api/exchange_connect/save_keys :

    @app.route("/api/exchange_connect/save_keys", methods=["POST"])
    def save_exchange_keys():
        data   = request.json
        exch   = data.get("exchange","")
        key    = data.get("api_key","")
        secret = data.get("api_secret","")
        if not key or not secret or not exch:
            return jsonify({"ok":False,"error":"Données manquantes"})
        # Utiliser le KeyVault pour chiffrer
        ok = save_exchange_keys_secure(get_uid(), exch, key, secret)
        return jsonify({"ok": ok, "message": f"Clés {exch} chiffrées et sauvegardées"})

──────────────────────────────────────────────────────────────
ÉTAPE 5 : Ajouter les routes 2FA TOTP
──────────────────────────────────────────────────────────────
Ajouter après la route /api/auth/enable_2fa :

    @app.route("/api/auth/setup_totp", methods=["POST"])
    def setup_totp_route():
        sess = get_session()
        if not sess: return jsonify({"ok":False}), 401
        data = setup_totp(sess["user_id"], sess["username"])
        return jsonify({"ok": True, **data})

    @app.route("/api/auth/confirm_totp", methods=["POST"])
    def confirm_totp_route():
        sess = get_session()
        if not sess: return jsonify({"ok":False}), 401
        code = request.json.get("code","")
        ok   = confirm_totp(sess["user_id"], code)
        return jsonify({"ok": ok, "error": "" if ok else "Code TOTP invalide"})

    @app.route("/api/auth/verify_totp", methods=["POST"])
    def verify_totp_route():
        data    = request.json
        user_id = data.get("user_id")
        code    = data.get("code","")
        if not user_id or not code:
            return jsonify({"ok":False,"error":"Données manquantes"})
        ok = verify_totp_login(int(user_id), code, get_ip())
        if ok:
            import sqlite3 as sq
            conn = sq.connect("cryptoscanner.db"); conn.row_factory = sq.Row
            user = conn.execute("SELECT id,username,role FROM users WHERE id=?",(user_id,)).fetchone()
            conn.close()
            if user:
                token = engine.create_session(user["id"], get_ip())
                resp  = make_response(jsonify({
                    "ok":True,"token":token,
                    "user_id":user["id"],"username":user["username"],"role":user["role"]
                }))
                resp.set_cookie("cs_token", token, max_age=86400, httponly=True, samesite="Lax")
                return resp
        return jsonify({"ok":False,"error":"Code invalide ou expiré"})

    @app.route("/api/auth/disable_totp", methods=["POST"])
    def disable_totp_route():
        sess = get_session()
        if not sess: return jsonify({"ok":False}), 401
        ok   = disable_totp(sess["user_id"])
        return jsonify({"ok": ok})

──────────────────────────────────────────────────────────────
ÉTAPE 6 : Ajouter les routes Forex
──────────────────────────────────────────────────────────────

    # ── FOREX ──────────────────────────────────────────────────
    @app.route("/api/forex/all")
    def api_forex_all():
        return jsonify(forex_full_scan())

    @app.route("/api/forex/pairs")
    def api_forex_pairs():
        category = request.args.get("category","all")
        pairs    = fetch_all_pairs()
        if category != "all":
            pairs = [p for p in pairs if p.get("category") == category]
        return jsonify(pairs)

    @app.route("/api/forex/pair/<pair>")
    def api_forex_pair(pair):
        pair    = pair.replace("-","/").upper()
        candles = None  # Sera chargé dans analyze_forex_pair
        signal  = analyze_forex_pair(pair, candles)
        return jsonify(signal or {"error": "Paire introuvable"})

    @app.route("/api/forex/sessions")
    def api_forex_sessions():
        return jsonify(get_session_overview())

    @app.route("/api/forex/correlations")
    def api_forex_correlations():
        minfo   = engine.get_market_info()
        btc_chg = 0
        coins   = engine.get_last().get("coins",[])
        btc     = next((c for c in coins if c["symbol"]=="BTC"),None)
        if btc: btc_chg = btc.get("change_pct",0)
        return jsonify(get_crypto_forex_correlations({"BTC":btc_chg}))

──────────────────────────────────────────────────────────────
ÉTAPE 7 : Ajouter les routes Indices
──────────────────────────────────────────────────────────────

    # ── INDICES ────────────────────────────────────────────────
    @app.route("/api/indices/all")
    def api_indices_all():
        keys = request.args.get("keys","").split(",") if request.args.get("keys") else None
        return jsonify(fetch_all_indices(keys))

    @app.route("/api/indices/<key>")
    def api_index_single(key):
        data = fetch_single_index(key.upper())
        return jsonify(data or {"error":"Indice introuvable"})

    @app.route("/api/indices/mood")
    def api_market_mood():
        indices = fetch_all_indices(["VIX","DXY","SP500"])
        minfo   = engine.get_market_info()
        coins   = engine.get_last().get("coins",[])
        btc     = next((c for c in coins if c["symbol"]=="BTC"),None)
        fg      = minfo.get("fear_greed",{}) or {}
        vix_d   = indices["indices"].get("VIX",{})
        dxy_d   = indices["indices"].get("DXY",{})
        sp5_d   = indices["indices"].get("SP500",{})
        mood    = calc_market_mood_score(
            vix        = vix_d.get("price"),
            fear_greed = fg.get("value"),
            dxy_change = dxy_d.get("change_pct"),
            sp500_change=sp5_d.get("change_pct"),
            btc_change = btc.get("change_pct",0) if btc else None,
        )
        return jsonify(mood)

    @app.route("/api/indices/cross_analysis")
    def api_cross_analysis():
        indices = fetch_all_indices(["VIX","DXY","SP500"])
        minfo   = engine.get_market_info()
        coins   = engine.get_last().get("coins",[])
        btc     = next((c for c in coins if c["symbol"]=="BTC"),None)
        fg      = minfo.get("fear_greed",{}) or {}
        vix_d   = indices["indices"].get("VIX",{})
        dxy_d   = indices["indices"].get("DXY",{})
        sp5_d   = indices["indices"].get("SP500",{})
        return jsonify(get_cross_market_analysis(
            btc_change   = btc.get("change_pct",0) if btc else 0,
            fear_greed   = fg.get("value",50),
            vix          = vix_d.get("price",18),
            dxy_change   = dxy_d.get("change_pct",0),
            sp500_change = sp5_d.get("change_pct",0),
        ))

──────────────────────────────────────────────────────────────
ÉTAPE 8 : Ajouter les routes exchanges Bybit / OKX
──────────────────────────────────────────────────────────────

    # ── BYBIT ──────────────────────────────────────────────────
    @app.route("/api/bybit/spot")
    def api_bybit_spot():
        coins = fetch_bybit_spot()
        return jsonify({"coins":coins,"count":len(coins),"ts":datetime.now().strftime("%H:%M:%S")})

    @app.route("/api/bybit/perp")
    def api_bybit_perp():
        perps = fetch_bybit_perp()
        return jsonify({"perps":perps,"count":len(perps),"ts":datetime.now().strftime("%H:%M:%S")})

    @app.route("/api/bybit/candles/<symbol>")
    def api_bybit_candles(symbol):
        interval = request.args.get("interval","1h")
        candles  = fetch_bybit_candles(sanitize_symbol(symbol), interval)
        return jsonify(candles)

    # ── OKX ────────────────────────────────────────────────────
    @app.route("/api/okx/spot")
    def api_okx_spot():
        coins = fetch_okx_spot()
        return jsonify({"coins":coins,"count":len(coins),"ts":datetime.now().strftime("%H:%M:%S")})

    @app.route("/api/okx/perp")
    def api_okx_perp():
        perps = fetch_okx_perp()
        return jsonify({"perps":perps,"count":len(perps),"ts":datetime.now().strftime("%H:%M:%S")})

    @app.route("/api/okx/candles/<symbol>")
    def api_okx_candles(symbol):
        interval = request.args.get("interval","1h")
        candles  = fetch_okx_candles(sanitize_symbol(symbol), interval)
        return jsonify(candles)

    # ── MULTI-EXCHANGE ─────────────────────────────────────────
    @app.route("/api/multi_exchange")
    def api_multi_exchange():
        exchanges = request.args.get("exchanges","bybit,okx").split(",")
        return jsonify(fetch_multi_exchange(exchanges))

──────────────────────────────────────────────────────────────
ÉTAPE 9 : Modifier le /api/exchange pour accepter bybit/okx
──────────────────────────────────────────────────────────────
Remplacer :
    if exchange not in ("binance","kraken"): return jsonify({"ok":False})

Par :
    if exchange not in ("binance","kraken","bybit","okx"): return jsonify({"ok":False})

"""


# ═══════════════════════════════════════════════════════════════
# MODIFICATIONS scanner_engine.py
# ═══════════════════════════════════════════════════════════════
"""
──────────────────────────────────────────────────────────────
ÉTAPE A : Remplacer hash_pw() par la version bcrypt
──────────────────────────────────────────────────────────────
Remplacer les lignes (87-88) :

    def hash_pw(pw):
        return hashlib.sha256(pw.encode()).hexdigest()

Par :

    def hash_pw(pw):
        # Compatibilité avec l'ancien code — délègue à security.py
        from security import hash_password
        return hash_password(pw)

──────────────────────────────────────────────────────────────
ÉTAPE B : Modifier create_user() pour valider et bcrypt
──────────────────────────────────────────────────────────────
Remplacer la méthode create_user (lignes 301-311) :

    def create_user(self, username, password, role="trader"):
        from security import validate_username, validate_password, hash_password
        ok_u, err_u = validate_username(username)
        if not ok_u:
            return {"ok":False, "error":err_u}
        ok_p, err_p = validate_password(password)
        if not ok_p:
            return {"ok":False, "error":err_p}
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute(
                "INSERT INTO users (username,password_hash,role,created,pw_algorithm) VALUES (?,?,?,?,?)",
                (username.lower(), hash_password(password), role,
                 datetime.now().isoformat(), "bcrypt")
            )
            conn.commit(); conn.close()
            return {"ok":True}
        except sqlite3.IntegrityError:
            conn.close(); return {"ok":False, "error":"Nom d'utilisateur déjà pris"}

──────────────────────────────────────────────────────────────
ÉTAPE C : Modifier login_user() pour bcrypt + migration auto
──────────────────────────────────────────────────────────────
Dans login_user() (ligne 313), modifier la requête SQL et vérification :

    def login_user(self, username, password, ip=""):
        from security import verify_password, needs_rehash, migrate_password_hash
        fails = self._count_recent_fails(username, ip)
        if fails >= MAX_LOGIN_ATTEMPTS:
            return {"ok":False, "error":f"Trop de tentatives. Réessaie dans 15 min."}

        conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
        # Récupérer l'utilisateur par username seulement (plus de hash dans la requête)
        row = conn.execute(
            "SELECT id,username,role,tfa_enabled,tg_chat_id,password_hash,totp_enabled FROM users WHERE username=?",
            (username.lower(),)
        ).fetchone()

        # Log tentative
        conn2 = sqlite3.connect(DB_PATH)
        conn2.execute("INSERT INTO login_attempts (username,ip,success,ts) VALUES (?,?,?,?)",
                     (username, ip, 1 if row else 0, datetime.now().isoformat()))
        conn2.commit(); conn2.close()

        if not row:
            conn.close(); return {"ok":False, "error":"Identifiants incorrects"}

        # Vérifier le mot de passe avec verify_password (bcrypt + fallback SHA-256)
        if not verify_password(password, row["password_hash"]):
            conn.close(); return {"ok":False, "error":"Identifiants incorrects"}

        user = dict(row)
        conn.execute("UPDATE users SET last_login=? WHERE id=?", (datetime.now().isoformat(), user["id"]))
        conn.commit(); conn.close()

        # Migration automatique SHA-256 → bcrypt au premier login réussi
        if needs_rehash(user["password_hash"]):
            migrate_password_hash(user["id"], password)

        # TOTP 2FA activé ? (nouveau système)
        if user.get("totp_enabled"):
            return {"ok":True, "requires_2fa":True, "tfa_type":"totp", "user_id":user["id"]}

        # Ancien 2FA Telegram
        if user["tfa_enabled"] and user["tg_chat_id"]:
            code = str(secrets.randbelow(900000) + 100000)
            exp  = (datetime.now() + timedelta(minutes=5)).isoformat()
            db   = sqlite3.connect(DB_PATH)
            db.execute("INSERT OR REPLACE INTO tfa_codes (user_id,code,expires) VALUES (?,?,?)",
                      (user["id"], code, exp))
            db.commit(); db.close()
            self._send_telegram_to(user["tg_chat_id"],
                f"🔐 <b>Code de connexion CryptoScanner</b>\\n\\n"
                f"Code : <b>{code}</b>\\nValable 5 minutes.")
            return {"ok":True, "requires_2fa":True, "tfa_type":"telegram", "user_id":user["id"]}

        token = self.create_session(user["id"], ip)
        self.log_action(user["id"], user["username"], "LOGIN", f"IP:{ip}", ip)
        return {"ok":True, "requires_2fa":False, "token":token,
                "user_id":user["id"], "username":user["username"], "role":user["role"]}

──────────────────────────────────────────────────────────────
ÉTAPE D : Modifier save/get exchange keys pour utiliser le vault
──────────────────────────────────────────────────────────────
Remplacer save_exchange_keys et get_exchange_keys dans ScannerEngine par :

    def save_exchange_keys(self, user_id, exchange, api_key, api_secret):
        from security import save_exchange_keys_secure
        return save_exchange_keys_secure(user_id, exchange, api_key, api_secret)

    def get_exchange_keys(self, user_id, exchange):
        from security import get_exchange_keys_secure
        return get_exchange_keys_secure(user_id, exchange)

──────────────────────────────────────────────────────────────
ÉTAPE E : Modifier admin_reset_password dans app.py
──────────────────────────────────────────────────────────────
Remplacer dans admin_reset_password :

    from scanner_engine import hash_pw
    conn.execute("UPDATE users SET password_hash=? WHERE id=?",(hash_pw(new_pw),uid))

Par :
    if len(new_pw) < 8: return jsonify({"ok":False,"error":"Mot de passe trop court (min 8)"})
    from security import hash_password
    conn.execute("UPDATE users SET password_hash=?, pw_algorithm=? WHERE id=?",
                 (hash_password(new_pw), "bcrypt", uid))

"""


# ═══════════════════════════════════════════════════════════════
# requirements_v11.txt
# ═══════════════════════════════════════════════════════════════
REQUIREMENTS_V11 = """
# CryptoScanner Pro V11 — Dépendances
# Installer avec : pip install -r requirements_v11.txt

# ── Existant ──────────────────────────────────────────────────
flask>=3.0.0
flask-socketio>=5.3.6
requests>=2.31.0
python-socketio>=5.10.0
eventlet>=0.35.1

# ── Sécurité V11 (NOUVEAU) ────────────────────────────────────
bcrypt>=4.1.0                  # Hash mots de passe sécurisé
cryptography>=42.0.0           # Chiffrement Fernet AES-256
pyotp>=2.9.0                   # TOTP 2FA (Google Authenticator)
qrcode[pil]>=7.4.2             # Génération QR Code

# ── Multi-marchés (NOUVEAU) ───────────────────────────────────
yfinance>=0.2.36               # Yahoo Finance (indices, ETFs, commodités)

# ── Optionnels ────────────────────────────────────────────────
# flask-limiter>=3.5.0         # Rate limiting avancé (optionnel, on a le nôtre)
# alpha-vantage>=2.3.1         # Données Forex avancées (nécessite clé API)
"""

if __name__ == "__main__":
    print("=" * 60)
    print("  CryptoScanner Pro V11 — Guide d'intégration")
    print("=" * 60)
    print()
    print("📦 Étape 1 : Installer les dépendances")
    print("   pip install bcrypt cryptography pyotp qrcode[pil] yfinance")
    print()
    print("📁 Étape 2 : Copier les fichiers")
    print("   → security.py")
    print("   → forex_engine.py")
    print("   → indices_engine.py")
    print()
    print("✏️  Étape 3 : Modifier app.py (voir commentaires dans ce fichier)")
    print("✏️  Étape 4 : Modifier scanner_engine.py (voir commentaires)")
    print()
    print("▶️  Étape 5 : python app.py")
    print("   Les migrations DB s'appliquent automatiquement au démarrage")
    print()
    print("🔐 Nouvelles fonctionnalités :")
    print("   • Mots de passe bcrypt (migration auto à la connexion)")
    print("   • Clés API chiffrées AES-256 (migration auto au démarrage)")
    print("   • TOTP 2FA compatible Google Authenticator")
    print("   • Headers sécurité HTTP (CSP, X-Frame-Options...)")
    print()
    print("🌍 Nouveaux marchés :")
    print("   • Forex : GET /api/forex/all")
    print("   • Sessions : GET /api/forex/sessions")
    print("   • Indices : GET /api/indices/all")
    print("   • Market Mood : GET /api/indices/mood")
    print("   • Bybit : GET /api/bybit/spot et /api/bybit/perp")
    print("   • OKX   : GET /api/okx/spot et /api/okx/perp")
    print("   • Arbitrage : GET /api/multi_exchange")
    print()
    print("🔑 Variables d'environnement optionnelles :")
    print("   VAULT_SECRET=...      # Clé maître chiffrement (auto-générée sinon)")
    print("   ALPHA_VANTAGE_KEY=... # Bougies Forex haute qualité")
    print("=" * 60)

    # Générer le fichier requirements
    with open("requirements_v11.txt", "w") as f:
        f.write(REQUIREMENTS_V11.strip())
    print("\n✅ requirements_v11.txt généré")
