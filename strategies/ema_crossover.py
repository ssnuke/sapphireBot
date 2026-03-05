"""
ema_crossover.py
"""

import logging
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


def _ema(values: list[float], period: int) -> list[float]:
    k = 2 / (period + 1)
    ema = [values[0]]
    for price in values[1:]:
        ema.append(price * k + ema[-1] * (1 - k))
    return ema


def _atr(candles: list[dict], period: int = 14) -> float:
    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i - 1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)
    return sum(true_ranges[-period:]) / period


def _rsi(closes: list[float], period: int = 14) -> float:
    """RSI to avoid entering overbought/oversold exhausted moves."""
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i+1] - closes[i] for i in range(len(closes)-1)]
    gains = [d for d in deltas[-period:] if d > 0]
    losses = [abs(d) for d in deltas[-period:] if d < 0]
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))

def _is_trend_aligned(candles: list[dict], signal: str, fast: int = 9, slow: int = 21) -> bool:
    """Aggregate 15m candles into 1H and check EMA trend direction."""
    hourly_closes = []
    for i in range(0, len(candles) - 4, 4):
        group = candles[i:i+4]
        hourly_closes.append(group[-1]["close"])

    if len(hourly_closes) < slow + 2:
        return False

    ema_fast = _ema(hourly_closes, fast)
    ema_slow = _ema(hourly_closes, slow)

    if signal == "buy":
        return ema_fast[-2] > ema_slow[-2]
    else:
        return ema_fast[-2] < ema_slow[-2]


def _confirm_candle(candles: list[dict], signal: str) -> bool:
    """
    Wait for the candle AFTER the crossover to confirm direction.
    Avoids entering on fakeout crossovers that immediately reverse.
    
    For buys:  confirmation candle must close higher than it opened (green)
    For sells: confirmation candle must close lower than it opened (red)
    """
    confirm = candles[-2]  # last closed candle (the one after the crossover)
    
    if signal == "buy":
        return confirm["close"] > confirm["open"]  # green candle
    else:
        return confirm["close"] < confirm["open"]  # red candle


class EMACrossoverStrategy(BaseStrategy):

    def __init__(self, symbol: str, timeframe: str, fast: int = 9, slow: int = 21):
        super().__init__(symbol, timeframe)
        self.fast = fast
        self.slow = slow
        self.volume_multiplier = 1.8
        self.atr_multiplier = 2.2

    def get_name(self) -> str:
        return "ema_crossover"

    def generate_signal(self, candles: list[dict]) -> str | None:
        if not self.validate_candles(candles, min_required=self.slow + 5):
            return None

        closes = [c["close"] for c in candles]
        volumes = [c["volume"] for c in candles]

        ema_fast = _ema(closes, self.fast)
        ema_slow = _ema(closes, self.slow)

        curr_fast, curr_slow = ema_fast[-2], ema_slow[-2]
        prev_fast, prev_slow = ema_fast[-3], ema_slow[-3]

        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-2]
        volume_ok = current_volume > avg_volume * self.volume_multiplier

        bullish_cross = prev_fast <= prev_slow and curr_fast > curr_slow
        bearish_cross = prev_fast >= prev_slow and curr_fast < curr_slow

        rsi = _rsi(closes[:-1])
        rsi_ok_buy  = 45 <= rsi <= 65
        rsi_ok_sell = 35 <= rsi <= 55

        if bullish_cross and volume_ok and rsi_ok_buy:
            if not _is_trend_aligned(candles, "buy", self.fast, self.slow):
                self.logger.debug("⏭️ BUY skipped — HTF not aligned")
                return None
            if not _confirm_candle(candles, "buy"):          # ← NEW
                self.logger.debug("⏭️ BUY skipped — confirmation candle bearish")
                return None
            self.logger.info(
                f"📗 BUY | EMA{self.fast}={curr_fast:.2f} > EMA{self.slow}={curr_slow:.2f} "
                f"| RSI={rsi:.1f} | HTF ✅ | Candle confirmed ✅"
            )
            return "buy"

        if bearish_cross and volume_ok and rsi_ok_sell:
            if not _is_trend_aligned(candles, "sell", self.fast, self.slow):
                self.logger.debug("⏭️ SELL skipped — HTF not aligned")
                return None
            if not _confirm_candle(candles, "sell"):         # ← NEW
                self.logger.debug("⏭️ SELL skipped — confirmation candle bullish")
                return None
            self.logger.info(
                f"📕 SELL | EMA{self.fast}={curr_fast:.2f} < EMA{self.slow}={curr_slow:.2f} "
                f"| RSI={rsi:.1f} | HTF ✅ | Candle confirmed ✅"
            )
            return "sell"

        return None

    def get_stop_loss(self, candles: list[dict], signal: str, entry_price: float) -> float:
        atr = _atr(candles)
        buffer = atr * self.atr_multiplier

        stop = entry_price - buffer if signal == "buy" else entry_price + buffer
        self.logger.info(f"🛑 Stop loss: {stop:.4f} (ATR={atr:.4f}, buffer={buffer:.4f})")
        return round(stop, 4)