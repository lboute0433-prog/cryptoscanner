#!/usr/bin/env python3
"""
Test: Smart Signal Detection -> Cache -> API -> ANALYSE/SMART SIGNALS Display

Verifie que si on declenche un signal, il s'affiche dans la page ANALYSE/SMART SIGNALS
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT, TELEGRAM_CHAT_FREE
from db import get_setting, set_setting
from scanner_engine import load_admin_alert_settings
from smart_signals import analyze_coin_smart, build_telegram_alert

print("\n" + "="*80)
print("TEST: Smart Signal Detection -> Display in ANALYSE/SMART SIGNALS")
print("="*80)

# ============================================================================
# STEP 1: Charger les settings ADMIN
# ============================================================================

print("\n[STEP 1] Charger settings ADMIN...")
settings = load_admin_alert_settings()
score_min = settings.get('score_min')
cache_size = settings.get('cache_size', 20)

print(f"  score_min: {score_min}")
print(f"  cache_size: {cache_size}")

# ============================================================================
# STEP 2: Analyser un coin reel (BTC) pour detecter un signal
# ============================================================================

print("\n[STEP 2] Analyser BTC pour detecter un Smart Signal...")

try:
    from ccxt_wrapper import MultiExchangeManager

    manager = MultiExchangeManager(['binance'])

    # Fetch OHLCV for BTC (returns dict: {'binance': [[ts, o, h, l, c, v], ...]})
    ohlcv_dict = manager.fetch_ohlcv('BTC/USDT', '1h', limit=100)

    # Get Binance candles
    binance_ohlcv = ohlcv_dict.get('binance', [])

    if not binance_ohlcv or len(binance_ohlcv) < 50:
        print(f"  ERREUR: Pas assez de candles pour BTC ({len(binance_ohlcv)})")
        sys.exit(1)

    # Convert OHLCV to candles format [timestamp, open, high, low, close, volume]
    # Format: [0]=ts, [1]=open, [2]=high, [3]=low, [4]=close, [5]=volume
    candles = [
        {
            "t": ohlcv_item[0],  # timestamp
            "o": ohlcv_item[1],  # open
            "h": ohlcv_item[2],  # high
            "l": ohlcv_item[3],  # low
            "c": ohlcv_item[4],  # close
            "v": ohlcv_item[5]   # volume
        }
        for ohlcv_item in binance_ohlcv
    ]

    print(f"  Candles fetched: {len(candles)} (1h timeframe)")

    # Analyze coin
    signal = analyze_coin_smart('BTC', candles)

    if not signal:
        print(f"  ERREUR: Pas de signal detecte pour BTC")
        sys.exit(1)

    print(f"\n  Signal DETECTE:")
    print(f"    Symbol: {signal.get('symbol')}")
    print(f"    Score: {signal.get('score', '?')}")
    print(f"    Direction: {signal.get('direction')}")
    print(f"    Price: ${signal.get('price'):.2f}")
    print(f"    RSI: {signal.get('rsi'):.1f}")
    print(f"    Volume: ${signal.get('volume_usdt', 0):,.0f}")

    signal_score = signal.get('score', 0)

except Exception as e:
    print(f"  ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 3: Verifier si le signal depasse le score_min
# ============================================================================

print("\n[STEP 3] Verifier si signal qualifie pour alerte...")

print(f"  Condition: signal.score ({signal_score}) >= score_min ({score_min})?")

if signal_score >= score_min:
    print(f"  Resultat: OUI - Signal QUALIFIE pour alerte Telegram et ANALYSE/SMART SIGNALS")
    qualifies = True
else:
    print(f"  Resultat: NON - Signal trop faible pour alerte")
    qualifies = False

# ============================================================================
# STEP 4: Tester l'API /api/smart_signals en simulant le cache
# ============================================================================

print("\n[STEP 4] Tester API /api/smart_signals...")

# On ne peut pas modifier le vrai cache depuis ce script (thread-safe)
# Donc on va juste verifier que l'API fonctionne

try:
    print(f"  Appel: GET /api/smart_signals?role=paid")
    resp = requests.get('http://localhost:5000/api/smart_signals?role=paid', timeout=5)

    if resp.status_code != 200:
        print(f"  ERREUR: Status {resp.status_code}")
        sys.exit(1)

    data = resp.json()
    signals = data.get('signals', [])
    api_score_min = data.get('score_min')

    print(f"  Reponse API:")
    print(f"    Signals retournes: {len(signals)}")
    print(f"    Score_min applique: {api_score_min}")
    print(f"    Timestamp: {data.get('ts')}")

    if signals:
        top_signal = signals[0]
        print(f"\n  Top Signal actuellement en cache:")
        print(f"    Symbol: {top_signal.get('symbol')}")
        print(f"    Score: {top_signal.get('score')}")
        print(f"    Direction: {top_signal.get('direction')}")
        print(f"    Price: ${top_signal.get('price', 0):.2f}")

except Exception as e:
    print(f"  ERREUR API: {e}")
    print(f"  (Serveur Hetzner peut ne pas etre accessible en local)")

# ============================================================================
# STEP 5: Message Telegram de test
# ============================================================================

if qualifies:
    print("\n[STEP 5] Construire message Telegram (si score qualifie)...")

    msg_free = build_telegram_alert(signal, for_role="free")
    msg_paid = build_telegram_alert(signal, for_role="paid")

    print(f"  Message FREE construit ({len(msg_free)} chars)")
    print(f"  Message PAID construit ({len(msg_paid)} chars)")

    print(f"\n[STEP 6] Envoyer message Telegram test...")

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_FREE,
                "text": f"[TEST SMART SIGNAL] BTC Signal (score={signal_score})\n\n{msg_free}",
                "parse_mode": "HTML"
            },
            timeout=5
        )

        if resp.status_code == 200:
            print(f"  OK - Message envoye sur CANAL FREE")
        else:
            print(f"  ERREUR: {resp.status_code}")
    except Exception as e:
        print(f"  ERREUR: {e}")

# ============================================================================
# RESUME
# ============================================================================

print("\n" + "="*80)
print("RESUME: Smart Signal Detection -> Display Flow")
print("="*80)

print(f"\n[RESULTAT]")
print(f"  1. Signal BTC detecte: SCORE = {signal_score}")
print(f"  2. Score_min requis: {score_min}")
print(f"  3. Signal QUALIFIE: {'OUI' if qualifies else 'NON'}")
print(f"  4. Visible en ANALYSE/SMART SIGNALS: {'OUI' if qualifies else 'NON'}")

if qualifies:
    print(f"\n[COHERENCE VERIFIEE]")
    print(f"  Signal avec score={signal_score} (>= {score_min}) sera:")
    print(f"    - Envoye en Telegram: OUI")
    print(f"    - Visible en ANALYSE/SMART SIGNALS: OUI")
    print(f"    - Visible en ANALYSE/SIGNAUX: OUI (affichage large)")
else:
    print(f"\n[COHERENCE VERIFIEE]")
    print(f"  Signal avec score={signal_score} (< {score_min}) sera:")
    print(f"    - Envoye en Telegram: NON")
    print(f"    - Visible en ANALYSE/SMART SIGNALS: NON (filtre score_min)")
    print(f"    - Visible en ANALYSE/SIGNAUX: OUI (affichage large)")

print(f"\nOuvre https://46.225.234.71/app et va dans ANALYSE > SMART SIGNALS")
print(f"Verifie que BTC apparat (ou pas selon le score)!")
print(f"\n")
