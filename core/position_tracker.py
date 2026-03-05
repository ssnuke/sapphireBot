"""
position_tracker.py
-------------------
Tracks open positions and manages trade lifecycle.

For both live trading and backtesting:
- Monitors stop loss and take profit levels
- Calculates unrealized P&L
- Handles partial exits
- Records trade history
"""

import logging
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open trading position."""
    
    # Trade identifiers
    trade_id: str
    symbol: str
    strategy: str
    signal: str  # "buy" or "sell"
    
    # Entry details
    entry_price: float
    entry_time: str
    quantity: float
    
    # Risk management
    stop_loss_price: float
    take_profit_1: float
    take_profit_2: float
    
    # Position sizing
    position_value_usd: float
    risk_amount_inr: float
    leverage: int
    
    # Status tracking
    status: str = "open"  # "open", "partial_exit", "closed"
    quantity_remaining: float = field(init=False)
    
    # Exit details (populated on close)
    exit_price: Optional[float] = None
    exit_time: Optional[str] = None
    exit_reason: Optional[str] = None
    
    # Performance
    realized_pnl_inr: float = 0.0
    unrealized_pnl_inr: float = 0.0
    
    def __post_init__(self):
        self.quantity_remaining = self.quantity
    
    def update_unrealized_pnl(self, current_price: float, usd_inr_rate: float = 84.0):
        """Calculate unrealized P&L based on current price."""
        if self.signal == "buy":
            price_diff = current_price - self.entry_price
        else:  # sell (short)
            price_diff = self.entry_price - current_price
        
        pnl_usd = (price_diff / self.entry_price) * self.position_value_usd
        self.unrealized_pnl_inr = pnl_usd * usd_inr_rate
        return self.unrealized_pnl_inr
    
    def check_exit_conditions(self, current_candle: Dict) -> Optional[str]:
        """
        Check if position should be closed based on price action.
        
        Returns:
            "stop_loss", "take_profit_1", "take_profit_2", or None
        """
        high = current_candle["high"]
        low = current_candle["low"]
        
        if self.signal == "buy":
            # Long position
            if low <= self.stop_loss_price:
                return "stop_loss"
            elif high >= self.take_profit_2:
                return "take_profit_2"
            elif high >= self.take_profit_1:
                return "take_profit_1"
        else:
            # Short position
            if high >= self.stop_loss_price:
                return "stop_loss"
            elif low <= self.take_profit_2:
                return "take_profit_2"
            elif low <= self.take_profit_1:
                return "take_profit_1"
        
        return None
    
    def close_position(
        self,
        exit_price: float,
        exit_time: str,
        exit_reason: str,
        percentage: float = 1.0,
        usd_inr_rate: float = 84.0
    ):
        """
        Close position (fully or partially).
        
        Args:
            exit_price: Price at which position is closed
            exit_time: Timestamp of exit
            exit_reason: Reason for exit ("stop_loss", "take_profit_1", etc.)
            percentage: Percentage of position to close (0.5 = 50%)
            usd_inr_rate: USD to INR conversion rate
        """
        quantity_to_close = self.quantity_remaining * percentage
        
        # Calculate P&L for this exit
        if self.signal == "buy":
            price_diff = exit_price - self.entry_price
        else:
            price_diff = self.entry_price - exit_price
        
        pnl_usd = (price_diff / self.entry_price) * self.position_value_usd * percentage
        pnl_inr = pnl_usd * usd_inr_rate
        
        self.realized_pnl_inr += pnl_inr
        self.quantity_remaining -= quantity_to_close
        
        # Update status
        if self.quantity_remaining <= 0.0001:  # Fully closed
            self.status = "closed"
            self.exit_price = exit_price
            self.exit_time = exit_time
            self.exit_reason = exit_reason
            self.unrealized_pnl_inr = 0.0
        else:  # Partial exit
            self.status = "partial_exit"
        
        return pnl_inr
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary for logging."""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "strategy": self.strategy,
            "signal": self.signal,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time,
            "exit_price": self.exit_price,
            "exit_time": self.exit_time,
            "exit_reason": self.exit_reason,
            "quantity": self.quantity,
            "stop_loss": self.stop_loss_price,
            "take_profit_1": self.take_profit_1,
            "realized_pnl_inr": round(self.realized_pnl_inr, 2),
            "status": self.status
        }


class PositionTracker:
    """
    Manages all open positions and trade history.
    Monitors stop loss / take profit conditions.
    """
    
    def __init__(self, usd_inr_rate: float = 84.0, persistence_path: str = "data/open_positions.json"):
        self.open_positions: List[Position] = []
        self.closed_positions: List[Position] = []
        self.trade_counter = 0
        self.usd_inr_rate = usd_inr_rate
        self.persistence_path = persistence_path
        # try to load previous state if available
        self.load_state()
        
    def open_position(
        self,
        symbol: str,
        strategy: str,
        signal: str,
        entry_price: float,
        entry_time: str,
        sizing: Dict
    ) -> Position:
        """
        Open a new position and add to tracking.
        
        Args:
            symbol: Trading pair
            strategy: Strategy name
            signal: "buy" or "sell"
            entry_price: Entry price
            entry_time: Timestamp
            sizing: Position sizing dict from RiskManager.get_position_size()
        """
        self.trade_counter += 1
        
        position = Position(
            trade_id=f"{symbol}_{self.trade_counter}",
            symbol=symbol,
            strategy=strategy,
            signal=signal,
            entry_price=entry_price,
            entry_time=entry_time,
            quantity=sizing["quantity"],
            stop_loss_price=sizing["stop_loss_price"],
            take_profit_1=sizing["tp1_price"],
            take_profit_2=sizing["tp2_price"],
            position_value_usd=sizing["position_value_usd"],
            risk_amount_inr=sizing["risk_inr"],
            leverage=sizing.get("leverage_needed", 5),
        )
        
        self.open_positions.append(position)
        self.save_state()
        
        direction = "LONG" if signal == "buy" else "SHORT"
        logger.info(
            f"📈 Position Opened | {position.trade_id} | {direction} | "
            f"Entry: {entry_price:.4f} | SL: {position.stop_loss_price:.4f} | "
            f"TP1: {position.take_profit_1:.4f} | TP2: {position.take_profit_2:.4f}"
        )
        
        return position
    
    def update_all_positions(self, current_candle: Dict, symbol: str) -> List[Dict]:
        """
        Update all open positions for a given symbol.
        Check exit conditions and close if needed.
        
        Returns:
            List of closed position dicts (for logging)
        """
        closed_trades = []
        positions_to_remove = []
        
        current_price = current_candle["close"]
        timestamp = current_candle.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        for position in self.open_positions:
            if position.symbol != symbol:
                continue
            
            # Update unrealized P&L
            position.update_unrealized_pnl(current_price, self.usd_inr_rate)
            
            # Check exit conditions
            exit_reason = position.check_exit_conditions(current_candle)
            
            if exit_reason:
                # Determine exit price based on reason
                if exit_reason == "stop_loss":
                    exit_price = position.stop_loss_price
                    percentage = 1.0  # Close full position on SL
                elif exit_reason == "take_profit_1":
                    exit_price = position.take_profit_1
                    percentage = 0.5  # Close 50% at TP1
                elif exit_reason == "take_profit_2":
                    exit_price = position.take_profit_2
                    percentage = 1.0  # Close remaining at TP2
                else:
                    exit_price = current_price
                    percentage = 1.0
                
                # Close position
                pnl = position.close_position(
                    exit_price=exit_price,
                    exit_time=timestamp,
                    exit_reason=exit_reason,
                    percentage=percentage,
                    usd_inr_rate=self.usd_inr_rate
                )
                
                emoji = "✅" if pnl >= 0 else "❌"
                logger.info(
                    f"{emoji} Position Closed | {position.trade_id} | "
                    f"Exit: {exit_price:.4f} | Reason: {exit_reason} | "
                    f"P&L: ₹{pnl:+.2f} ({percentage*100:.0f}% closed)"
                )
                
                # If fully closed, move to closed positions
                if position.status == "closed":
                    closed_trades.append(position.to_dict())
                    positions_to_remove.append(position)
        
        # Remove fully closed positions
        for position in positions_to_remove:
            self.open_positions.remove(position)
            self.closed_positions.append(position)
        if positions_to_remove:
            self.save_state()
        
        return closed_trades
    
    def save_state(self):
        """Persist open positions and trade counter to disk."""
        try:
            data = {
                "trade_counter": self.trade_counter,
                "open_positions": [p.to_dict() for p in self.open_positions],
            }
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            with open(self.persistence_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.open_positions)} open positions to {self.persistence_path}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)

    def load_state(self):
        """Load persisted state if file exists."""
        if not os.path.exists(self.persistence_path):
            return
        try:
            with open(self.persistence_path, "r") as f:
                data = json.load(f)
            self.trade_counter = data.get("trade_counter", 0)
            for pos in data.get("open_positions", []):
                position = Position(
                    trade_id=pos["trade_id"],
                    symbol=pos["symbol"],
                    strategy=pos["strategy"],
                    signal=pos["signal"],
                    entry_price=pos["entry_price"],
                    entry_time=pos.get("entry_time", ""),
                    quantity=pos.get("quantity", 0),
                    stop_loss_price=pos.get("stop_loss", 0),
                    take_profit_1=pos.get("take_profit_1", 0),
                    take_profit_2=pos.get("take_profit", 0),
                    position_value_usd=pos.get("position_value_usd", 0),
                    risk_amount_inr=pos.get("pnl_inr", 0),
                    leverage=pos.get("leverage", 0),
                )
                # set status/unrealized if present
                position.status = pos.get("status", "open")
                self.open_positions.append(position)
            logger.info(f"Loaded {len(self.open_positions)} open positions from disk")
        except Exception as e:
            logger.error(f"Failed to load state: {e}", exc_info=True)

    def get_open_positions_summary(self) -> List[Dict]:
        """Get summary of all open positions."""
        return [
            {
                "trade_id": p.trade_id,
                "symbol": p.symbol,
                "signal": p.signal,
                "entry_price": p.entry_price,
                "current_pnl_inr": round(p.unrealized_pnl_inr, 2),
                "status": p.status,
                "entry_time": p.entry_time
            }
            for p in self.open_positions
        ]
    
    def get_total_unrealized_pnl(self) -> float:
        """Calculate total unrealized P&L across all open positions."""
        return sum(p.unrealized_pnl_inr for p in self.open_positions)
    
    def get_position_count(self) -> Dict[str, int]:
        """Get count of positions by status."""
        return {
            "open": len(self.open_positions),
            "closed": len(self.closed_positions),
            "total": len(self.open_positions) + len(self.closed_positions)
        }
    
    def close_all_positions(self, current_price: float, timestamp: str, reason: str = "forced"):
        """Force close all open positions (e.g., end of backtest)."""
        for position in self.open_positions[:]:  # Copy list to avoid modification during iteration
            position.close_position(
                exit_price=current_price,
                exit_time=timestamp,
                exit_reason=reason,
                percentage=1.0,
                usd_inr_rate=self.usd_inr_rate
            )
            self.closed_positions.append(position)
        
        self.open_positions.clear()
        logger.info(f"⚠️ Force closed all positions. Reason: {reason}")
