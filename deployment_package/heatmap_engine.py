"""
Heatmap Engine — OI + Volume Intensity Calculation & Cache Management
"""
import os
from typing import List, Dict, Any
import requests
from datetime import datetime
import sqlite3
import logging

logger = logging.getLogger(__name__)

# Environment variables (defaults)
VOLUME_WEIGHT = float(os.getenv('HEATMAP_VOLUME_WEIGHT', 0.6))
OI_WEIGHT = float(os.getenv('HEATMAP_OI_WEIGHT', 0.4))
THRESHOLD_LOW = float(os.getenv('HEATMAP_THRESHOLD_LOW', 0.4))
THRESHOLD_HIGH = float(os.getenv('HEATMAP_THRESHOLD_HIGH', 0.7))

BINANCE_API_URL = "https://fapi.binance.com"
DB_PATH = "cryptoscanner.db"


def normalize_values(values: List[float]) -> List[float]:
    """
    Normalize values to [0, 1] range.
    Edge case: if all values are identical, return [0.5, 0.5, ...]
    """
    if not values:
        return []
    
    min_val = min(values)
    max_val = max(values)
    
    # Edge case: all values identical
    if min_val == max_val:
        return [0.5] * len(values)
    
    return [(v - min_val) / (max_val - min_val) for v in values]


def calculate_intensity(volume_normalized: float, oi_normalized: float) -> float:
    """
    Calculate intensity as weighted blend:
    intensity = 0.6 * volume_normalized + 0.4 * oi_normalized
    """
    return VOLUME_WEIGHT * volume_normalized + OI_WEIGHT * oi_normalized


def assign_color(intensity: float) -> str:
    """
    Assign color based on intensity threshold:
    < 0.4 → blue
    0.4-0.7 → orange
    ≥ 0.7 → red
    """
    if intensity < THRESHOLD_LOW:
        return "blue"
    elif intensity < THRESHOLD_HIGH:
        return "orange"
    else:
        return "red"


class HeatmapCalculator:
    """Manage heatmap calculations and SQLite cache"""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crypto_heatmap (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT UNIQUE NOT NULL,
                    intensity REAL NOT NULL,
                    color TEXT NOT NULL,
                    volume_24h REAL,
                    oi_variation_1h REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS oi_history (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    oi_value REAL NOT NULL,
                    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Table initialization error: {e}")
    
    def fetch_binance_data(self) -> List[Dict[str, Any]]:
        """
        Fetch 24h ticker + OI data from Binance Futures REST API.
        Returns: [{"symbol": "BTC", "volume_24h": ..., "oi_change_1h": ...}, ...]
        """
        try:
            # Get all tickers
            tickers_resp = requests.get(
                f"{BINANCE_API_URL}/fapi/v1/ticker/24hr",
                timeout=5
            )
            tickers = tickers_resp.json()
            
            if not isinstance(tickers, list):
                logger.error(f"Invalid ticker response: {tickers}")
                return []
            
            # Build crypto list with volume
            cryptos = []
            for ticker in tickers:
                symbol = ticker.get("symbol", "").replace("USDT", "")
                if symbol:
                    cryptos.append({
                        "symbol": symbol,
                        "volume_24h": float(ticker.get("quoteAssetVolume", 0)),
                        "oi_change_1h": 0.0  # Placeholder (see step below)
                    })
            
            return cryptos
        
        except Exception as e:
            logger.error(f"Binance API error: {e}")
            return []
    
    def get_oi_1h_variation(self, symbol: str) -> float:
        """
        Calculate OI variation over last 1 hour.
        Fetch current OI, compare with snapshot from 1h ago.
        If no 1h snapshot, return 0.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get OI from 1h ago (order by DESC, limit 1)
            cursor.execute("""
                SELECT oi_value FROM oi_history
                WHERE symbol = ? AND snapshot_time > datetime('now', '-1 hour')
                ORDER BY snapshot_time ASC
                LIMIT 1
            """, (symbol,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return 0.0  # No historical data
            
            oi_1h_ago = row[0]
            
            # Fetch current OI
            resp = requests.get(
                f"{BINANCE_API_URL}/fapi/v1/openInterest",
                params={"symbol": f"{symbol}USDT"},
                timeout=5
            )
            current_oi = float(resp.json().get("openInterest", 0))
            
            if oi_1h_ago == 0:
                return 0.0
            
            variation = ((current_oi - oi_1h_ago) / oi_1h_ago) * 100
            
            # Store current snapshot
            self.store_oi_snapshot(symbol, current_oi)
            
            return variation
        
        except Exception as e:
            logger.error(f"OI variation error for {symbol}: {e}")
            return 0.0
    
    def store_oi_snapshot(self, symbol: str, oi_value: float):
        """Store current OI snapshot in oi_history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO oi_history (symbol, oi_value, snapshot_time)
                VALUES (?, ?, datetime('now'))
            """, (symbol, oi_value))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Store OI snapshot error: {e}")
    
    def process_cryptos(self, cryptos_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process raw crypto data → calculate intensity → assign color → return results.
        
        Args:
            cryptos_data: [{"symbol": "BTC", "volume_24h": 28e9, "oi_change_1h": 3.2}, ...]
        
        Returns:
            [{"symbol": "BTC", "intensity": 0.82, "color": "red", ...}, ...]
        """
        if not cryptos_data:
            return []
        
        # Extract volumes and OI variations
        volumes = [c.get("volume_24h", 0) for c in cryptos_data]
        oi_changes = [c.get("oi_change_1h", 0) for c in cryptos_data]
        
        # Normalize
        volumes_norm = normalize_values(volumes)
        oi_norm = normalize_values(oi_changes)
        
        # Calculate intensities
        results = []
        for i, crypto in enumerate(cryptos_data):
            intensity = calculate_intensity(volumes_norm[i], oi_norm[i])
            color = assign_color(intensity)
            
            results.append({
                "symbol": crypto["symbol"],
                "intensity": round(intensity, 4),
                "color": color,
                "volume_24h": crypto.get("volume_24h"),
                "oi_variation_1h": crypto.get("oi_change_1h")
            })
        
        return results
    
    def update_cache(self, cryptos_result: List[Dict[str, Any]]):
        """Update crypto_heatmap table with latest intensities"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for crypto in cryptos_result:
                cursor.execute("""
                    INSERT OR REPLACE INTO crypto_heatmap
                    (symbol, intensity, color, volume_24h, oi_variation_1h, last_updated)
                    VALUES (?, ?, ?, ?, ?, datetime('now'))
                """, (
                    crypto["symbol"],
                    crypto["intensity"],
                    crypto["color"],
                    crypto.get("volume_24h"),
                    crypto.get("oi_variation_1h")
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cache updated: {len(cryptos_result)} cryptos")
        
        except Exception as e:
            logger.error(f"Cache update error: {e}")
    
    def get_all_from_cache(self) -> List[Dict[str, Any]]:
        """Fetch all cryptos from cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT symbol, intensity, color, volume_24h, oi_variation_1h FROM crypto_heatmap")
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    "symbol": row[0],
                    "intensity": row[1],
                    "color": row[2],
                    "volume_24h": row[3],
                    "oi_change_1h": row[4]
                }
                for row in rows
            ]
        
        except Exception as e:
            logger.error(f"Cache fetch error: {e}")
            return []
    
    def run_update_cycle(self):
        """
        Full update cycle: fetch → calculate → cache → return deltas
        Call every 10s from background thread
        """
        try:
            # Fetch from Binance
            cryptos_data = self.fetch_binance_data()
            
            if not cryptos_data:
                logger.warning("No data from Binance")
                return None
            
            # Get OI variations
            for crypto in cryptos_data:
                crypto["oi_change_1h"] = self.get_oi_1h_variation(crypto["symbol"])
            
            # Calculate intensities
            results = self.process_cryptos(cryptos_data)
            
            # Update cache
            self.update_cache(results)
            
            return results
        
        except Exception as e:
            logger.error(f"Update cycle error: {e}")
            return None
