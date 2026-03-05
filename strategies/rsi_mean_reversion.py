"""
rsi_mean_reversion.py
----------------------
Strategy: RSI Mean Reversion

Logic:
  BUY  when RSI drops below 30 (oversold) then crosses back above 33
  SELL when RSI rises above 70 (overbought) then crosses back below 67

Stop Loss: Recent swing low/high (last 5 candles) with ATR buffer
Timeframe: 15m
"""

import logging
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


def _rsi(closes: list[float], period: int = 14) -> list[float]:
    """Calculate RSI values for a list of closing prices."""
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = []
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(round(100 - (100 / (1 + rs)), 2))

    return rsi_values


def _atr(candles: list[dict], period: int = 14) -> float:
    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    return sum(true_ranges[-period:]) / period


class RSIMeanReversionStrategy(BaseStrategy):

    def __init__(self, symbol: str, timeframe: str):
        super().__init__(symbol, timeframe)
        self.oversold = 30
        self.overbought = 70
        self.buy_cross = 33      # RSI must cross back above this to confirm buy
        self.sell_cross = 67     # RSI must cross back below this to confirm sell
        self.rsi_period = 14
        self._was_oversold = False
        self._was_overbought = False

    def get_name(self) -> str:
        return "rsi_mean_reversion"

    def generate_signal(self, candles: list[dict]) -> str | None:
        if not self.validate_candles(candles, min_required=self.rsi_period + 10):
            return None

        closes = [c["close"] for c in candles]
        rsi = _rsi(closes, self.rsi_period)

        if len(rsi) < 2:
            return None

        curr_rsi = rsi[-1]
        prev_rsi = rsi[-2]

        # Track oversold/overbought state
        if curr_rsi < self.oversold:
            self._was_oversold = True
        if curr_rsi > self.overbought:
            self._was_overbought = True

        # BUY: Was oversold, now recovering above buy_cross
        if self._was_oversold and prev_rsi <= self.buy_cross and curr_rsi > self.buy_cross:
            self._was_oversold = False
            self.logger.info(f"📗 BUY signal | RSI recovered: {prev_rsi:.1f} → {curr_rsi:.1f}")
            return "buy"

        # SELL: Was overbought, now dropping below sell_cross
        if self._was_overbought and prev_rsi >= self.sell_cross and curr_rsi < self.sell_cross:
            self._was_overbought = False
            self.logger.info(f"📕 SELL signal | RSI dropped: {prev_rsi:.1f} → {curr_rsi:.1f}")
            return "sell"

        return None

    def get_stop_loss(self, candles: list[dict], signal: str, entry_price: float) -> float:
        recent = candles[-5:]
        atr = _atr(candles)

        if signal == "buy":
            swing_low = min(c["low"] for c in recent)
            stop = swing_low - (atr * 0.5)
        else:
            swing_high = max(c["high"] for c in recent)
            stop = swing_high + (atr * 0.5)

        self.logger.info(f"🛑 Stop loss: {stop:.4f}")
        return round(stop, 4)