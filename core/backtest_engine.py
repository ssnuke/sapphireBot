"""
backtest_engine.py
------------------
Core backtesting engine that simulates trading strategies on historical data.

Workflow:
1. Load historical data
2. Iterate through candles (simulating time progression)
3. Generate signals from strategy
4. Simulate trade execution
5. Track positions and P&L
6. Generate performance report
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from core.data_fetcher import DataFetcher
from core.position_tracker import PositionTracker
from core.risk_manager import RiskManager
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for backtest run."""
    
    # Data parameters
    symbol: str
    timeframe: str
    days: int = 90
    
    # Strategy
    strategy: BaseStrategy = None
    
    # Risk parameters
    initial_balance: float = 10000.0
    risk_per_trade_pct: float = 0.25
    max_loss_day_pct: float = 3.0
    max_trades_per_day: int = 5
    leverage: int = 5
    
    # Execution
    slippage_pct: float = 0.05  # 0.05% slippage
    commission_pct: float = 0.04  # 0.04% taker fee
    
    # Tracking
    track_drawdown: bool = True
    track_daily_stats: bool = True


@dataclass
class BacktestResult:
    """Results from a backtest run."""
    
    # Strategy info
    strategy_name: str
    symbol: str
    timeframe: str
    
    # Date range
    start_date: str
    end_date: str
    total_candles: int
    
    # Performance
    initial_balance: float
    final_balance: float
    total_return_pct: float
    total_return_inr: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate_pct: float
    
    # P&L statistics
    gross_profit: float
    gross_loss: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    avg_rr_ratio: float
    largest_win: float
    largest_loss: float
    
    # Risk metrics
    max_drawdown_pct: float
    max_drawdown_inr: float
    sharpe_ratio: float
    
    # Trade details
    all_trades: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    daily_stats: List[Dict] = field(default_factory=list)


class BacktestEngine:
    """
    Backtesting engine for strategy validation.
    
    Usage:
        config = BacktestConfig(
            symbol="BTC/USDT",
            timeframe="15m",
            days=90,
            strategy=strategy_instance
        )
        
        engine = BacktestEngine(config)
        result = engine.run()
        result.print_summary()
    """
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.balance = config.initial_balance
        self.peak_balance = config.initial_balance
        self.max_drawdown = 0.0
        
        # Initialize components
        self.data_fetcher = DataFetcher()
        self.position_tracker = PositionTracker()
        
        # Initialize risk manager with custom config
        self.risk_manager = RiskManager()
        self.risk_manager.balance = config.initial_balance
        
        # Tracking
        self.equity_curve = []
        self.daily_stats = []
        self.current_date = None
        self.trades_today = 0
        self.daily_pnl = 0.0
        
        logger.info(f"🔬 Backtest Engine initialized for {config.symbol} on {config.timeframe}")
    
    def run(self) -> BacktestResult:
        """
        Execute the backtest.
        
        Returns:
            BacktestResult with all performance metrics
        """
        logger.info("=" * 80)
        logger.info(f"🚀 STARTING BACKTEST: {self.config.strategy.get_name().upper()}")
        logger.info(f"   Symbol:      {self.config.symbol}")
        logger.info(f"   Timeframe:   {self.config.timeframe}")
        logger.info(f"   Period:      {self.config.days} days")
        logger.info(f"   Balance:     ₹{self.config.initial_balance:,.2f}")
        logger.info("=" * 80)
        
        # 1. Fetch historical data
        candles = self.data_fetcher.fetch_historical(
            symbol=self.config.symbol,
            timeframe=self.config.timeframe,
            days=self.config.days
        )
        
        if not candles or len(candles) < 100:
            raise ValueError(f"Insufficient data: got {len(candles)} candles, need at least 100")
        
        # 2. Run simulation
        start_time = datetime.now()
        self._simulate(candles)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # 3. Close any remaining positions
        if self.position_tracker.open_positions:
            last_candle = candles[-1]
            self.position_tracker.close_all_positions(
                current_price=last_candle["close"],
                timestamp=last_candle["timestamp"],
                reason="backtest_end"
            )
        
        # 4. Generate results
        result = self._calculate_results(candles)
        
        logger.info("=" * 80)
        logger.info(f"✅ BACKTEST COMPLETED in {elapsed:.2f}s")
        logger.info(f"   Total Trades:    {result.total_trades}")
        logger.info(f"   Final Balance:   ₹{result.final_balance:,.2f}")
        logger.info(f"   Total Return:    {result.total_return_pct:+.2f}%")
        logger.info(f"   Win Rate:        {result.win_rate_pct:.1f}%")
        logger.info(f"   Max Drawdown:    {result.max_drawdown_pct:.2f}%")
        logger.info("=" * 80)
        
        return result
    
    def _simulate(self, candles: List[Dict]):
        """Main simulation loop."""
        min_candles = 50  # Minimum candles needed for indicators
        
        for i in range(min_candles, len(candles)):
            current_candle = candles[i]
            historical_candles = candles[:i]  # All candles up to current
            entry_price = current_candle["close"] 
            
            # Track date changes for daily resets
            current_date = current_candle["timestamp"][:10]  # YYYY-MM-DD
            if current_date != self.current_date:
                self._reset_daily_counters()
                self.current_date = current_date
            
            # Update open positions (check SL/TP)
            closed_trades = self.position_tracker.update_all_positions(
                current_candle, self.config.symbol
            )
            
            # Update balance from closed trades
            for trade in closed_trades:
                pnl = trade["realized_pnl_inr"]
                self.balance += pnl
                self.daily_pnl += pnl
                self.trades_today += 1
                
                # Track drawdown
                if self.balance > self.peak_balance:
                    self.peak_balance = self.balance
                
                current_dd = ((self.peak_balance - self.balance) / self.peak_balance) * 100
                if current_dd > self.max_drawdown:
                    self.max_drawdown = current_dd
            
            # Check if we can trade
            can_trade = (
                self.trades_today < self.config.max_trades_per_day and
                len(self.position_tracker.open_positions) < 2 and
                self.daily_pnl > -self.balance * (self.config.max_loss_day_pct / 100)
            )
            
            if not can_trade:
                continue
            
            # Generate signal
            signal = self.config.strategy.generate_signal(historical_candles)
            
            if signal:
                # Calculate position sizing
                entry_price = current_candle["close"]
                stop_loss = self.config.strategy.get_stop_loss(
                    historical_candles, signal, entry_price
                )
                
                # Apply slippage
                entry_price = self._apply_slippage(entry_price, signal)
                
                # Get position size
                sizing = self.risk_manager.get_position_size(entry_price, stop_loss)
                
                # Apply commission
                commission = sizing["position_value_usd"] * (self.config.commission_pct / 100) * 84
                self.balance -= commission
                
                # Open position
                self.position_tracker.open_position(
                    symbol=self.config.symbol,
                    strategy=self.config.strategy.get_name(),
                    signal=signal,
                    entry_price=entry_price,
                    entry_time=current_candle["timestamp"],
                    sizing=sizing
                )
            
            # Record equity curve
            self.equity_curve.append({
                "timestamp": current_candle["timestamp"],
                "balance": round(self.balance, 2),
                "unrealized_pnl": round(self.position_tracker.get_total_unrealized_pnl(), 2),
                "open_positions": len(self.position_tracker.open_positions)
            })
    
    def _apply_slippage(self, price: float, signal: str) -> float:
        """Simulate slippage on entry."""
        slippage = price * (self.config.slippage_pct / 100)
        if signal == "buy":
            return price + slippage  # Buy at slightly higher price
        else:
            return price - slippage  # Sell at slightly lower price
    
    def _reset_daily_counters(self):
        """Reset daily tracking variables."""
        if self.current_date:
            self.daily_stats.append({
                "date": self.current_date,
                "trades": self.trades_today,
                "pnl": round(self.daily_pnl, 2),
                "balance": round(self.balance, 2)
            })
        
        self.trades_today = 0
        self.daily_pnl = 0.0
    
    def _calculate_results(self, candles: List[Dict]) -> BacktestResult:
        """Calculate all performance metrics."""
        closed = self.position_tracker.closed_positions
        
        if not closed:
            # No trades executed
            return BacktestResult(
                strategy_name=self.config.strategy.get_name(),
                symbol=self.config.symbol,
                timeframe=self.config.timeframe,
                start_date=candles[0]["timestamp"],
                end_date=candles[-1]["timestamp"],
                total_candles=len(candles),
                initial_balance=self.config.initial_balance,
                final_balance=self.balance,
                total_return_pct=0.0,
                total_return_inr=0.0,
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate_pct=0.0,
                gross_profit=0.0,
                gross_loss=0.0,
                profit_factor=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                avg_rr_ratio=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                max_drawdown_pct=0.0,
                max_drawdown_inr=0.0,
                sharpe_ratio=0.0,
                all_trades=[],
                equity_curve=self.equity_curve,
                daily_stats=self.daily_stats
            )
        
        # Trade statistics
        winning = [p for p in closed if p.realized_pnl_inr > 0]
        losing = [p for p in closed if p.realized_pnl_inr <= 0]
        
        gross_profit = sum(p.realized_pnl_inr for p in winning)
        gross_loss = abs(sum(p.realized_pnl_inr for p in losing))
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_win = gross_profit / len(winning) if winning else 0
        avg_loss = gross_loss / len(losing) if losing else 0
        avg_rr = avg_win / avg_loss if avg_loss > 0 else 0
        
        # Calculate Sharpe ratio from daily returns
        if len(self.daily_stats) > 1:
            daily_returns = [
                (self.daily_stats[i]["balance"] - self.daily_stats[i-1]["balance"]) / 
                self.daily_stats[i-1]["balance"] * 100
                for i in range(1, len(self.daily_stats))
            ]
            
            avg_return = sum(daily_returns) / len(daily_returns)
            std_return = (sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
            sharpe = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0  # Annualized
        else:
            sharpe = 0.0
        
        return BacktestResult(
            strategy_name=self.config.strategy.get_name(),
            symbol=self.config.symbol,
            timeframe=self.config.timeframe,
            start_date=candles[0]["timestamp"],
            end_date=candles[-1]["timestamp"],
            total_candles=len(candles),
            initial_balance=self.config.initial_balance,
            final_balance=self.balance,
            total_return_pct=((self.balance - self.config.initial_balance) / self.config.initial_balance) * 100,
            total_return_inr=self.balance - self.config.initial_balance,
            total_trades=len(closed),
            winning_trades=len(winning),
            losing_trades=len(losing),
            win_rate_pct=(len(winning) / len(closed)) * 100,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_rr_ratio=avg_rr,
            largest_win=max((p.realized_pnl_inr for p in winning), default=0),
            largest_loss=min((p.realized_pnl_inr for p in losing), default=0),
            max_drawdown_pct=self.max_drawdown,
            max_drawdown_inr=(self.peak_balance - (self.peak_balance * (1 - self.max_drawdown/100))),
            sharpe_ratio=sharpe,
            all_trades=[p.to_dict() for p in closed],
            equity_curve=self.equity_curve,
            daily_stats=self.daily_stats
        )
