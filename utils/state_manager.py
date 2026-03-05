"""
state_manager.py
----------------
Manages session persistence and recovery.
Stores:
  - Open positions (loaded by PositionTracker)
  - RiskManager state (daily/weekly PnL, trades)
  - Last sync time, balance, etc.

On startup, call load() to restore the bot state.
Periodically call save() to persist current state.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class StateManager:
    def __init__(self, state_file: str = "data/bot_state.json"):
        self.state_file = state_file
        self.state = self._default_state()
        os.makedirs(os.path.dirname(state_file), exist_ok=True)

    @staticmethod
    def _default_state() -> Dict:
        return {
            "version": "1.0",
            "last_save": datetime.utcnow().isoformat(),
            "last_sync": datetime.utcnow().isoformat(),
            "balance": 0.0,
            "daily_pnl": 0.0,
            "weekly_pnl": 0.0,
            "trades_today": 0,
            "last_reset_date": datetime.now().date().isoformat(),
            "risk_manager": {},
            "open_positions": [],
            "error_count": 0,
            "restart_count": 0,
        }

    def load(self) -> bool:
        """Load state from disk if it exists."""
        if not os.path.exists(self.state_file):
            logger.info(f"No previous state file found at {self.state_file}")
            return False
        try:
            with open(self.state_file, "r") as f:
                self.state = json.load(f)
            logger.info(f"Loaded state from {self.state_file}")
            self.state["restart_count"] = self.state.get("restart_count", 0) + 1
            return True
        except Exception as e:
            logger.error(f"Failed to load state: {e}", exc_info=True)
            return False

    def save(self) -> bool:
        """Save current state to disk."""
        try:
            self.state["last_save"] = datetime.utcnow().isoformat()
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)
            return False

    def update_risk_manager(
        self,
        daily_pnl: float,
        weekly_pnl: float,
        trades_today: int,
        balance: float,
        last_reset_date: str,
    ):
        """Update RiskManager snapshot in state."""
        self.state["daily_pnl"] = daily_pnl
        self.state["weekly_pnl"] = weekly_pnl
        self.state["trades_today"] = trades_today
        self.state["balance"] = balance
        self.state["last_reset_date"] = last_reset_date

    def increment_error_count(self):
        """Increment error counter."""
        self.state["error_count"] = self.state.get("error_count", 0) + 1

    def get(self, key: str, default=None) -> Optional[object]:
        """Get state value."""
        return self.state.get(key, default)

    def pretty_print(self) -> str:
        """Return human-readable state summary."""
        return json.dumps(self.state, indent=2, default=str)
