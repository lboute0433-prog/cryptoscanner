#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test tier permission system foundation."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from db import get_connection, migrate_add_subscription_tier
from security import get_user_tier, TIER_LEVELS


def test_migration():
    """Test that migration adds subscription_tier column."""
    migrate_add_subscription_tier()
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in cur.fetchall()]
        assert 'subscription_tier' in cols, "subscription_tier column not found"
        assert 'subscription_expires' in cols, "subscription_expires column not found"
        print("[OK] Migration test passed")
    finally:
        conn.close()


def test_tier_levels():
    """Test tier levels constants."""
    assert TIER_LEVELS['free'] == 0
    assert TIER_LEVELS['member'] == 1
    assert TIER_LEVELS['vip'] == 2
    print("[OK] Tier levels test passed")


def test_get_user_tier_nonexistent():
    """Test getting tier for non-existent user returns 'free'."""
    tier = get_user_tier(99999)
    assert tier == 'free', f"Expected 'free' for non-existent user, got {tier}"
    print("[OK] Non-existent user tier test passed")


if __name__ == '__main__':
    try:
        test_migration()
        test_tier_levels()
        test_get_user_tier_nonexistent()
        print("\n[OK] All foundation tests passed")
    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
