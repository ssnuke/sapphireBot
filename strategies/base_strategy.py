"""
base_strategy.py
-----------------
All strategies MUST inherit from BaseStrategy.
Enforces a consistent interface so main.py can swap strategies
just by changing config.json → strategy → active
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.

    Every strategy must implement:
    - generate_signal()  → returns "buy", "sell", or None
    - get_stop_loss()    → returns stop loss price
    - get_name()         → returns strategy name string

    Optional override:
    - on_trade_closed()  → called when a trade closes (for strategy-level tracking)
    """

    def __init__(self, symbol: str, timeframe: str):
        self.symbol = symbol
        self.timeframe = timeframe
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_name(self) -> str:
        """Return the strategy name. Must match config.json → strategy → active."""
        pass

    @abstractmethod
    def generate_signal(self, candles: list[dict]) -> str | None:
        """
        Analyze candles and return a signal.

        Args:
            candles: List of OHLCV dicts with keys:
                     [timestamp, open, high, low, close, volume]

        Returns:
            "buy"  → Open long position
            "sell" → Open short position
            None   → No signal, do nothing
        """
        pass

    @abstractmethod
    def get_stop_loss(self, candles: list[dict], signal: str, entry_price: float) -> float:
        """
        Calculate stop loss price for the trade.

        Args:
            candles:      Recent OHLCV candles
            signal:       "buy" or "sell"
            entry_price:  The entry price of the trade

        Returns:
            Stop loss price as float
        """
        pass

    def on_trade_closed(self, pnl: float, signal: str):
        """
        Optional hook called when a trade closes.
        Override in your strategy for strategy-level tracking.
        """
        pass

    def validate_candles(self, candles: list[dict], min_required: int = 50) -> bool:
        """Validate we have enough candles before running strategy logic."""
        if not candles or len(candles) < min_required:
            self.logger.warning(
                f"Not enough candles: got {len(candles) if candles else 0}, need {min_required}"
            )
            return False
        return True