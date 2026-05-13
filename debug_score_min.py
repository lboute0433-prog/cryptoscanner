#!/usr/bin/env python3
"""Debug: Tracer le chargement de score_min depuis la DB"""

from db import get_setting
from scanner_engine import load_admin_alert_settings
import sqlite3

print("[STEP 1] Lire score_min directement depuis DB...")
raw_value = get_setting('score_min', '')
print(f"  get_setting('score_min') = '{raw_value}'")
print(f"  Type: {type(raw_value)}")

print("\n[STEP 2] Charger via load_admin_alert_settings()...")
settings = load_admin_alert_settings()
score_min = settings.get('score_min')
print(f"  load_admin_alert_settings()['score_min'] = {score_min}")
print(f"  Type: {type(score_min)}")

print("\n[STEP 3] Verifier la DB directement...")
conn = sqlite3.connect('cryptoscanner.db')
cursor = conn.cursor()
cursor.execute("SELECT key, value FROM platform_settings WHERE key='score_min'")
row = cursor.fetchone()
if row:
    print(f"  DB: key='{row[0]}', value='{row[1]}'")
else:
    print(f"  DB: Pas d'entree score_min")
conn.close()

print("\n[STEP 4] Tous les settings actuels:")
for key, value in sorted(settings.items()):
    print(f"  {key}: {value}")
