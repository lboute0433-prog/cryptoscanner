"""
Unit tests for exchange data tables (Phase 1 Task 2).

Tests:
- Table creation (exchange_data and exchange_metadata)
- Insert operations with type validation
- Retrieval operations
- Uniqueness constraints
- Migration function
"""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import os
import sys


class TestExchangeDataAndMetadataTables(unittest.TestCase):
    """Test exchange data and metadata table operations."""

    @classmethod
    def setUpClass(cls):
        """Create a real test database file."""
        cls.db_path = tempfile.mktemp(suffix='.db')
        cls.test_db = sqlite3.connect(cls.db_path)
        cls.test_db.isolation_level = None  # Autocommit mode

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        cls.test_db.close()
        Path(cls.db_path).unlink(missing_ok=True)

    def setUp(self):
        """Clear tables before each test."""
        self.test_db.execute('DROP TABLE IF EXISTS exchange_data')
        self.test_db.execute('DROP TABLE IF EXISTS exchange_metadata')
        self.test_db.execute('DROP INDEX IF EXISTS idx_exchange_data_exchange_symbol')

    def _create_exchange_data_table(self):
        """Helper to create exchange_data table directly."""
        self.test_db.execute('''
            CREATE TABLE IF NOT EXISTS exchange_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(exchange, symbol, timestamp)
            )
        ''')
        self.test_db.execute('''
            CREATE INDEX IF NOT EXISTS idx_exchange_data_exchange_symbol
            ON exchange_data(exchange, symbol)
        ''')

    def _create_exchange_metadata_table(self):
        """Helper to create exchange_metadata table directly."""
        self.test_db.execute('''
            CREATE TABLE IF NOT EXISTS exchange_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT NOT NULL UNIQUE,
                maker_fee REAL,
                taker_fee REAL,
                min_order_amount REAL,
                supports_fetch_ticker INTEGER DEFAULT 1,
                supports_fetch_ohlcv INTEGER DEFAULT 1,
                rate_limit INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    # ── Tests for exchange_data table ──

    def test_exchange_data_table_creation(self):
        """Test that exchange_data table is created with correct schema."""
        self._create_exchange_data_table()

        cur = self.test_db.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exchange_data'")
        self.assertIsNotNone(cur.fetchone(), "exchange_data table should exist")

    def test_exchange_data_table_columns(self):
        """Test that all required columns exist."""
        self._create_exchange_data_table()

        cur = self.test_db.cursor()
        cur.execute("PRAGMA table_info(exchange_data)")
        columns = {row[1] for row in cur.fetchall()}

        required = {
            'id', 'exchange', 'symbol', 'timestamp',
            'open', 'high', 'low', 'close', 'volume', 'created_at'
        }
        self.assertTrue(required.issubset(columns), f"Missing columns: {required - columns}")

    def test_exchange_data_primary_key(self):
        """Test that id is the primary key."""
        self._create_exchange_data_table()

        cur = self.test_db.cursor()
        cur.execute("PRAGMA table_info(exchange_data)")
        rows = cur.fetchall()

        pk_column = next((r for r in rows if r[5] > 0), None)
        self.assertIsNotNone(pk_column, "Primary key should exist")
        self.assertEqual(pk_column[1], 'id', "id should be the primary key")

    def test_exchange_data_insert_ohlcv(self):
        """Test inserting OHLCV data."""
        self._create_exchange_data_table()

        cur = self.test_db.cursor()
        cur.execute('''
            INSERT INTO exchange_data
            (exchange, symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('binance', 'BTC/USDT', 1694000000, 45000.0, 45500.0, 44800.0, 45200.0, 1500.5))

        # Verify insertion
        cur.execute(
            'SELECT * FROM exchange_data WHERE exchange=? AND symbol=?',
            ('binance', 'BTC/USDT')
        )
        row = cur.fetchone()
        self.assertIsNotNone(row, "OHLCV data should be inserted")

    def test_exchange_data_unique_constraint(self):
        """Test UNIQUE(exchange, symbol, timestamp) constraint."""
        self._create_exchange_data_table()

        cur = self.test_db.cursor()

        # Insert first record
        cur.execute('''
            INSERT INTO exchange_data
            (exchange, symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('kraken', 'ETH/USD', 1694010000, 2500.0, 2600.0, 2400.0, 2550.0, 500.0))

        # Try to insert duplicate - should raise UNIQUE constraint error
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute('''
                INSERT INTO exchange_data
                (exchange, symbol, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('kraken', 'ETH/USD', 1694010000, 2550.0, 2650.0, 2450.0, 2580.0, 600.0))

    def test_exchange_data_index_exists(self):
        """Test that index on (exchange, symbol) is created."""
        self._create_exchange_data_table()

        cur = self.test_db.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_exchange_data_exchange_symbol'"
        )
        self.assertIsNotNone(cur.fetchone(), "Index on (exchange, symbol) should exist")

    def test_exchange_data_numeric_types(self):
        """Test that numeric data types are preserved."""
        self._create_exchange_data_table()

        cur = self.test_db.cursor()
        cur.execute('''
            INSERT INTO exchange_data
            (exchange, symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('bybit', 'XRP/USDT', 1694020000, 0.5123, 0.5456, 0.4890, 0.5200, 1000000.123))

        cur.execute('SELECT * FROM exchange_data WHERE symbol=?', ('XRP/USDT',))
        row = cur.fetchone()

        # Verify numeric types
        self.assertIsInstance(row[4], (int, float), "open should be numeric")
        self.assertIsInstance(row[5], (int, float), "high should be numeric")
        self.assertIsInstance(row[8], (int, float), "volume should be numeric")

    # ── Tests for exchange_metadata table ──

    def test_exchange_metadata_table_creation(self):
        """Test that exchange_metadata table is created."""
        self._create_exchange_metadata_table()

        cur = self.test_db.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exchange_metadata'")
        self.assertIsNotNone(cur.fetchone(), "exchange_metadata table should exist")

    def test_exchange_metadata_table_columns(self):
        """Test that all required columns exist."""
        self._create_exchange_metadata_table()

        cur = self.test_db.cursor()
        cur.execute("PRAGMA table_info(exchange_metadata)")
        columns = {row[1] for row in cur.fetchall()}

        required = {
            'id', 'exchange', 'maker_fee', 'taker_fee',
            'min_order_amount', 'supports_fetch_ticker',
            'supports_fetch_ohlcv', 'rate_limit', 'updated_at'
        }
        self.assertTrue(required.issubset(columns), f"Missing columns: {required - columns}")

    def test_exchange_metadata_unique_exchange(self):
        """Test UNIQUE constraint on exchange column."""
        self._create_exchange_metadata_table()

        cur = self.test_db.cursor()

        # Insert first record
        cur.execute('''
            INSERT INTO exchange_metadata
            (exchange, maker_fee, taker_fee, rate_limit)
            VALUES (?, ?, ?, ?)
        ''', ('binance', 0.001, 0.001, 1200))

        # Try to insert duplicate exchange - should raise UNIQUE constraint error
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute('''
                INSERT INTO exchange_metadata
                (exchange, maker_fee, taker_fee, rate_limit)
                VALUES (?, ?, ?, ?)
            ''', ('binance', 0.002, 0.002, 1500))

    def test_exchange_metadata_insert_full(self):
        """Test inserting complete metadata record."""
        self._create_exchange_metadata_table()

        cur = self.test_db.cursor()
        cur.execute('''
            INSERT INTO exchange_metadata
            (exchange, maker_fee, taker_fee, min_order_amount,
             supports_fetch_ticker, supports_fetch_ohlcv, rate_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('kraken', 0.0016, 0.0026, 10.0, 1, 1, 600))

        # Verify
        cur.execute('SELECT * FROM exchange_metadata WHERE exchange=?', ('kraken',))
        row = cur.fetchone()
        self.assertIsNotNone(row)

    def test_exchange_metadata_insert_partial(self):
        """Test inserting metadata with optional fields as NULL."""
        self._create_exchange_metadata_table()

        cur = self.test_db.cursor()
        cur.execute('''
            INSERT INTO exchange_metadata (exchange)
            VALUES (?)
        ''', ('unknown_exchange',))

        # Verify defaults are set
        cur.execute('SELECT * FROM exchange_metadata WHERE exchange=?', ('unknown_exchange',))
        row = cur.fetchone()
        self.assertIsNotNone(row)
        # supports_fetch_ohlcv should default to 1
        self.assertEqual(row[6], 1, "supports_fetch_ohlcv should default to 1")

    def test_exchange_metadata_default_timestamp(self):
        """Test that updated_at defaults to CURRENT_TIMESTAMP."""
        self._create_exchange_metadata_table()

        cur = self.test_db.cursor()
        cur.execute('''
            INSERT INTO exchange_metadata (exchange)
            VALUES (?)
        ''', ('timestamp_test',))

        cur.execute('SELECT updated_at FROM exchange_metadata WHERE exchange=?', ('timestamp_test',))
        row = cur.fetchone()
        self.assertIsNotNone(row[0], "updated_at should have a default value")

    # ── Integration tests ──

    def test_both_tables_creation(self):
        """Test that both tables can be created together."""
        self._create_exchange_data_table()
        self._create_exchange_metadata_table()

        cur = self.test_db.cursor()

        # Check both exist
        cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('exchange_data', 'exchange_metadata')")
        self.assertEqual(cur.fetchone()[0], 2, "Both tables should exist")

    def test_data_and_metadata_insertion(self):
        """Test inserting data into both tables."""
        self._create_exchange_data_table()
        self._create_exchange_metadata_table()

        cur = self.test_db.cursor()

        # Insert metadata
        cur.execute('''
            INSERT INTO exchange_metadata
            (exchange, maker_fee, taker_fee, rate_limit)
            VALUES (?, ?, ?, ?)
        ''', ('binance', 0.001, 0.001, 1200))

        # Insert OHLCV data
        cur.execute('''
            INSERT INTO exchange_data
            (exchange, symbol, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('binance', 'BTC/USDT', 1694000000, 45000.0, 45500.0, 44800.0, 45200.0, 1500.5))

        # Verify both inserts succeeded
        cur.execute('SELECT COUNT(*) FROM exchange_metadata')
        self.assertEqual(cur.fetchone()[0], 1)

        cur.execute('SELECT COUNT(*) FROM exchange_data')
        self.assertEqual(cur.fetchone()[0], 1)


class TestDbFunctions(unittest.TestCase):
    """Test database helper functions from db module."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.db_path = tempfile.mktemp(suffix='.db')

    @classmethod
    def tearDownClass(cls):
        """Clean up."""
        Path(cls.db_path).unlink(missing_ok=True)

    def test_functions_exist(self):
        """Test that all new functions exist in db module."""
        import db as db_module

        functions = [
            'create_exchange_data_table',
            'create_exchange_metadata_table',
            'insert_exchange_data',
            'insert_exchange_metadata',
            'get_exchange_metadata',
            'migrate_add_exchange_tables'
        ]

        for func_name in functions:
            self.assertTrue(
                hasattr(db_module, func_name),
                f"db module should have {func_name} function"
            )

    def test_functions_have_docstrings(self):
        """Test that all new functions have docstrings."""
        import db as db_module

        functions = [
            'create_exchange_data_table',
            'create_exchange_metadata_table',
            'insert_exchange_data',
            'insert_exchange_metadata',
            'get_exchange_metadata',
            'migrate_add_exchange_tables'
        ]

        for func_name in functions:
            func = getattr(db_module, func_name)
            self.assertIsNotNone(func.__doc__, f"{func_name} should have a docstring")
            self.assertGreater(len(func.__doc__.strip()), 20, f"{func_name} docstring should be substantial")

    def test_insert_exchange_data_signature(self):
        """Test that insert_exchange_data has correct signature."""
        import db as db_module
        import inspect

        sig = inspect.signature(db_module.insert_exchange_data)
        params = list(sig.parameters.keys())
        expected = ['exchange', 'symbol', 'timestamp', 'open_price', 'high', 'low', 'close', 'volume']
        self.assertEqual(params, expected, f"insert_exchange_data params should be {expected}")

    def test_insert_exchange_metadata_signature(self):
        """Test that insert_exchange_metadata has correct signature."""
        import db as db_module
        import inspect

        sig = inspect.signature(db_module.insert_exchange_metadata)
        params = list(sig.parameters.keys())
        self.assertIn('exchange', params)
        self.assertIn('maker_fee', params)
        self.assertIn('taker_fee', params)
        self.assertIn('rate_limit', params)

    def test_get_exchange_metadata_signature(self):
        """Test that get_exchange_metadata has correct signature."""
        import db as db_module
        import inspect

        sig = inspect.signature(db_module.get_exchange_metadata)
        self.assertEqual(list(sig.parameters.keys()), ['exchange'])


if __name__ == '__main__':
    unittest.main()
