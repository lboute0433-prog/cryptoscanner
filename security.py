#!/usr/bin/env python3
"""
CryptoScanner Pro V11 — Module Sécurité
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• bcrypt (hash mots de passe avec salage)
• KeyVault (chiffrement Fernet AES-256 des clés API exchange)
• TOTP 2FA (Google Authenticator / Authy)
• Rate Limiting par IP (en mémoire, thread-safe)
• Headers HTTP sécurité (CSP, HSTS, X-Frame-Options...)
• Sanitisation / validation des inputs
• Audit trail complet
"""

import os
import base64
import hashlib
import hmac
import secrets
import sqlite3
import threading
import time
import re
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple

try:
    from flask import request
except Exception:
    request = None

from db import get_connection  # noqa: E402

# ── Dépendances optionnelles avec fallbacks ───────────────────
try:
    import bcrypt
    _BCRYPT_AVAILABLE = True
except ImportError:
    _BCRYPT_AVAILABLE = False
    print("[Security] bcrypt non installe - pip install bcrypt")

try:
    from cryptography.fernet import Fernet, InvalidToken
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False
    print("[Security] cryptography non installe - pip install cryptography")

try:
    import pyotp
    import qrcode
    import io
    _TOTP_AVAILABLE = True
except ImportError:
    _TOTP_AVAILABLE = False
    print("[Security] pyotp non installe - pip install pyotp qrcode[pil]")

DB_PATH = "cryptoscanner.db"

# ══════════════════════════════════════════════════════════════
# 1. HASH MOT DE PASSE — bcrypt avec salage automatique
# ══════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    """
    Hash un mot de passe avec bcrypt (salage automatique, 12 rounds).
    Remplace l'ancien hash_pw() SHA-256 sans salage.
    """
    if not password:
        raise ValueError("Mot de passe vide")
    if _BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")
    else:
        # Fallback SHA-256 avec sel si bcrypt absent (moins sécurisé)
        salt = secrets.token_hex(32)
        h = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"sha256:{salt}:{h}"


def verify_password(password: str, hashed: str) -> bool:
    """Vérifie un mot de passe contre son hash (bcrypt ou fallback)."""
    if not password or not hashed:
        return False
    try:
        if _BCRYPT_AVAILABLE and not hashed.startswith("sha256:"):
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        elif hashed.startswith("sha256:"):
            # Fallback SHA-256
            _, salt, stored_hash = hashed.split(":", 2)
            h = hashlib.sha256((salt + password).encode()).hexdigest()
            return hmac.compare_digest(h, stored_hash)
        else:
            # Anciens hashes SHA-256 purs (migration)
            old_hash = hashlib.sha256(password.encode()).hexdigest()
            return hmac.compare_digest(old_hash, hashed)
    except Exception:
        return False


def migrate_password_hash(user_id: int, password: str) -> bool:
    """
    Migre un ancien hash SHA-256 vers bcrypt.
    À appeler lors du premier login réussi d'un utilisateur existant.
    """
    new_hash = hash_password(password)
    try:
        conn = get_connection()
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        conn.commit(); conn.close()
        return True
    except Exception:
        return False


def needs_rehash(hashed: str) -> bool:
    """Retourne True si le hash est un ancien SHA-256 qui doit être migré."""
    return not hashed.startswith("$2b$") and not hashed.startswith("sha256:")


# ══════════════════════════════════════════════════════════════
# 2. KEY VAULT — Chiffrement AES-256 (Fernet) des clés API
# ══════════════════════════════════════════════════════════════

class KeyVault:
    """
    Chiffre/déchiffre les clés API exchange avec Fernet (AES-128-CBC + HMAC-SHA256).
    La clé maître est dérivée d'un secret applicatif stocké en variable d'environnement.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._cipher = None
                cls._instance._init_cipher()
        return cls._instance

    def _init_cipher(self):
        """Initialise le cipher depuis VAULT_SECRET (env) ou génère + sauvegarde."""
        if not _FERNET_AVAILABLE:
            self._cipher = None
            return

        master = os.environ.get("VAULT_SECRET", "")
        if not master:
            # Générer et sauvegarder dans le fichier .vault_key (local uniquement)
            vault_file = ".vault_key"
            if os.path.exists(vault_file):
                with open(vault_file, "r") as f:
                    master = f.read().strip()
            else:
                master = secrets.token_urlsafe(48)
                with open(vault_file, "w") as f:
                    f.write(master)
                # Protéger le fichier (Unix uniquement)
                try:
                    os.chmod(vault_file, 0o600)
                except Exception:
                    pass
                print(f"[KeyVault] Cle maitre generee dans {vault_file}")

        # Dériver une clé Fernet valide (32 bytes, base64url)
        key_bytes = hashlib.sha256(master.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        self._cipher = Fernet(fernet_key)

    def encrypt(self, plaintext: str) -> str:
        """Chiffre une chaîne. Retourne le texte chiffré Fernet."""
        if not plaintext:
            return ""
        if not _FERNET_AVAILABLE or self._cipher is None:
            raise RuntimeError(
                "[KeyVault] Chiffrement impossible : bibliothèque 'cryptography' manquante. "
                "Installez-la avec : pip install cryptography"
            )
        return self._cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Déchiffre une chaîne chiffrée par encrypt()."""
        if not ciphertext:
            return ""
        if not _FERNET_AVAILABLE or self._cipher is None:
            raise RuntimeError(
                "[KeyVault] Déchiffrement impossible : bibliothèque 'cryptography' manquante. "
                "Installez-la avec : pip install cryptography"
            )
        try:
            return self._cipher.decrypt(ciphertext.encode()).decode()
        except (InvalidToken, Exception):
            # Peut-être déjà en clair (ancienne DB) — retourner tel quel
            return ciphertext

    def is_encrypted(self, value: str) -> bool:
        """Détecte si une valeur est chiffrée par ce vault (Fernet)."""
        if not value:
            return False
        # Les tokens Fernet commencent toujours par "gAAA"
        return value.startswith("gAAA")

    def encrypt_if_needed(self, value: str) -> str:
        """Chiffre seulement si pas déjà chiffré (migration)."""
        if self.is_encrypted(value):
            return value
        return self.encrypt(value)


# Instance globale singleton
vault = KeyVault()


# ══════════════════════════════════════════════════════════════
# 3. TOTP 2FA — Google Authenticator / Authy
# ══════════════════════════════════════════════════════════════

class TOTPManager:
    """
    Gestion du 2FA TOTP compatible Google Authenticator.
    Remplace l'ancien système de codes SMS via Telegram.
    """

    @staticmethod
    def generate_secret() -> str:
        """Génère un secret TOTP aléatoire (base32, 32 caractères)."""
        if _TOTP_AVAILABLE:
            return pyotp.random_base32()
        return base64.b32encode(secrets.token_bytes(20)).decode()

    @staticmethod
    def get_totp_uri(secret: str, username: str, issuer: str = "CryptoScanner Pro") -> str:
        """Retourne l'URI otpauth:// pour le QR code."""
        if _TOTP_AVAILABLE:
            totp = pyotp.TOTP(secret)
            return totp.provisioning_uri(name=username, issuer_name=issuer)
        return f"otpauth://totp/{issuer}:{username}?secret={secret}&issuer={issuer}"

    @staticmethod
    def get_qr_base64(secret: str, username: str) -> str:
        """Génère un QR code en base64 PNG pour affichage HTML."""
        if not _TOTP_AVAILABLE:
            return ""
        try:
            uri = TOTPManager.get_totp_uri(secret, username)
            img = qrcode.make(uri)
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()
        except Exception as e:
            print(f"[TOTP] QR generation failed: {e}")
            return ""

    @staticmethod
    def verify_code(secret: str, code: str, window: int = 1) -> bool:
        """
        Vérifie un code TOTP à 6 chiffres.
        window=1 tolère ±30 secondes de décalage horloge.
        """
        if not secret or not code:
            return False
        code = str(code).replace(" ", "").strip()
        if _TOTP_AVAILABLE:
            try:
                totp = pyotp.TOTP(secret)
                return totp.verify(code, valid_window=window)
            except Exception:
                return False
        else:
            # Fallback TOTP manuel (RFC 6238)
            return _verify_totp_manual(secret, code)

    @staticmethod
    def generate_backup_codes(count: int = 10) -> list:
        """Génère des codes de secours usage unique (format XXXX-XXXX)."""
        codes = []
        for _ in range(count):
            raw = secrets.token_hex(4).upper()
            codes.append(f"{raw[:4]}-{raw[4:]}")
        return codes


def _verify_totp_manual(secret: str, code: str) -> bool:
    """Implémentation TOTP manuelle sans pyotp (fallback)."""
    try:
        key = base64.b32decode(secret.upper())
        t = int(time.time()) // 30
        for delta in (-1, 0, 1):
            msg = (t + delta).to_bytes(8, "big")
            h = hmac.new(key, msg, hashlib.sha1).digest()
            offset = h[-1] & 0x0F
            code_int = ((h[offset] & 0x7F) << 24 | h[offset+1] << 16 |
                        h[offset+2] << 8 | h[offset+3]) % 1_000_000
            if hmac.compare_digest(str(code_int).zfill(6), str(code).zfill(6)):
                return True
        return False
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════
# 4. RATE LIMITING — Thread-safe, par IP et par endpoint
# ══════════════════════════════════════════════════════════════

class RateLimiter:
    """
    Rate limiter en mémoire par IP.
    Fenêtre glissante, thread-safe.
    """

    def __init__(self):
        self._buckets: dict = {}
        self._lock = threading.Lock()

    def check(self, key: str, max_requests: int, window_seconds: int = 60) -> Tuple[bool, int]:
        """
        Vérifie si la clé (IP + endpoint) peut faire une requête.
        Retourne (allowed: bool, remaining: int).
        """
        now = time.time()
        with self._lock:
            if key not in self._buckets:
                self._buckets[key] = []
            # Nettoyer les anciennes entrées
            self._buckets[key] = [t for t in self._buckets[key] if now - t < window_seconds]
            count = len(self._buckets[key])
            if count >= max_requests:
                return False, 0
            self._buckets[key].append(now)
            return True, max_requests - count - 1

    def cleanup(self):
        """Nettoie les buckets expirés (à appeler périodiquement)."""
        now = time.time()
        with self._lock:
            keys_to_delete = [k for k, ts in self._buckets.items()
                               if not ts or now - max(ts) > 3600]
            for k in keys_to_delete:
                del self._buckets[k]


# Limits par endpoint
RATE_LIMITS = {
    "login":    (5,   60),   # 5 tentatives par minute
    "register": (3,   300),  # 3 inscriptions par 5 minutes
    "api":      (120, 60),   # 120 requêtes API par minute
    "chat":     (20,  60),   # 20 messages chat IA par minute
    "2fa":      (10,  300),  # 10 codes 2FA par 5 minutes
}

# Instance globale
rate_limiter = RateLimiter()


def check_rate_limit(ip: str, endpoint: str = "api") -> Tuple[bool, int]:
    """Shortcut pour vérifier un rate limit."""
    max_req, window = RATE_LIMITS.get(endpoint, (60, 60))
    return rate_limiter.check(f"{ip}:{endpoint}", max_req, window)


def get_ip() -> str:
    """Retourne l'IP client si Flask request est disponible."""
    if request is None:
        return ""
    try:
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return (request.headers.get("X-Real-IP") or request.remote_addr or "").strip()
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════
# 5. HEADERS DE SÉCURITÉ HTTP
# ══════════════════════════════════════════════════════════════

SECURITY_HEADERS = {
    "X-Content-Type-Options":       "nosniff",
    "X-Frame-Options":              "DENY",
    "X-XSS-Protection":             "1; mode=block",
    "Referrer-Policy":              "strict-origin-when-cross-origin",
    "Permissions-Policy":           "geolocation=(), microphone=(), camera=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
        "https://cdn.jsdelivr.net https://cdnjs.cloudflare.com "
        "https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' "
        "https://cdn.jsdelivr.net https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self' wss: ws:; "
        "frame-ancestors 'none';"
    ),
}


def apply_security_headers(response):
    """
    Middleware Flask : ajoute les headers sécurité à chaque réponse.
    Usage : app.after_request(apply_security_headers)
    """
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    # Cache-Control strict pour les pages auth
    if "auth" in response.headers.get("Content-Type", ""):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return response


# ══════════════════════════════════════════════════════════════
# 6. VALIDATION ET SANITISATION DES INPUTS
# ══════════════════════════════════════════════════════════════

def validate_username(username: str) -> Tuple[bool, str]:
    """Valide un nom d'utilisateur."""
    if not username:
        return False, "Nom d'utilisateur requis"
    if len(username) < 3:
        return False, "Minimum 3 caractères"
    if len(username) > 32:
        return False, "Maximum 32 caractères"
    if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
        return False, "Caractères autorisés : lettres, chiffres, _ . -"
    return True, ""


def validate_password(password: str) -> Tuple[bool, str]:
    """Valide un mot de passe (force minimum)."""
    if not password:
        return False, "Mot de passe requis"
    if len(password) < 8:
        return False, "Minimum 8 caractères"
    if len(password) > 128:
        return False, "Trop long (max 128)"
    # Vérifier qu'il y a au moins un chiffre et une lettre
    if not re.search(r'[A-Za-z]', password):
        return False, "Doit contenir au moins une lettre"
    if not re.search(r'[0-9]', password):
        return False, "Doit contenir au moins un chiffre"
    return True, ""


def sanitize_symbol(symbol: str) -> str:
    """Nettoie un symbole de crypto/forex (garde seulement alphanum + /)."""
    return re.sub(r'[^A-Z0-9/]', '', str(symbol).upper()[:20])


def sanitize_text(text: str, max_len: int = 500) -> str:
    """Sanitise un texte utilisateur (notes, messages...)."""
    if not text:
        return ""
    # Supprimer les caractères de contrôle dangereux
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', str(text))
    return cleaned[:max_len]


def validate_price(value) -> Tuple[bool, float]:
    """Valide et retourne un prix numérique."""
    try:
        p = float(str(value).replace(',', '.'))
        if p < 0 or p > 1_000_000_000:
            return False, 0.0
        return True, p
    except (ValueError, TypeError):
        return False, 0.0


def validate_quantity(value) -> Tuple[bool, float]:
    """Valide et retourne une quantité."""
    try:
        q = float(str(value).replace(',', '.'))
        if q <= 0 or q > 1_000_000_000:
            return False, 0.0
        return True, q
    except (ValueError, TypeError):
        return False, 0.0


# ══════════════════════════════════════════════════════════════
# 7. MIGRATION DB — Tables sécurité V11
# ══════════════════════════════════════════════════════════════

def run_security_migrations():
    """
    Applique les migrations de sécurité en douceur.
    Compatible avec l'existant (ne casse rien).
    """
    conn = get_connection()
    try:
        from db import get_columns
        # Ajouter colonne totp_secret si elle n'existe pas
        cols = get_columns("users", conn)
        if "totp_secret" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN totp_secret TEXT DEFAULT ''")
            print("[Security] Migration: colonne totp_secret ajoutee")
        if "totp_enabled" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN totp_enabled INTEGER DEFAULT 0")
            print("[Security] Migration: colonne totp_enabled ajoutee")
        if "backup_codes" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN backup_codes TEXT DEFAULT ''")
            print("[Security] Migration: colonne backup_codes ajoutee")
        if "pw_algorithm" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN pw_algorithm TEXT DEFAULT 'sha256'")
            print("[Security] Migration: colonne pw_algorithm ajoutee")
        if "failed_logins" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN failed_logins INTEGER DEFAULT 0")
        if "locked_until" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN locked_until TEXT DEFAULT ''")

        # Table backup codes dédiée
        conn.execute("""
            CREATE TABLE IF NOT EXISTS backup_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code_hash TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                created TEXT,
                used_at TEXT DEFAULT ''
            )
        """)

        # Table audit_security (logs sécurité séparés)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_security (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                event TEXT NOT NULL,
                detail TEXT DEFAULT '',
                ip TEXT DEFAULT '',
                success INTEGER DEFAULT 1,
                ts TEXT NOT NULL
            )
        """)

        # Migrer user_exchange_keys : ajouter colonnes chiffrées
        key_cols = get_columns("user_exchange_keys", conn)
        if "api_key_enc" not in key_cols:
            conn.execute("ALTER TABLE user_exchange_keys ADD COLUMN api_key_enc TEXT DEFAULT ''")
            conn.execute("ALTER TABLE user_exchange_keys ADD COLUMN api_secret_enc TEXT DEFAULT ''")
            conn.execute("ALTER TABLE user_exchange_keys ADD COLUMN migrated INTEGER DEFAULT 0")
            print("[Security] Migration: colonnes chiffrees cles exchange ajoutees")

        conn.commit()
        print("[Security] Migrations securite appliquees")
    except Exception as e:
        print(f"[Security] Migration error: {e}")
    finally:
        conn.close()


def migrate_exchange_keys_to_vault():
    """
    Chiffre toutes les clés API existantes stockées en clair.
    À appeler une seule fois au démarrage.
    """
    try:
        conn = get_connection(); conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT user_id, exchange, api_key, api_secret FROM user_exchange_keys WHERE migrated=0"
        ).fetchall()
        migrated = 0
        for row in rows:
            if row["api_key"] and row["api_key"] != "":
                enc_key    = vault.encrypt_if_needed(row["api_key"])
                enc_secret = vault.encrypt_if_needed(row["api_secret"] or "")
                conn.execute(
                    "UPDATE user_exchange_keys SET api_key_enc=?, api_secret_enc=?, migrated=1 "
                    "WHERE user_id=? AND exchange=?",
                    (enc_key, enc_secret, row["user_id"], row["exchange"])
                )
                migrated += 1
        conn.commit(); conn.close()
        if migrated:
            print(f"[KeyVault] {migrated} cle(s) exchange chiffree(s)")
    except Exception as e:
        print(f"[KeyVault] Migration error: {e}")


# ══════════════════════════════════════════════════════════════
# 8. GESTION 2FA COMPLÈTE (DB)
# ══════════════════════════════════════════════════════════════

def setup_totp(user_id: int, username: str) -> dict:
    """
    Initialise le TOTP pour un utilisateur.
    Retourne le secret, l'URI et le QR code base64.
    """
    secret = TOTPManager.generate_secret()
    uri    = TOTPManager.get_totp_uri(secret, username)
    qr_b64 = TOTPManager.get_qr_base64(secret, username)
    backup  = TOTPManager.generate_backup_codes(10)

    # Sauvegarder le secret (pas encore activé)
    conn = get_connection()
    conn.execute(
        "UPDATE users SET totp_secret=? WHERE id=?",
        (vault.encrypt(secret), user_id)
    )
    # Sauvegarder les codes de backup hashés
    conn.execute("DELETE FROM backup_codes WHERE user_id=?", (user_id,))
    for code in backup:
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        conn.execute(
            "INSERT INTO backup_codes (user_id, code_hash, created) VALUES (?,?,?)",
            (user_id, code_hash, datetime.now().isoformat())
        )
    conn.commit(); conn.close()

    return {
        "secret":       secret,
        "uri":          uri,
        "qr_base64":    qr_b64,
        "backup_codes": backup,
    }


def confirm_totp(user_id: int, code: str) -> bool:
    """
    Confirme l'activation du TOTP après scan du QR.
    Active seulement si le code est valide.
    """
    secret = _get_user_totp_secret(user_id)
    if not secret:
        return False
    if TOTPManager.verify_code(secret, code):
        conn = get_connection()
        conn.execute("UPDATE users SET totp_enabled=1 WHERE id=?", (user_id,))
        conn.commit(); conn.close()
        return True
    return False


def verify_totp_login(user_id: int, code: str, ip: str = "") -> bool:
    """
    Vérifie le code TOTP ou un code de backup lors du login.
    Retourne True si valide.
    """
    # Vérifier code TOTP
    secret = _get_user_totp_secret(user_id)
    if secret and TOTPManager.verify_code(secret, code):
        _audit_security(user_id, "TOTP_SUCCESS", f"IP:{ip}", True)
        return True
    # Vérifier code de backup
    if _verify_backup_code(user_id, code):
        _audit_security(user_id, "BACKUP_CODE_USED", f"IP:{ip}", True)
        return True
    _audit_security(user_id, "TOTP_FAILED", f"Code:{code[:3]}... IP:{ip}", False)
    return False


def disable_totp(user_id: int) -> bool:
    """Désactive le TOTP pour un utilisateur."""
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE users SET totp_enabled=0, totp_secret='' WHERE id=?",
            (user_id,)
        )
        conn.execute("DELETE FROM backup_codes WHERE user_id=?", (user_id,))
        conn.commit(); conn.close()
        return True
    except Exception:
        return False


def _get_user_totp_secret(user_id: int) -> Optional[str]:
    """Récupère et déchiffre le secret TOTP d'un utilisateur."""
    try:
        conn = get_connection(); conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT totp_secret FROM users WHERE id=?", (user_id,)
        ).fetchone()
        conn.close()
        if row and row["totp_secret"]:
            return vault.decrypt(row["totp_secret"])
    except Exception:
        pass
    return None


def _verify_backup_code(user_id: int, code: str) -> bool:
    """Vérifie et invalide un code de backup."""
    code_hash = hashlib.sha256(code.upper().replace("-","").encode()).hexdigest()
    # Essayer aussi avec tirets
    code_hash2 = hashlib.sha256(code.upper().encode()).hexdigest()
    try:
        conn = get_connection(); conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id FROM backup_codes WHERE user_id=? AND (code_hash=? OR code_hash=?) AND used=0",
            (user_id, code_hash, code_hash2)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE backup_codes SET used=1, used_at=? WHERE id=?",
                (datetime.now().isoformat(), row["id"])
            )
            conn.commit(); conn.close()
            return True
        conn.close()
    except Exception:
        pass
    return False


# ══════════════════════════════════════════════════════════════
# 9. AUDIT SÉCURITÉ
# ══════════════════════════════════════════════════════════════

def _audit_security(user_id: int, event: str, detail: str = "", success: bool = True):
    """Enregistre un événement de sécurité."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_security (user_id, event, detail, success, ts) VALUES (?,?,?,?,?)",
            (user_id, event, detail, 1 if success else 0, datetime.now().isoformat())
        )
        conn.commit(); conn.close()
    except Exception:
        pass


def get_security_events(user_id: int = None, limit: int = 100) -> list:
    """Récupère les derniers événements de sécurité."""
    try:
        conn = get_connection(); conn.row_factory = sqlite3.Row
        if user_id:
            rows = conn.execute(
                "SELECT * FROM audit_security WHERE user_id=? ORDER BY id DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_security ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════
# 10. FONCTIONS D'INTÉGRATION (remplacent les anciennes)
# ══════════════════════════════════════════════════════════════

def save_exchange_keys_secure(user_id: int, exchange: str, api_key: str, api_secret: str) -> bool:
    """
    Sauvegarde les clés exchange chiffrées.
    Remplace engine.save_exchange_keys() dans scanner_engine.py
    """
    enc_key    = vault.encrypt(api_key)
    enc_secret = vault.encrypt(api_secret)
    try:
        conn = get_connection()
        conn.execute("""
            INSERT OR REPLACE INTO user_exchange_keys
            (user_id, exchange, api_key, api_secret, api_key_enc, api_secret_enc, migrated, updated)
            VALUES (?,?,?,?,?,?,1,?)
        """, (user_id, exchange, "", "", enc_key, enc_secret, datetime.now().isoformat()))
        conn.commit(); conn.close()
        _audit_security(user_id, "KEYS_SAVED", f"exchange:{exchange}")
        return True
    except Exception as e:
        print(f"[KeyVault] save_exchange_keys error: {e}")
        return False


def get_exchange_keys_secure(user_id: int, exchange: str) -> Optional[dict]:
    """
    Récupère et déchiffre les clés exchange.
    Remplace engine.get_exchange_keys() dans scanner_engine.py
    """
    try:
        conn = get_connection(); conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT api_key, api_secret, api_key_enc, api_secret_enc, migrated, updated "
            "FROM user_exchange_keys WHERE user_id=? AND exchange=?",
            (user_id, exchange)
        ).fetchone()
        conn.close()
        if not row:
            return None

        # Préférer les colonnes chiffrées
        if row["migrated"] and row["api_key_enc"]:
            return {
                "api_key":    vault.decrypt(row["api_key_enc"]),
                "api_secret": vault.decrypt(row["api_secret_enc"]),
                "updated":    row["updated"],
            }
        # Fallback sur colonnes non chiffrées (migration en cours)
        if row["api_key"]:
            # Migrer à la volée
            enc_key    = vault.encrypt(row["api_key"])
            enc_secret = vault.encrypt(row["api_secret"] or "")
            db = get_connection()
            db.execute(
                "UPDATE user_exchange_keys SET api_key_enc=?, api_secret_enc=?, migrated=1, api_key='', api_secret='' "
                "WHERE user_id=? AND exchange=?",
                (enc_key, enc_secret, user_id, exchange)
            )
            db.commit(); db.close()
            return {
                "api_key":    row["api_key"],
                "api_secret": row["api_secret"],
                "updated":    row["updated"],
            }
    except Exception as e:
        print(f"[KeyVault] get_exchange_keys error: {e}")
    return None


# ══════════════════════════════════════════════════════════════
# 11. INITIALISATION COMPLÈTE
# ══════════════════════════════════════════════════════════════

def init_security():
    """
    Point d'entrée unique — à appeler dans app.py au démarrage.
    
    Usage dans app.py :
        from security import init_security, apply_security_headers
        init_security()
        app.after_request(apply_security_headers)
    """
    print("[Security] Initialisation securite V11...")

    if not _FERNET_AVAILABLE:
        raise RuntimeError(
            "[Security] CRITIQUE : bibliothèque 'cryptography' manquante. "
            "Le chiffrement des clés API est impossible. "
            "Installez-la avec : pip install cryptography"
        )
    if not _BCRYPT_AVAILABLE:
        raise RuntimeError(
            "[Security] CRITIQUE : bibliothèque 'bcrypt' manquante. "
            "Le hachage des mots de passe est impossible. "
            "Installez-la avec : pip install bcrypt"
        )

    run_security_migrations()
    migrate_exchange_keys_to_vault()

    deps = []
    deps.append("bcrypt")
    deps.append("Fernet AES-256")
    if _TOTP_AVAILABLE:      deps.append("TOTP (pyotp)")
    else:                    deps.append("pyotp manquant")

    print(f"[Security] {' · '.join(deps)}")
    print("[Security] Securite V11 active")

    return {
        "bcrypt":  _BCRYPT_AVAILABLE,
        "fernet":  _FERNET_AVAILABLE,
        "totp":    _TOTP_AVAILABLE,
    }
