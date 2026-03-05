"""
strategy_factory.py
--------------------
Loads the active strategy from config.json.
To switch strategies, just change config.json → strategy → active.
No code changes needed.
"""

from utils.config_loader import get
from strategies.ema_crossover import EMACrossoverStrategy
from strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from strategies.opening_range_breakout import OpeningRangeBreakoutStrategy
from strategies.base_strategy import BaseStrategy


STRATEGY_MAP = {
    "ema_crossover": EMACrossoverStrategy,
    "rsi_mean_reversion": RSIMeanReversionStrategy,
    "opening_range_breakout": OpeningRangeBreakoutStrategy,
}


def load_strategy(symbol: str = None, timeframe: str = None) -> BaseStrategy:
    """
    Load the active strategy from config.json.

    Usage:
        strategy = load_strategy()
        signal = strategy.generate_signal(candles)
    """
    active = get("strategy.active")
    symbol = symbol or get("trading.pairs")[0]
    timeframe = timeframe or get("trading.timeframe")

    if active not in STRATEGY_MAP:
        available = list(STRATEGY_MAP.keys())
        raise ValueError(
            f"Strategy '{active}' not found. Available: {available}\n"
            f"Update config.json → strategy → active"
        )

    strategy_class = STRATEGY_MAP[active]
    return strategy_class(symbol=symbol, timeframe=timeframe)