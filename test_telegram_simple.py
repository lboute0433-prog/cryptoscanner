#!/usr/bin/env python3
"""Test simple: Envoyer alertes sur 2 canaux Telegram"""

import os, requests, time
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT, TELEGRAM_CHAT_FREE
from db import set_setting
from scanner_engine import load_admin_alert_settings
from smart_signals import build_telegram_alert, build_retrace_alert

print("\n" + "="*80)
print("TEST E2E - ALERTES TELEGRAM (2 CANAUX)")
print("="*80)

# Test 1: Verifier config
print("\n[TEST 1] Configuration")
print(f"  Token OK: {bool(TELEGRAM_TOKEN)}")
print(f"  Canal PAID: {TELEGRAM_CHAT[:20]}..." if TELEGRAM_CHAT else "  Canal PAID: NOT SET")
print(f"  Canal FREE: {TELEGRAM_CHAT_FREE[:20]}..." if TELEGRAM_CHAT_FREE else "  Canal FREE: NOT SET")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT or not TELEGRAM_CHAT_FREE:
    print("\nERREUR: Tokens Telegram pas configures!")
    print("  Set: TG_TOKEN, TG_CHAT, TG_CHAT_FREE")
    exit(1)

# Test 2: Admin settings
print("\n[TEST 2] Admin Alert Settings")
settings = load_admin_alert_settings()
print(f"  score_min: {settings.get('score_min')}")
print(f"  rsi_oversold: {settings.get('rsi_oversold')}")
print(f"  rsi_overbought: {settings.get('rsi_overbought')}")
print(f"  max_per_cycle: {settings.get('max_per_cycle')}")
print(f"  cooldown_hours: {settings.get('cooldown_hours')}")

# Test 3: Smart Signal
print("\n[TEST 3] Envoyer Smart Signal aux 2 canaux")

signal = {
    "symbol": "BTC",
    "score": 75,
    "direction": "buy",
    "rsi": 45.5,
    "macd_line": 0.5,
    "change_pct": 2.3,
    "volume_mult": 3.2,
    "vol_ratio": 3.2,
    "volume_usdt": 2500000,
    "price": 67500,
    "bb_pos": 0.65,
    "timestamp": datetime.now().isoformat(),
    "tags": [
        {"label": "RSI BULLISH", "emoji": "+"},
        {"label": "VOLUME SPIKE", "emoji": "^"}
    ]
}

msg_free = build_telegram_alert(signal, for_role="free")
msg_paid = build_telegram_alert(signal, for_role="paid")

# Canal PUBLIC (FREE)
print("\n  Envoi sur CANAL PUBLIC (FREE)...")
try:
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_FREE,
            "text": "[TEST SMART SIGNAL - FREE]\n\n" + msg_free,
            "parse_mode": "HTML"
        },
        timeout=5
    )
    if resp.status_code == 200:
        print("    SUCCES - Message recu sur canal PUBLIC")
    else:
        print(f"    ERREUR: {resp.status_code}")
except Exception as e:
    print(f"    ERREUR: {e}")

time.sleep(1)

# Canal VIP (PAID)
print("\n  Envoi sur CANAL VIP (PAID)...")
try:
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT,
            "text": "[TEST SMART SIGNAL - PAID]\n\n" + msg_paid,
            "parse_mode": "HTML"
        },
        timeout=5
    )
    if resp.status_code == 200:
        print("    SUCCES - Message recu sur canal VIP")
    else:
        print(f"    ERREUR: {resp.status_code}")
except Exception as e:
    print(f"    ERREUR: {e}")

# Test 4: Retrace RSI
print("\n[TEST 4] Envoyer Retrace RSI aux 2 canaux")

rsi_exit = {
    "direction": "bullish",
    "name": "RSI OVERSOLD BOUNCE",
    "rsi_prev": 28,
    "rsi_now": 32,
    "desc": "RSI a depasse le seuil de survente (30)",
    "action": "LONG OPPORTUNITY"
}

coin = {
    "symbol": "ETH",
    "price": 3500,
    "change_pct": 1.5,
    "volume_usdt": 1500000
}

msg_free = build_retrace_alert(
    coin["symbol"], rsi_exit, coin["price"],
    coin["change_pct"], coin["volume_usdt"],
    for_role="free"
)

msg_paid = build_retrace_alert(
    coin["symbol"], rsi_exit, coin["price"],
    coin["change_pct"], coin["volume_usdt"],
    for_role="paid"
)

# Canal PUBLIC
print("\n  Envoi Retrace RSI sur CANAL PUBLIC (FREE)...")
try:
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_FREE,
            "text": "[TEST RETRACE RSI - FREE]\n\n" + msg_free,
            "parse_mode": "HTML"
        },
        timeout=5
    )
    if resp.status_code == 200:
        print("    SUCCES")
    else:
        print(f"    ERREUR: {resp.status_code}")
except Exception as e:
    print(f"    ERREUR: {e}")

time.sleep(1)

# Canal VIP
print("\n  Envoi Retrace RSI sur CANAL VIP (PAID)...")
try:
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT,
            "text": "[TEST RETRACE RSI - PAID]\n\n" + msg_paid,
            "parse_mode": "HTML"
        },
        timeout=5
    )
    if resp.status_code == 200:
        print("    SUCCES")
    else:
        print(f"    ERREUR: {resp.status_code}")
except Exception as e:
    print(f"    ERREUR: {e}")

# Test 5: Coherence
print("\n[TEST 5] Coherence ADMIN -> Alertes")
print(f"  Score avant: {settings.get('score_min')}")

new_score = 80
print(f"  Changer score_min -> {new_score}...")
set_setting('score_min', str(new_score))
time.sleep(1)

settings2 = load_admin_alert_settings()
score_after = settings2.get('score_min')
print(f"  Score apres: {score_after}")

if score_after == new_score:
    print("  SUCCES - Changement immédiat et persisté!")
    # Revert
    set_setting('score_min', str(settings.get('score_min')))
    print(f"  Reverted a {settings.get('score_min')}")
else:
    print(f"  ERREUR - Score ne change pas!")

# Resume
print("\n" + "="*80)
print("RESUME TESTS")
print("="*80)
print("\nMessages envoyes sur:")
print(f"  1. CANAL PUBLIC (FREE): {TELEGRAM_CHAT_FREE}")
print(f"  2. CANAL VIP (PAID): {TELEGRAM_CHAT}")
print("\nDifferences FREE vs PAID:")
print("  - FREE: Infos basiques (symbol, score, RSI, volume)")
print("  - PAID: Infos enrichis (patterns, divergences, support/resist)")
print("\nOuvre Telegram et verifie que tu as recu les messages!")
print("\n")
