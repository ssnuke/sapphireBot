"""
order_manager.py
----------------
Handles live order placement via CCXT, tracks pending orders,
applies slippage buffers, and provides simple retry logic for
network/API errors.

Assumptions:
  * Exchange object passed from main already initialized with
    API credentials.
  * Orders should be sized/validated by RiskManager before calling.
  * We will only trade USDT‑margined perpetuals (linear futures).
  * Leverage is set in exchange via params when creating orders.
  * Persistence of open positions is handled by PositionTracker; the
    OrderManager only needs to update the tracker once a fill occurs.

The manager exposes:
  - execute_trade(...)
  - cancel_order(order_id)
  - fetch_balance()
  - safe_fetch_candles(...) [optional wrap]

The retry logic uses exponential backoff on network/ExchangeErrors.
"""

import logging
import time
from typing import Optional
import ccxt

logger = logging.getLogger(__name__)


class OrderManager:
    def __init__(self, exchange: ccxt.Exchange, max_retries: int = 5, backoff_base: float = 2.0):
        self.exchange = exchange
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    def _retry(self, func, *args, **kwargs):
        """Generic retry wrapper for exchange calls."""
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                wait = self.backoff_base ** attempt
                logger.warning(f"Exchange error ({e}) on attempt {attempt}/{self.max_retries}, retrying in {wait}s...")
                time.sleep(wait)
            except Exception:
                logger.error("Uncaught exception in order manager", exc_info=True)
                raise
        raise RuntimeError("Max retries exceeded for exchange call")

    def _adjust_price(self, price: float, side: str) -> float:
        from utils.config_loader import get
        slippage = get("trading.slippage_buffer_pct") / 100
        if side == "buy":
            return price * (1 + slippage)
        else:
            return price * (1 - slippage)

    def fetch_balance(self) -> dict:
        """Fetch account balance from exchange with retries."""
        return self._retry(self.exchange.fetch_balance)

    def fetch_order(self, order_id: str, symbol: str) -> dict:
        return self._retry(self.exchange.fetch_order, order_id, symbol)

    def cancel_order(self, order_id: str, symbol: str) -> dict:
        return self._retry(self.exchange.cancel_order, order_id, symbol)

    def execute_trade(
        self,
        signal: str,
        sizing: dict,
        symbol: str,
        strategy: str,
        position_tracker,
    ):
        """Place a live order and add position to tracker once filled.

        Returns the new Position object.
        """
        side = "buy" if signal == "buy" else "sell"
        amount = sizing["quantity"]
        price = sizing["entry_price"]
        price = self._adjust_price(price, side)

        # Import inline to avoid circular dependency
        from utils.config_loader import get
        
        order_type = get("trading.order_type")
        params = {"leverage": get("risk.leverage")}

        try:
            order = self._retry(
                self.exchange.create_order,
                symbol,
                order_type,
                side,
                amount,
                price if order_type == "limit" else None,
                params,
            )
        except Exception as e:
            logger.error(f"Order placement failed: {e}", exc_info=True)
            raise

        logger.info(f"🛒 Order placed {order_type} {side} {amount}@{price} ({symbol})")

        # wait for fill or poll until status is closed/filled
        filled = False
        for i in range(self.max_retries * 2):
            time.sleep(1)
            order = self.fetch_order(order["id"], symbol)
            status = order.get("status")
            if status in ["closed", "canceled", "filled"]:
                filled = True
                break
        if not filled:
            logger.warning("Order did not fill within timeout period")

        entry_price = float(order.get("average") or order.get("price") or price)
        position = position_tracker.open_position(
            symbol=symbol,
            strategy=strategy,
            signal=signal,
            entry_price=entry_price,
            entry_time=order.get("datetime", ""),
            sizing=sizing,
        )
        return position
