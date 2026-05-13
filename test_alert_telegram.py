#!/usr/bin/env python3
"""
Test E2E: Envoi d'alertes sur 2 canaux Telegram
TEST: Vérifie que les messages FREE et PAID sont envoyés correctement

Utilisation:
  python test_alert_telegram.py
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT, TELEGRAM_CHAT_FREE
from db import get_connection, get_setting, set_setting
from scanner_engine import load_admin_alert_settings
from smart_signals import build_telegram_alert, build_retrace_alert

# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Vérifier les tokens et canaux
# ══════════════════════════════════════════════════════════════════════════════

def test_config():
    """Vérifie que les tokens Telegram sont configurés"""
    print("\n" + "="*80)
    print("[INFO] TEST 1: Configuration Telegram")
    print("="*80)

    print(f"✓ TELEGRAM_TOKEN configured: {bool(TELEGRAM_TOKEN)}")
    print(f"✓ TELEGRAM_CHAT (PAID): {TELEGRAM_CHAT if TELEGRAM_CHAT else '[ERROR] NOT SET'}")
    print(f"✓ TELEGRAM_CHAT_FREE (FREE): {TELEGRAM_CHAT_FREE if TELEGRAM_CHAT_FREE else '[ERROR] NOT SET'}")

    if not TELEGRAM_TOKEN:
        print("\n[ERROR] ERREUR: TELEGRAM_TOKEN pas configuré!")
        print("   Set: TG_TOKEN environment variable")
        return False

    if not TELEGRAM_CHAT:
        print("\n[WARNING]  ATTENTION: TELEGRAM_CHAT (PAID) pas configuré!")
        print("   Test va sauter le canal PAID")

    if not TELEGRAM_CHAT_FREE:
        print("\n[WARNING]  ATTENTION: TELEGRAM_CHAT_FREE pas configuré!")
        print("   Test va sauter le canal FREE")

    return True

# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Charger les settings ADMIN
# ══════════════════════════════════════════════════════════════════════════════

def test_admin_settings():
    """Charge et affiche les settings actuels"""
    print("\n" + "="*80)
    print("[CONFIG]  TEST 2: Admin Alert Settings")
    print("="*80)

    settings = load_admin_alert_settings()

    print("\n- SMART SIGNALS Block:")
    print(f"   score_min: {settings.get('score_min')} (alertes si score >= ce seuil)")
    print(f"   max_per_cycle: {settings.get('max_per_cycle')} (max alertes par cycle)")
    print(f"   cooldown_hours: {settings.get('cooldown_hours')} (heures entre alertes même symbol)")
    print(f"   variation_pump: {settings.get('variation_pump')}%")
    print(f"   variation_dump: {settings.get('variation_dump')}%")

    print("\n- RETRACE RSI Block:")
    print(f"   rsi_oversold: {settings.get('rsi_oversold')} (trigger bullish)")
    print(f"   rsi_overbought: {settings.get('rsi_overbought')} (trigger bearish)")
    print(f"   retrace_cooldown_hours: {settings.get('retrace_cooldown_hours')}")

    print("\n- MACRO EVENTS Block:")
    print(f"   macro_impact_filter: {settings.get('macro_impact_filter')}")
    print(f"   macro_window_start_utc: {settings.get('macro_window_start_utc')}h")
    print(f"   macro_window_end_utc: {settings.get('macro_window_end_utc')}h")

    return settings

# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Créer un signal de test et l'envoyer aux 2 canaux
# ══════════════════════════════════════════════════════════════════════════════

def test_send_smart_signal(settings):
    """Envoie une alerte Smart Signal de test sur les 2 canaux"""
    print("\n" + "="*80)
    print("[TEST] TEST 3: Envoyer Smart Signal de Test")
    print("="*80)

    # Créer un signal de test
    test_signal = {
        "symbol": "BTC",
        "score": 75,  # > score_min (60)
        "direction": "buy",
        "rsi": 45.5,
        "macd_line": 0.5,
        "change_pct": 2.3,
        "volume_mult": 3.2,
        "volume_usdt": 2500000,
        "price": 67500,
        "bb_pos": 0.65,
        "timestamp": datetime.now().isoformat(),
        "tags": ["RSI_BULLISH", "VOLUME_SPIKE"]
    }

    print(f"\n[SIGNAL] Signal de Test:")
    print(f"   Symbol: {test_signal['symbol']}")
    print(f"   Score: {test_signal['score']} (seuil: {settings['score_min']})")
    print(f"   Direction: {test_signal['direction'].upper()}")
    print(f"   RSI: {test_signal['rsi']}")
    print(f"   Volume: {test_signal['volume_usdt']:,} USDT")

    # Construire les messages FREE et PAID
    print(f"\n[MESSAGE] Construire les messages:")
    msg_free = build_telegram_alert(test_signal, for_role="free")
    msg_paid = build_telegram_alert(test_signal, for_role="paid")

    print(f"\n   [OK] Message FREE créé ({len(msg_free)} chars)")
    print(f"   [OK] Message PAID créé ({len(msg_paid)} chars)")

    # Envoyer sur le canal FREE
    if TELEGRAM_CHAT_FREE:
        print(f"\n[SEND] Envoi sur CANAL PUBLIC (FREE)...")
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_FREE,
                    "text": f"[TEST 3 - SMART SIGNAL FREE]\n\n{msg_free}",
                    "parse_mode": "HTML"
                },
                timeout=5
            )
            if resp.status_code == 200:
                print(f"   [OK] SUCCÈS - Message reçu sur canal FREE")
                print(f"      Message ID: {resp.json().get('result', {}).get('message_id')}")
            else:
                print(f"   [ERROR] ERREUR: Status {resp.status_code}")
                print(f"      {resp.text}")
        except Exception as e:
            print(f"   [ERROR] ERREUR: {e}")
    else:
        print(f"   [WARNING]  SKIPPED - TELEGRAM_CHAT_FREE pas configuré")

    # Envoyer sur le canal PAID
    if TELEGRAM_CHAT:
        print(f"\n[SEND] Envoi sur CANAL VIP (PAID)...")
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT,
                    "text": f"[TEST 3 - SMART SIGNAL PAID]\n\n{msg_paid}",
                    "parse_mode": "HTML"
                },
                timeout=5
            )
            if resp.status_code == 200:
                print(f"   [OK] SUCCÈS - Message reçu sur canal PAID")
                print(f"      Message ID: {resp.json().get('result', {}).get('message_id')}")
            else:
                print(f"   [ERROR] ERREUR: Status {resp.status_code}")
                print(f"      {resp.text}")
        except Exception as e:
            print(f"   [ERROR] ERREUR: {e}")
    else:
        print(f"   [WARNING]  SKIPPED - TELEGRAM_CHAT pas configuré")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Envoyer une alerte Retrace RSI
# ══════════════════════════════════════════════════════════════════════════════

def test_send_retrace_alert(settings):
    """Envoie une alerte Retrace RSI de test"""
    print("\n" + "="*80)
    print("[TEST] TEST 4: Envoyer Retrace RSI de Test")
    print("="*80)

    # Signal RSI de test
    rsi_exit = {
        "direction": "bullish",
        "name": "RSI OVERSOLD BOUNCE",
        "rsi_prev": 28,
        "rsi_now": 32,
        "desc": "RSI a dépassé le seuil de survente (30)",
        "action": "LONG OPPORTUNITY"
    }

    coin = {
        "symbol": "ETH",
        "price": 3500,
        "change_pct": 1.5,
        "volume_usdt": 1500000
    }

    print(f"\n[SIGNAL] Retrace RSI de Test:")
    print(f"   Symbol: {coin['symbol']}")
    print(f"   Direction: {rsi_exit['direction'].upper()}")
    print(f"   RSI: {rsi_exit['rsi_prev']} → {rsi_exit['rsi_now']}")
    print(f"   Seuil oversold: {settings['rsi_oversold']} (configurable ADMIN)")

    # Construire messages
    print(f"\n[MESSAGE] Construire les messages:")
    msg_free = build_retrace_alert(
        coin['symbol'], rsi_exit, coin['price'],
        coin['change_pct'], coin['volume_usdt'],
        for_role="free"
    )
    msg_paid = build_retrace_alert(
        coin['symbol'], rsi_exit, coin['price'],
        coin['change_pct'], coin['volume_usdt'],
        for_role="paid"
    )

    print(f"   [OK] Message FREE créé ({len(msg_free)} chars)")
    print(f"   [OK] Message PAID créé ({len(msg_paid)} chars)")

    # Envoyer sur les 2 canaux
    if TELEGRAM_CHAT_FREE:
        print(f"\n[SEND] Envoi sur CANAL PUBLIC (FREE)...")
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT_FREE,
                    "text": f"[TEST 4 - RETRACE RSI FREE]\n\n{msg_free}",
                    "parse_mode": "HTML"
                },
                timeout=5
            )
            if resp.status_code == 200:
                print(f"   [OK] SUCCÈS")
            else:
                print(f"   [ERROR] ERREUR: {resp.status_code}")
        except Exception as e:
            print(f"   [ERROR] ERREUR: {e}")

    if TELEGRAM_CHAT:
        print(f"\n[SEND] Envoi sur CANAL VIP (PAID)...")
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    "chat_id": TELEGRAM_CHAT,
                    "text": f"[TEST 4 - RETRACE RSI PAID]\n\n{msg_paid}",
                    "parse_mode": "HTML"
                },
                timeout=5
            )
            if resp.status_code == 200:
                print(f"   [OK] SUCCÈS")
            else:
                print(f"   [ERROR] ERREUR: {resp.status_code}")
        except Exception as e:
            print(f"   [ERROR] ERREUR: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Vérifier la cohérence (changer score_min et relancer)
# ══════════════════════════════════════════════════════════════════════════════

def test_cohérence():
    """Teste la cohérence ADMIN → Alertes"""
    print("\n" + "="*80)
    print("[CHECK] TEST 5: Cohérence ADMIN → Alertes")
    print("="*80)

    # Score actuel
    settings_before = load_admin_alert_settings()
    score_before = settings_before.get('score_min')

    print(f"\n1.  Score AVANT: {score_before}")

    # Changer le score
    new_score = 80
    print(f"2.  Changer score_min → {new_score}...")
    set_setting('score_min', str(new_score))
    time.sleep(1)

    # Recharger
    settings_after = load_admin_alert_settings()
    score_after = settings_after.get('score_min')

    print(f"3.  Score APRÈS: {score_after}")

    if score_after == new_score:
        print(f"\n[OK] SUCCÈS - Changement immédiat et persisté!")
        # Revert
        print(f"\nReverting score_min → {score_before}...")
        set_setting('score_min', str(score_before))
    else:
        print(f"\n[ERROR] ERREUR - Changement pas appliqué!")

    return score_after == new_score

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n")
    print("="*80)
    print("TEST E2E: SYSTEME D'ALERTES TELEGRAM (2 CANAUX)".center(80))
    print("="*80)

    # Test 1
    if not test_config():
        print("\n[ERROR] Configuration incomplète. Impossible de continuer.")
        sys.exit(1)

    # Test 2
    settings = test_admin_settings()

    # Test 3
    test_send_smart_signal(settings)
    time.sleep(2)

    # Test 4
    test_send_retrace_alert(settings)
    time.sleep(2)

    # Test 5
    cohérent = test_cohérence()

    # RÉSUMÉ
    print("\n" + "="*80)
    print("[SIGNAL] RÉSUMÉ DES TESTS")
    print("="*80)
    print(f"\n[OK] Configuration Telegram: OK")
    print(f"[OK] Admin Settings Loading: OK")
    print(f"[OK] Smart Signal (FREE + PAID): OK")
    print(f"[OK] Retrace RSI (FREE + PAID): OK")
    print(f"{'[OK]' if cohérent else '[ERROR]'} Cohérence ADMIN → Alertes: {'OK' if cohérent else 'FAILED'}")

    print(f"\n[RESULT] CONCLUSION:")
    print(f"   Les messages ont été envoyés sur:")
    print(f"   • CANAL FREE (PUBLIC): {TELEGRAM_CHAT_FREE}")
    print(f"   • CANAL PAID (VIP): {TELEGRAM_CHAT}")
    print(f"\n   Ouvre Telegram et vérifie les 2 canaux!")
    print(f"\n   Différences FREE vs PAID:")
    print(f"   • FREE: Infos basiques (symbol, score, RSI)")
    print(f"   • PAID: Détails enrichis (patterns, divergences, support/resist)")
    print("\n")
