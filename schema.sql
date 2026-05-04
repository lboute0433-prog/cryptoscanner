-- Heatmap OI+Volume Cache
CREATE TABLE IF NOT EXISTS crypto_heatmap (
  id INTEGER PRIMARY KEY,
  symbol TEXT UNIQUE NOT NULL,
  intensity REAL NOT NULL,
  color TEXT NOT NULL,
  volume_24h REAL,
  oi_variation_1h REAL,
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_crypto_heatmap_symbol ON crypto_heatmap(symbol);

-- Historical OI snapshots (for calculating 1h variation)
CREATE TABLE IF NOT EXISTS oi_history (
  id INTEGER PRIMARY KEY,
  symbol TEXT NOT NULL,
  oi_value REAL NOT NULL,
  snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (symbol) REFERENCES crypto_heatmap(symbol)
);

CREATE INDEX IF NOT EXISTS idx_oi_history_symbol_time ON oi_history(symbol, snapshot_time);
