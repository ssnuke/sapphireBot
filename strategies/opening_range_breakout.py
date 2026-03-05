"""
opening_range_breakout.py
--------------------------
Strategy: Opening Range Breakout (ORB)

Logic:
  - Define the "opening range" as the first candle of the trading session
    (for crypto, use the first candle after 00:00 UTC daily)
  - BUY  when price breaks ABOVE the opening range high
  - SELL when price breaks BELOW the opening range low

Stop Loss: Opposite side of the opening range
Timeframe: 15m
"""

import logging
from datetime import datetime, timezone
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


class OpeningRangeBreakoutStrategy(BaseStrategy):

    def __init__(self, symbol: str, timeframe: str):
        super().__init__(symbol, timeframe)
        self.orb_candles = 4            # Use first 4 x 15m candles = 1 hour range
        self.range_high: float | None = None
        self.range_low: float | None = None
        self.range_set_date: str | None = None
        self.breakout_atr_multiplier = 0.3  # Small buffer beyond range

    def get_name(self) -> str:
        return "opening_range_breakout"

    def _set_opening_range(self, candles: list[dict]):
        """Set today's opening range from the first N candles of the day."""
        today = datetime.now(timezone.utc).date().isoformat()

        # Only recalculate once per day
        if self.range_set_date == today:
            return

        # Get candles from today's open (00:00 UTC)
        today_candles = [c for c in candles if self._is_today(c["timestamp"])]

        if len(today_candles) >= self.orb_candles:
            range_candles = today_candles[:self.orb_candles]
            self.range_high = max(c["high"] for c in range_candles)
            self.range_low = min(c["low"] for c in range_candles)
            self.range_set_date = today
            self.logger.info(
                f"📏 ORB set for {today}: High={self.range_high:.4f} Low={self.range_low:.4f}"
            )

    def _is_today(self, timestamp_ms: int) -> bool:
        """Check if a candle timestamp belongs to today (UTC)."""
        today = datetime.now(timezone.utc).date()
        candle_date = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).date()
        return candle_date == today

    def generate_signal(self, candles: list[dict]) -> str | None:
        if not self.validate_candles(candles, min_required=self.orb_candles + 5):
            return None

        self._set_opening_range(candles)

        if self.range_high is None or self.range_low is None:
            self.logger.debug("Opening range not set yet. Waiting for enough candles.")
            return None

        current_close = candles[-1]["close"]
        prev_close = candles[-2]["close"]

        # Breakout above range high
        if prev_close <= self.range_high and current_close > self.range_high:
            self.logger.info(
                f"📗 BUY signal | ORB breakout above {self.range_high:.4f} | Close: {current_close:.4f}"
            )
            return "buy"

        # Breakdown below range low
        if prev_close >= self.range_low and current_close < self.range_low:
            self.logger.info(
                f"📕 SELL signal | ORB breakdown below {self.range_low:.4f} | Close: {current_close:.4f}"
            )
            return "sell"

        return None

    def get_stop_loss(self, candles: list[dict], signal: str, entry_price: float) -> float:
        if signal == "buy":
            # Stop at the range low (full range acts as stop)
            stop = self.range_low
        else:
            # Stop at the range high
            stop = self.range_high

        self.logger.info(f"🛑 Stop loss: {stop:.4f}")
        return round(stop, 4)