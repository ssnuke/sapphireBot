"""
risk_manager.py
---------------
Enforces all risk rules defined in config.json.
Every trade MUST pass through can_trade() before execution.
"""

import logging
from datetime import datetime, date
from utils.config_loader import (
    get,
    get_risk_amount_inr,
    get_max_loss_day_inr,
    get_max_loss_week_inr,
    get_profit_target_inr,
    update_balance,
)

logger = logging.getLogger(__name__)


class RiskManager:
    def __init__(self):
        self.daily_pnl: float = 0.0
        self.weekly_pnl: float = 0.0
        self.trades_today: int = 0
        self.last_reset_date: date = datetime.now().date()
        self.balance: float = get("account.balance")
        self.balance_at_last_scale: float = self.balance

    # ─────────────────────────────────────────────
    # DAILY / WEEKLY RESET
    # ─────────────────────────────────────────────

    def _check_reset(self):
        today = datetime.now().date()
        if today != self.last_reset_date:
            logger.info(f"📅 New day. Resetting daily counters. Previous day PnL: ₹{self.daily_pnl:.2f}")
            self.daily_pnl = 0.0
            self.trades_today = 0
            self.last_reset_date = today

    # ─────────────────────────────────────────────
    # CIRCUIT BREAKER — MAIN GATE
    # ─────────────────────────────────────────────

    def can_trade(self) -> tuple[bool, str]:
        """
        Returns (True, "ok") if trading is allowed.
        Returns (False, reason) if any circuit breaker is triggered.
        Call this before every single trade.
        """
        self._check_reset()

        max_loss_day = get_max_loss_day_inr()
        max_loss_week = get_max_loss_week_inr()
        max_trades = get("risk.max_trades_per_day")

        if self.daily_pnl <= -max_loss_day:
            msg = f"🔴 Daily loss limit hit: ₹{abs(self.daily_pnl):.2f} / ₹{max_loss_day:.2f}"
            logger.warning(msg)
            return False, msg

        if self.weekly_pnl <= -max_loss_week:
            msg = f"🔴 Weekly loss limit hit: ₹{abs(self.weekly_pnl):.2f} / ₹{max_loss_week:.2f}"
            logger.warning(msg)
            return False, msg

        if self.trades_today >= max_trades:
            msg = f"🔴 Max trades reached: {self.trades_today}/{max_trades} today"
            logger.warning(msg)
            return False, msg

        return True, "ok"

    # ─────────────────────────────────────────────
    # POSITION SIZING
    # ─────────────────────────────────────────────

    def get_position_size(self, entry_price: float, stop_loss_price: float) -> dict:
        risk_inr = get_risk_amount_inr()
        usd_rate = get("account.usd_inr_rate")
        leverage = get("risk.leverage")
        rr_min = get("targets.rr_ratio_min")
        rr_max = get("targets.rr_ratio_max")

        risk_usd = risk_inr / usd_rate
        stop_dist_pct = abs(entry_price - stop_loss_price) / entry_price

        position_value_usd = risk_usd / stop_dist_pct
        quantity = position_value_usd / entry_price

        # ✅ FIXED: stop BELOW entry = long, stop ABOVE entry = short
        is_long = stop_loss_price < entry_price
        tp1_distance = stop_dist_pct * rr_min
        tp2_distance = stop_dist_pct * rr_max

        tp1_price = entry_price * (1 + tp1_distance) if is_long else entry_price * (1 - tp1_distance)
        tp2_price = entry_price * (1 + tp2_distance) if is_long else entry_price * (1 - tp2_distance)

        sizing = {
            "entry_price": entry_price,
            "stop_loss_price": stop_loss_price,
            "stop_dist_pct": round(stop_dist_pct * 100, 3),
            "quantity": round(quantity, 6),
            "position_value_usd": round(position_value_usd, 2),
            "position_value_inr": round(position_value_usd * usd_rate, 2),
            "risk_usd": round(risk_usd, 2),
            "risk_inr": risk_inr,
            "leverage_needed": round(position_value_usd / (risk_usd / stop_dist_pct * leverage), 2),
            "tp1_price": round(tp1_price, 4),
            "tp1_profit_inr": round(risk_inr * rr_min, 2),
            "tp2_price": round(tp2_price, 4),
            "tp2_profit_inr": round(risk_inr * rr_max, 2),
        }

        logger.info(f"📐 Position sized: {sizing}")
        return sizing

    # ─────────────────────────────────────────────
    # RECORD TRADE RESULT
    # ─────────────────────────────────────────────

    def record_trade(self, pnl_inr: float):
        """Call this after every trade closes with actual PnL."""
        self.daily_pnl += pnl_inr
        self.weekly_pnl += pnl_inr
        self.trades_today += 1
        self.balance += pnl_inr

        emoji = "✅" if pnl_inr >= 0 else "❌"
        logger.info(
            f"{emoji} Trade closed: ₹{pnl_inr:+.2f} | "
            f"Day P&L: ₹{self.daily_pnl:+.2f} | "
            f"Balance: ₹{self.balance:.2f} | "
            f"Trades today: {self.trades_today}"
        )

        self._check_scaling()

    # ─────────────────────────────────────────────
    # AUTO SCALING
    # ─────────────────────────────────────────────

    def _check_scaling(self):
        """
        Auto-scale risk when balance grows by scaling_trigger_pct.
        Updates config.json so risk_per_trade recalculates automatically.
        """
        trigger_pct = get("scaling.trigger_pct") / 100
        growth = (self.balance - self.balance_at_last_scale) / self.balance_at_last_scale

        if growth >= trigger_pct:
            old_risk = get_risk_amount_inr()
            update_balance(round(self.balance, 2))
            new_risk = get_risk_amount_inr()
            self.balance_at_last_scale = self.balance

            logger.info(
                f"📈 SCALING TRIGGERED! Balance: ₹{self.balance:.2f} | "
                f"Risk/trade: ₹{old_risk} → ₹{new_risk}"
            )

    # ─────────────────────────────────────────────
    # DAILY SUMMARY
    # ─────────────────────────────────────────────

    def get_daily_summary(self) -> dict:
        return {
            "date": str(self.last_reset_date),
            "trades_today": self.trades_today,
            "daily_pnl_inr": round(self.daily_pnl, 2),
            "weekly_pnl_inr": round(self.weekly_pnl, 2),
            "current_balance": round(self.balance, 2),
            "max_loss_day_remaining": round(get_max_loss_day_inr() + self.daily_pnl, 2),
            "trades_remaining": get("risk.max_trades_per_day") - self.trades_today,
        }