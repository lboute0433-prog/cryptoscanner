#!/usr/bin/env python3
"""
Initialize alert settings in platform_settings table.
Run this on the production server to set up JSON-formatted alert configuration.
"""
import sqlite3
import json
import sys

def init_alert_settings(db_path="/app/scanner.db"):
    """Create JSON-formatted alert settings in the database."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Define the alert configuration structure
        smart_signals = {
            'score_min': 50,
            'max_per_cycle': 3,
            'cooldown_hours': 24
        }

        retrace_rsi = {
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'cooldown_hours': 12
        }

        macro_events = {
            'importance': 'moyen',
            'enabled': True,
            'cooldown_hours': 6
        }

        # Insert or replace these settings in the platform_settings table
        cur.execute("INSERT OR REPLACE INTO platform_settings (key, value) VALUES (?, ?)",
                    ('smart_signals', json.dumps(smart_signals)))
        cur.execute("INSERT OR REPLACE INTO platform_settings (key, value) VALUES (?, ?)",
                    ('retrace_rsi', json.dumps(retrace_rsi)))
        cur.execute("INSERT OR REPLACE INTO platform_settings (key, value) VALUES (?, ?)",
                    ('macro_events', json.dumps(macro_events)))

        conn.commit()

        print("SUCCESS: Alert settings initialized")
        print(f"  smart_signals: {smart_signals}")
        print(f"  retrace_rsi: {retrace_rsi}")
        print(f"  macro_events: {macro_events}")

        # Verify the settings were created
        cur.execute("SELECT key, value FROM platform_settings WHERE key IN ('smart_signals', 'retrace_rsi', 'macro_events')")
        rows = cur.fetchall()
        print(f"\nVerification: {len(rows)} entries created")
        for key, value in rows:
            parsed = json.loads(value)
            print(f"  {key}: OK (score_min={parsed.get('score_min', 'N/A')})")

        conn.close()
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "/app/scanner.db"
    success = init_alert_settings(db_path)
    sys.exit(0 if success else 1)
