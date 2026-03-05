"""
data_fetcher.py
---------------
Historical data fetcher for backtesting.
Supports multiple data sources: CCXT, CSV files, and caching.

Data Sources Priority:
1. Local cache (fastest)
2. CCXT exchange API (fallback)
3. Manual CSV import (for custom datasets)
"""

import os
import json
import logging
import ccxt
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DataFetcher:
    """
    Fetches and manages historical OHLCV data for backtesting.
    
    Usage:
        fetcher = DataFetcher(exchange="binance")
        data = fetcher.fetch_historical("BTC/USDT", "15m", days=90)
    """
    
    def __init__(self, exchange: str = "binance", cache_dir: str = "data/cache"):
        self.exchange_id = exchange
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize exchange
        exchange_class = getattr(ccxt, exchange)
        self.exchange = exchange_class({
            "enableRateLimit": True,
            "options": {"defaultType": "future"}
        })
        
        logger.info(f"📊 DataFetcher initialized for {exchange.upper()}")
    
    def fetch_historical(
        self,
        symbol: str,
        timeframe: str,
        days: int = 90,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Fetch historical OHLCV data for backtesting.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            timeframe: Candle interval ("1m", "5m", "15m", "1h", "4h", "1d")
            days: Number of days of historical data
            use_cache: Whether to use cached data if available
        
        Returns:
            List of candle dicts with keys: timestamp, open, high, low, close, volume
        """
        cache_file = self._get_cache_filename(symbol, timeframe, days)
        
        # Try loading from cache first
        if use_cache and os.path.exists(cache_file):
            logger.info(f"📁 Loading from cache: {cache_file}")
            return self._load_from_cache(cache_file)
        
        # Fetch from exchange
        logger.info(f"🌐 Fetching {days} days of {symbol} {timeframe} data from {self.exchange_id}...")
        candles = self._fetch_from_exchange(symbol, timeframe, days)
        
        # Save to cache
        self._save_to_cache(candles, cache_file)
        
        logger.info(f"✅ Fetched {len(candles)} candles ({candles[0]['timestamp']} to {candles[-1]['timestamp']})")
        return candles
    
    def _fetch_from_exchange(self, symbol: str, timeframe: str, days: int) -> List[Dict]:
        """Fetch data from exchange API with rate limiting and pagination."""
        timeframe_minutes = self._timeframe_to_minutes(timeframe)
        candles_needed = (days * 24 * 60) // timeframe_minutes
        
        # CCXT limit per request (usually 1000-1500)
        limit_per_request = 1000
        all_candles = []
        
        since = self.exchange.parse8601(
            (datetime.utcnow() - timedelta(days=days)).isoformat()
        )
        
        while len(all_candles) < candles_needed:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    symbol,
                    timeframe=timeframe,
                    since=since,
                    limit=limit_per_request
                )
                
                if not ohlcv:
                    break
                
                # Convert to dict format
                for row in ohlcv:
                    all_candles.append({
                        "timestamp": datetime.fromtimestamp(row[0] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                        "open": row[1],
                        "high": row[2],
                        "low": row[3],
                        "close": row[4],
                        "volume": row[5],
                    })
                
                # Update since for next batch
                since = ohlcv[-1][0] + 1
                
                logger.debug(f"Fetched {len(ohlcv)} candles (total: {len(all_candles)})")
                
                # Break if we got less than requested (end of available data)
                if len(ohlcv) < limit_per_request:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                break
        
        return all_candles[:candles_needed]
    
    def import_from_csv(self, filepath: str) -> List[Dict]:
        """
        Import historical data from CSV file.
        
        CSV Format:
            timestamp,open,high,low,close,volume
            2024-01-01 00:00:00,42000,42500,41800,42200,1500
        """
        logger.info(f"📄 Importing data from {filepath}")
        candles = []
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                candles.append({
                    "timestamp": row["timestamp"],
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row["volume"]),
                })
        
        logger.info(f"✅ Imported {len(candles)} candles from CSV")
        return candles
    
    def export_to_csv(self, candles: List[Dict], filepath: str):
        """Export candles to CSV for backup or manual analysis."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp", "open", "high", "low", "close", "volume"])
            writer.writeheader()
            writer.writerows(candles)
        
        logger.info(f"💾 Exported {len(candles)} candles to {filepath}")
    
    def _get_cache_filename(self, symbol: str, timeframe: str, days: int) -> str:
        """Generate cache filename based on parameters."""
        safe_symbol = symbol.replace("/", "_")
        return os.path.join(self.cache_dir, f"{safe_symbol}_{timeframe}_{days}d.json")
    
    def _save_to_cache(self, candles: List[Dict], filepath: str):
        """Save candles to JSON cache."""
        with open(filepath, 'w') as f:
            json.dump(candles, f)
        logger.debug(f"💾 Saved to cache: {filepath}")
    
    def _load_from_cache(self, filepath: str) -> List[Dict]:
        """Load candles from JSON cache."""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _timeframe_to_minutes(self, timeframe: str) -> int:
        """Convert timeframe string to minutes."""
        mapping = {
            "1m": 1, "3m": 3, "5m": 5, "15m": 15,
            "30m": 30, "1h": 60, "2h": 120, "4h": 240,
            "6h": 360, "12h": 720, "1d": 1440
        }
        return mapping.get(timeframe, 15)
