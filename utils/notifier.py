"""
notifier.py
-----------
Sends Telegram messages for trade alerts and hourly summaries.
Supports both Telegram bot API and optional Relegram webhook.

Config-driven: telegram_enabled, bot token, chat ID, and webhook
all come from config.json.
"""

import logging
import requests
from datetime import datetime
from utils.config_loader import get

logger = logging.getLogger(__name__)


class Notifier:
    def __init__(self):
        self.enabled = get("notifications.telegram_enabled", False)
        self.bot_token = get("notifications.telegram_bot_token", "")
        self.chat_id = get("notifications.telegram_chat_id", "")
        self.webhook_url = get("notifications.relegram_webhook", "")
        self.telegram_api = "https://api.telegram.org/bot"

    def send_message(self, text: str) -> bool:
        """Send a message via Telegram bot or webhook."""
        if not self.enabled:
            return False

        success = False
        if self.bot_token and self.chat_id:
            success |= self._send_telegram(text)
        if self.webhook_url:
            success |= self._send_webhook(text)
        return success

    def _send_telegram(self, text: str) -> bool:
        try:
            url = f"{self.telegram_api}{self.bot_token}/sendMessage"
            data = {"chat_id": self.chat_id, "text": text, "parse_mode": "HTML"}
            r = requests.post(url, data=data, timeout=10)
            if r.status_code == 200:
                logger.debug("Telegram notification sent")
                return True
            else:
                logger.warning(f"Telegram error: {r.status_code} {r.text}")
                return False
        except Exception as e:
            logger.warning(f"Failed to send Telegram message: {e}")
            return False

    def _send_webhook(self, text: str) -> bool:
        try:
            data = {"text": text}
            r = requests.post(self.webhook_url, json=data, timeout=10)
            if r.status_code >= 200 and r.status_code < 300:
                logger.debug("Webhook notification sent")
                return True
            else:
                logger.warning(f"Webhook error: {r.status_code} {r.text}")
                return False
        except Exception as e:
            logger.warning(f"Failed to send webhook message: {e}")
            return False

    def notify_trade_open(
        self, symbol: str, signal: str, entry_price: float, stop_loss: float, sizing: dict
    ) -> bool:
        if not get("notifications.notify_on_trade_open", True):
            return False
        direction = "LONG" if signal == "buy" else "SHORT"
        text = (
            f"<b>📈 Trade Opened</b>\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Direction:</b> {direction}\n"
            f"<b>Entry:</b> ${entry_price:.4f}\n"
            f"<b>Stop Loss:</b> ${stop_loss:.4f}\n"
            f"<b>Risk:</b> ₹{sizing.get('risk_inr', 0):.2f}\n"
            f"<b>TP1:</b> ${sizing.get('tp1_price', 0):.4f}\n"
            f"<b>TP2:</b> ${sizing.get('tp2_price', 0):.4f}"
        )
        return self.send_message(text)

    def notify_trade_close(
        self, symbol: str, exit_reason: str, exit_price: float, pnl_inr: float
    ) -> bool:
        if not get("notifications.notify_on_trade_close", True):
            return False
        emoji = "✅" if pnl_inr >= 0 else "❌"
        text = (
            f"{emoji} <b>Trade Closed</b>\n"
            f"<b>Symbol:</b> {symbol}\n"
            f"<b>Exit Reason:</b> {exit_reason}\n"
            f"<b>Exit Price:</b> ${exit_price:.4f}\n"
            f"<b>P&L:</b> ₹{pnl_inr:+.2f}"
        )
        return self.send_message(text)

    def notify_circuit_breaker(self, reason: str) -> bool:
        if not get("notifications.notify_on_circuit_breaker", True):
            return False
        text = f"<b>⛔ Circuit Breaker</b>\n{reason}"
        return self.send_message(text)

    def notify_daily_summary(self, summary: dict) -> bool:
        if not get("notifications.notify_on_daily_summary", True):
            return False
        text = (
            f"<b>📊 Daily Summary</b>\n"
            f"<b>Date:</b> {summary.get('date', '')}\n"
            f"<b>Trades:</b> {summary.get('trades_today', 0)}\n"
            f"<b>P&L:</b> ₹{summary.get('daily_pnl_inr', 0):+.2f}\n"
            f"<b>Balance:</b> ₹{summary.get('current_balance', 0):.2f}\n"
            f"<b>Max Loss Remaining:</b> ₹{summary.get('max_loss_day_remaining', 0):.2f}"
        )
        return self.send_message(text)

    def notify_hourly_summary(self, summary: dict, open_positions: list) -> bool:
        if not get("notifications.notify_hourly_update", False):
            return False
        unrealized_pnl = summary.get("unrealized_pnl_inr", 0)
        emoji = "📈" if unrealized_pnl >= 0 else "📉"
        text = (
            f"{emoji} <b>Hourly Update</b>\n"
            f"<b>Time:</b> {datetime.now().strftime('%H:%M UTC')}\n"
            f"<b>Balance:</b> ₹{summary.get('current_balance', 0):.2f}\n"
            f"<b>Daily P&L:</b> ₹{summary.get('daily_pnl_inr', 0):+.2f}\n"
            f"<b>Open Positions:</b> {len(open_positions)}\n"
            f"<b>Unrealized P&L:</b> ₹{unrealized_pnl:+.2f}"
        )
        return self.send_message(text)
