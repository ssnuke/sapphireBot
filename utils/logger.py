"""
logger.py
----------
Sets up logging to both console and file.
Config-driven: log level and file path come from config.json.
"""

import logging
import os
import csv
from datetime import datetime
from utils.config_loader import get


def setup_logger():
    """Call once at bot startup to initialize logging."""
    log_level_str = get("logging.log_level", "INFO")
    log_to_file = get("logging.log_to_file", True)
    log_file = get("logging.log_file", "logs/bot.log")

    log_level = getattr(logging, log_level_str.upper(), logging.INFO)

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    handlers = [logging.StreamHandler()]
    if log_to_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("ccxt").setLevel(logging.WARNING)

    logging.info("🤖 Bot logger initialized")


class TradeLogger:
    """Logs every trade to a CSV file for analysis."""

    def __init__(self):
        self.filepath = get("logging.trade_log_file", "logs/trades.csv")
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        self._ensure_headers()

    def _ensure_headers(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "symbol", "strategy", "signal",
                    "entry_price", "exit_price", "stop_loss",
                    "take_profit", "quantity", "pnl_inr",
                    "duration_mins", "exit_reason"
                ])

    def log_trade(self, trade: dict):
        with open(self.filepath, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                trade.get("symbol", ""),
                trade.get("strategy", ""),
                trade.get("signal", ""),
                trade.get("entry_price", ""),
                trade.get("exit_price", ""),
                trade.get("stop_loss", ""),
                trade.get("take_profit", ""),
                trade.get("quantity", ""),
                trade.get("pnl_inr", ""),
                trade.get("duration_mins", ""),
                trade.get("exit_reason", ""),
            ])