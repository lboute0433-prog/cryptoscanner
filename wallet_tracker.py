"""
Wallet Tracker On-Chain — CryptoScanner Pro
Supporte : ETH, BTC, SOL
APIs gratuites sans clé requise :
  - ETH  : Ethplorer (freekey)
  - BTC  : Blockchain.info
  - SOL  : Solana public RPC + Solscan public API
"""

from __future__ import annotations

import re
import time
import threading
import requests
from datetime import datetime
from typing import Optional

# ── Cache ─────────────────────────────────────────────────────
_cache: dict = {}
_cache_lock = threading.Lock()
CACHE_TTL = 120  # 2 minutes


def _cache_get(key: str):
    with _cache_lock:
        e = _cache.get(key)
        if e and time.time() < e["exp"]:
            return e["v"]
    return None


def _cache_set(key: str, value, ttl: int = CACHE_TTL):
    with _cache_lock:
        _cache[key] = {"v": value, "exp": time.time() + ttl}


# ── Détection de chaîne ───────────────────────────────────────

def detect_chain(address: str) -> Optional[str]:
    """Détecte automatiquement la blockchain depuis le format d'adresse."""
    address = address.strip()
    # Ethereum / EVM (0x + 40 hex)
    if re.match(r"^0x[0-9a-fA-F]{40}$", address):
        return "eth"
    # Bitcoin Legacy (1...), P2SH (3...) ou Bech32 (bc1...)
    if re.match(r"^(1|3)[1-9A-HJ-NP-Za-km-z]{25,34}$", address):
        return "btc"
    if re.match(r"^bc1[0-9a-zA-Z]{6,87}$", address):
        return "btc"
    # Solana (base58, 32-44 chars)
    if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address):
        return "sol"
    return None


# ── ETH via Ethplorer ─────────────────────────────────────────

def fetch_eth_wallet(address: str) -> dict:
    cached = _cache_get(f"eth:{address}")
    if cached:
        return cached

    try:
        url = f"https://api.ethplorer.io/getAddressInfo/{address}?apiKey=freekey"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()

        eth_balance = float(data.get("ETH", {}).get("balance", 0))
        eth_price   = float((data.get("ETH", {}).get("price") or {}).get("rate", 0))
        eth_usd     = eth_balance * eth_price

        # Top tokens (valeur USD décroissante)
        tokens = []
        for t in (data.get("tokens") or []):
            info  = t.get("tokenInfo", {})
            price = info.get("price") or {}
            bal   = float(t.get("balance", 0))
            dec   = int(info.get("decimals") or 18)
            qty   = bal / (10 ** dec)
            usd   = qty * float(price.get("rate", 0)) if price else 0
            if usd > 1:
                tokens.append({
                    "symbol": info.get("symbol", "?"),
                    "name":   info.get("name", ""),
                    "qty":    round(qty, 4),
                    "usd":    round(usd, 2),
                })
        tokens.sort(key=lambda x: x["usd"], reverse=True)

        # Dernières transactions
        txs = []
        for tx in (data.get("transfers") or [])[:8]:
            ts = datetime.fromtimestamp(int(tx.get("timestamp", 0))).strftime("%d/%m %H:%M") if tx.get("timestamp") else "—"
            val = float(tx.get("value", 0))
            sym = tx.get("tokenInfo", {}).get("symbol", "ETH") if tx.get("tokenInfo") else "ETH"
            txs.append({
                "hash":  (tx.get("transactionHash") or "")[:16] + "…",
                "type":  "REÇU" if (tx.get("to") or "").lower() == address.lower() else "ENVOYÉ",
                "value": round(val, 4),
                "symbol": sym,
                "ts":    ts,
            })

        result = {
            "chain":    "ETH",
            "address":  address,
            "balance":  round(eth_balance, 6),
            "balance_usd": round(eth_usd, 2),
            "tokens":   tokens[:8],
            "txs":      txs,
            "ts":       datetime.now().strftime("%H:%M:%S"),
            "ok":       True,
        }
        _cache_set(f"eth:{address}", result)
        return result

    except Exception as e:
        return {"ok": False, "error": str(e), "chain": "ETH", "address": address}


# ── BTC via Blockchain.info ───────────────────────────────────

def fetch_btc_wallet(address: str) -> dict:
    cached = _cache_get(f"btc:{address}")
    if cached:
        return cached

    try:
        url = f"https://blockchain.info/rawaddr/{address}?limit=8&cors=true"
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()

        balance_sat = int(data.get("final_balance", 0))
        balance_btc = balance_sat / 1e8

        # Prix BTC approximatif via ticker
        btc_price = 0
        try:
            tp = requests.get("https://blockchain.info/ticker", timeout=4).json()
            btc_price = float(tp.get("USD", {}).get("last", 0))
        except Exception:
            pass

        balance_usd = balance_btc * btc_price

        # Dernières transactions
        txs = []
        for tx in (data.get("txs") or [])[:8]:
            ts_epoch = tx.get("time", 0)
            ts = datetime.fromtimestamp(ts_epoch).strftime("%d/%m %H:%M") if ts_epoch else "—"
            # Détecter si reçu ou envoyé
            sent = any(inp.get("prev_out", {}).get("addr") == address for inp in (tx.get("inputs") or []))
            total_out = sum(o.get("value", 0) for o in (tx.get("out") or []) if o.get("addr") != address) / 1e8
            total_in  = sum(o.get("value", 0) for o in (tx.get("out") or []) if o.get("addr") == address)  / 1e8
            txs.append({
                "hash":   (tx.get("hash") or "")[:16] + "…",
                "type":   "ENVOYÉ" if sent else "REÇU",
                "value":  round(total_out if sent else total_in, 6),
                "symbol": "BTC",
                "ts":     ts,
            })

        result = {
            "chain":       "BTC",
            "address":     address,
            "balance":     round(balance_btc, 8),
            "balance_usd": round(balance_usd, 2),
            "tokens":      [],
            "txs":         txs,
            "ts":          datetime.now().strftime("%H:%M:%S"),
            "ok":          True,
        }
        _cache_set(f"btc:{address}", result)
        return result

    except Exception as e:
        return {"ok": False, "error": str(e), "chain": "BTC", "address": address}


# ── SOL via Solana RPC public ─────────────────────────────────

def fetch_sol_wallet(address: str) -> dict:
    cached = _cache_get(f"sol:{address}")
    if cached:
        return cached

    try:
        rpc = "https://api.mainnet-beta.solana.com"
        headers = {"Content-Type": "application/json"}

        # Balance SOL
        r = requests.post(rpc, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getBalance",
            "params": [address]
        }, headers=headers, timeout=8)
        lamports = r.json().get("result", {}).get("value", 0)
        sol_balance = lamports / 1e9

        # Prix SOL via CoinGecko (no key)
        sol_price = 0
        try:
            pg = requests.get(
                "https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd",
                timeout=4
            ).json()
            sol_price = float(pg.get("solana", {}).get("usd", 0))
        except Exception:
            pass

        balance_usd = sol_balance * sol_price

        # Token accounts (SPL tokens)
        tokens = []
        try:
            rt = requests.post(rpc, json={
                "jsonrpc": "2.0", "id": 2,
                "method": "getTokenAccountsByOwner",
                "params": [
                    address,
                    {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                    {"encoding": "jsonParsed"}
                ]
            }, headers=headers, timeout=8)
            for acc in (rt.json().get("result", {}).get("value") or [])[:12]:
                info = acc.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                mint = info.get("mint", "")
                amt  = info.get("tokenAmount", {})
                qty  = float(amt.get("uiAmount") or 0)
                if qty > 0:
                    tokens.append({
                        "symbol": mint[:8] + "…",
                        "name":   "",
                        "qty":    round(qty, 4),
                        "usd":    0,
                    })
        except Exception:
            pass

        result = {
            "chain":       "SOL",
            "address":     address,
            "balance":     round(sol_balance, 6),
            "balance_usd": round(balance_usd, 2),
            "tokens":      tokens[:6],
            "txs":         [],
            "ts":          datetime.now().strftime("%H:%M:%S"),
            "ok":          True,
        }
        _cache_set(f"sol:{address}", result)
        return result

    except Exception as e:
        return {"ok": False, "error": str(e), "chain": "SOL", "address": address}


# ── Dispatcher principal ──────────────────────────────────────

def track_wallet(address: str, chain: str = None) -> dict:
    """Point d'entrée principal. Détecte la chaîne si non fournie."""
    address = (address or "").strip()
    if not address:
        return {"ok": False, "error": "Adresse vide"}

    if not chain:
        chain = detect_chain(address)
    if not chain:
        return {"ok": False, "error": "Format d'adresse non reconnu (ETH/BTC/SOL supportés)"}

    chain = chain.lower()
    if chain == "eth":
        return fetch_eth_wallet(address)
    elif chain == "btc":
        return fetch_btc_wallet(address)
    elif chain == "sol":
        return fetch_sol_wallet(address)
    else:
        return {"ok": False, "error": f"Chaîne '{chain}' non supportée"}
