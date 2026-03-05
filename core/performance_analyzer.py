"""
performance_analyzer.py
-----------------------
Analyzes backtest results and generates visual reports.
Creates professional charts for strategy performance evaluation.

Charts generated:
1. Equity curve (balance over time)
2. Drawdown chart
3. Trade distribution (wins/losses)
4. Monthly returns heatmap
5. Performance metrics dashboard
"""

import os
import logging
from typing import Dict, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Try importing matplotlib, provide fallback if not installed
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("⚠️ Matplotlib not installed. Install with: pip install matplotlib")


class PerformanceAnalyzer:
    """
    Analyzes and visualizes backtest performance.
    
    Usage:
        analyzer = PerformanceAnalyzer(backtest_result)
        analyzer.generate_report(output_dir="results/")
        analyzer.plot_all_charts(output_dir="results/")
    """
    
    def __init__(self, result):
        """
        Args:
            result: BacktestResult object from BacktestEngine
        """
        self.result = result
        self.output_dir = "results/"
        
        logger.info(f"📊 Performance Analyzer initialized for {result.strategy_name}")
    
    def generate_report(self, output_dir: str = "results/") -> str:
        """
        Generate comprehensive text report and save to file.
        
        Returns:
            Path to generated report file
        """
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.result.strategy_name}_{self.result.symbol.replace('/', '_')}_{timestamp}.txt"
        filepath = os.path.join(output_dir, filename)
        
        report = self._build_report_text()
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        logger.info(f"📄 Report saved to: {filepath}")
        return filepath
    
    def _build_report_text(self) -> str:
        """Build formatted text report."""
        r = self.result
        
        report = f"""
{'='*80}
BACKTEST PERFORMANCE REPORT
{'='*80}

STRATEGY INFORMATION
{'─'*80}
Strategy Name:           {r.strategy_name.upper()}
Symbol:                  {r.symbol}
Timeframe:               {r.timeframe}
Test Period:             {r.start_date} to {r.end_date}
Total Candles:           {r.total_candles:,}

ACCOUNT PERFORMANCE
{'─'*80}
Initial Balance:         ₹{r.initial_balance:,.2f}
Final Balance:           ₹{r.final_balance:,.2f}
Total Return:            ₹{r.total_return_inr:+,.2f} ({r.total_return_pct:+.2f}%)
Peak Balance:            ₹{r.initial_balance + r.gross_profit:,.2f}

TRADE STATISTICS
{'─'*80}
Total Trades:            {r.total_trades}
Winning Trades:          {r.winning_trades} ({r.win_rate_pct:.1f}%)
Losing Trades:           {r.losing_trades} ({100-r.win_rate_pct:.1f}%)
Win Rate:                {r.win_rate_pct:.2f}%

PROFIT & LOSS
{'─'*80}
Gross Profit:            ₹{r.gross_profit:,.2f}
Gross Loss:              ₹{r.gross_loss:,.2f}
Net Profit:              ₹{r.total_return_inr:+,.2f}
Profit Factor:           {r.profit_factor:.2f}x

Average Win:             ₹{r.avg_win:,.2f}
Average Loss:            ₹{r.avg_loss:,.2f}
Avg Win/Loss Ratio:      {r.avg_rr_ratio:.2f}

Largest Win:             ₹{r.largest_win:,.2f}
Largest Loss:            ₹{r.largest_loss:,.2f}

RISK METRICS
{'─'*80}
Maximum Drawdown:        {r.max_drawdown_pct:.2f}% (₹{r.max_drawdown_inr:,.2f})
Sharpe Ratio:            {r.sharpe_ratio:.2f}
Risk/Reward Ratio:       {r.avg_rr_ratio:.2f}

TRADING FREQUENCY
{'─'*80}
Test Duration (days):    {len(r.daily_stats)}
Trades per Day:          {r.total_trades / max(len(r.daily_stats), 1):.2f}
Best Day P&L:            ₹{max((d['pnl'] for d in r.daily_stats), default=0):+,.2f}
Worst Day P&L:           ₹{min((d['pnl'] for d in r.daily_stats), default=0):+,.2f}

PERFORMANCE ASSESSMENT
{'─'*80}
"""
        
        # Add performance grade
        report += self._performance_grade(r)
        
        report += f"\n{'='*80}\n"
        report += "END OF REPORT\n"
        report += f"{'='*80}\n"
        
        return report
    
    def _performance_grade(self, r) -> str:
        """Generate performance assessment."""
        grade = []

        # Win rate assessment
        if r.win_rate_pct >= 55:
            grade.append("✅ Win Rate: EXCELLENT (≥55%)")
        elif r.win_rate_pct >= 45:
            grade.append("✅ Win Rate: GOOD (≥45%) — solid for trend-following")
        elif r.win_rate_pct >= 40:
            grade.append("✓ Win Rate: ACCEPTABLE (≥40%) — viable with strong R:R")
        else:
            grade.append("⚠️ Win Rate: NEEDS IMPROVEMENT (<40%)")

        # Profit factor assessment
        if r.profit_factor >= 2.0:
            grade.append("✅ Profit Factor: EXCELLENT (≥2.0)")
        elif r.profit_factor >= 1.5:
            grade.append("✓ Profit Factor: GOOD (≥1.5)")
        elif r.profit_factor >= 1.0:
            grade.append("⚠️ Profit Factor: MARGINAL (1.0–1.5)")
        else:
            grade.append("❌ Profit Factor: POOR (<1.0)")

        # Drawdown assessment
        if r.max_drawdown_pct <= 5:
            grade.append("✅ Max Drawdown: EXCELLENT (≤5%)")
        elif r.max_drawdown_pct <= 10:
            grade.append("✓ Max Drawdown: GOOD (≤10%)")
        elif r.max_drawdown_pct <= 20:
            grade.append("⚠️ Max Drawdown: ACCEPTABLE (≤20%)")
        else:
            grade.append("❌ Max Drawdown: HIGH (>20%)")

        # Return assessment — scaled to 90-day single pair reality
        if r.total_return_pct >= 10:
            grade.append("✅ Total Return: STRONG (≥10%)")
        elif r.total_return_pct >= 5:
            grade.append("✓ Total Return: GOOD (≥5%)")
        elif r.total_return_pct >= 2:
            grade.append("✓ Total Return: MODEST (≥2%) — acceptable for low-risk strategy")
        elif r.total_return_pct >= 0:
            grade.append("⚠️ Total Return: FLAT (<2%)")
        else:
            grade.append("❌ Total Return: NEGATIVE")

        # Sharpe ratio assessment — most important single metric
        if r.sharpe_ratio >= 2.5:
            grade.append("✅ Sharpe Ratio: EXCEPTIONAL (≥2.5) — hedge fund grade")
        elif r.sharpe_ratio >= 1.5:
            grade.append("✅ Sharpe Ratio: STRONG (≥1.5)")
        elif r.sharpe_ratio >= 1.0:
            grade.append("✓ Sharpe Ratio: ACCEPTABLE (≥1.0)")
        else:
            grade.append("⚠️ Sharpe Ratio: WEAK (<1.0) — returns not worth the risk")

        # Overall verdict — rebalanced to weight Sharpe + PF heavily
        grade.append("\nOVERALL VERDICT:")

        is_exceptional = (
            r.sharpe_ratio >= 2.0 and
            r.profit_factor >= 2.0 and
            r.max_drawdown_pct <= 5 and
            r.total_return_pct > 0
        )
        is_live_ready = (
            r.total_return_pct > 5 and
            r.win_rate_pct >= 45 and
            r.profit_factor >= 1.5 and
            r.sharpe_ratio >= 1.5
        )
        is_promising = (
            r.total_return_pct > 0 and
            r.profit_factor >= 1.2 and
            r.sharpe_ratio >= 1.0
        )

        if is_exceptional:
            grade.append("🏆 STRATEGY EXCEPTIONAL — Ready for paper trading immediately")
        elif is_live_ready:
            grade.append("✅ STRATEGY READY — Begin paper trading, target 30-day live validation")
        elif is_promising:
            grade.append("⚠️ STRATEGY SHOWS PROMISE — Continue optimizing")
        else:
            grade.append("❌ STRATEGY NEEDS SIGNIFICANT IMPROVEMENT")

        return "\n".join(grade)
    
    def plot_all_charts(self, output_dir: str = "results/"):
        """Generate all visualization charts."""
        if not MATPLOTLIB_AVAILABLE:
            logger.error("❌ Cannot generate charts: matplotlib not installed")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = f"{self.result.strategy_name}_{self.result.symbol.replace('/', '_')}_{timestamp}"
        
        # Generate individual charts
        self.plot_equity_curve(os.path.join(output_dir, f"{prefix}_equity.png"))
        self.plot_drawdown(os.path.join(output_dir, f"{prefix}_drawdown.png"))
        self.plot_trade_distribution(os.path.join(output_dir, f"{prefix}_distribution.png"))
        self.plot_monthly_returns(os.path.join(output_dir, f"{prefix}_monthly.png"))
        self.plot_dashboard(os.path.join(output_dir, f"{prefix}_dashboard.png"))
        
        logger.info(f"📊 All charts saved to: {output_dir}")
    
    def plot_equity_curve(self, filepath: str):
        """Plot equity curve over time."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        equity = self.result.equity_curve
        if not equity:
            logger.warning("No equity data to plot")
            return
        
        timestamps = [datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S") for e in equity]
        balances = [e["balance"] for e in equity]
        
        plt.figure(figsize=(14, 7))
        plt.plot(timestamps, balances, linewidth=2, color='#2E86AB', label='Balance')
        plt.axhline(y=self.result.initial_balance, color='gray', linestyle='--', alpha=0.5, label='Initial Balance')
        
        plt.title(f'Equity Curve - {self.result.strategy_name.upper()} on {self.result.symbol}', 
                  fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Balance (₹)', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📈 Equity curve saved: {filepath}")
    
    def plot_drawdown(self, filepath: str):
        """Plot drawdown chart."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        equity = self.result.equity_curve
        if not equity:
            return
        
        timestamps = [datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S") for e in equity]
        balances = [e["balance"] for e in equity]
        
        # Calculate drawdown
        peak = balances[0]
        drawdowns = []
        for balance in balances:
            if balance > peak:
                peak = balance
            dd = ((peak - balance) / peak) * 100
            drawdowns.append(-dd)  # Negative for visual
        
        plt.figure(figsize=(14, 7))
        plt.fill_between(timestamps, drawdowns, 0, color='#A23B72', alpha=0.3)
        plt.plot(timestamps, drawdowns, color='#A23B72', linewidth=2)
        
        plt.title(f'Drawdown - {self.result.strategy_name.upper()}', fontsize=16, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Drawdown (%)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📉 Drawdown chart saved: {filepath}")
    
    def plot_trade_distribution(self, filepath: str):
        """Plot win/loss distribution."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        trades = self.result.all_trades
        if not trades:
            return
        
        pnls = [t["realized_pnl_inr"] for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Histogram
        ax1.hist([wins, losses], bins=20, label=['Wins', 'Losses'], 
                 color=['#06D6A0', '#EF476F'], alpha=0.7)
        ax1.set_title('P&L Distribution', fontsize=14, fontweight='bold')
        ax1.set_xlabel('P&L (₹)', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Pie chart
        ax2.pie([len(wins), len(losses)], 
                labels=[f'Wins: {len(wins)}', f'Losses: {len(losses)}'],
                colors=['#06D6A0', '#EF476F'],
                autopct='%1.1f%%',
                startangle=90)
        ax2.set_title('Win/Loss Ratio', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📊 Trade distribution saved: {filepath}")
    
    def plot_monthly_returns(self, filepath: str):
        """Plot monthly returns bar chart."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        daily = self.result.daily_stats
        if not daily:
            return
        
        # Aggregate by month
        monthly = {}
        for day in daily:
            month = day["date"][:7]  # YYYY-MM
            if month not in monthly:
                monthly[month] = 0
            monthly[month] += day["pnl"]
        
        months = list(monthly.keys())
        returns = list(monthly.values())
        colors = ['#06D6A0' if r >= 0 else '#EF476F' for r in returns]
        
        plt.figure(figsize=(14, 7))
        plt.bar(months, returns, color=colors, alpha=0.7)
        plt.axhline(y=0, color='black', linewidth=0.8)
        
        plt.title(f'Monthly Returns - {self.result.strategy_name.upper()}', 
                  fontsize=16, fontweight='bold')
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('P&L (₹)', fontsize=12)
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"📅 Monthly returns saved: {filepath}")
    
    def plot_dashboard(self, filepath: str):
        """Create a dashboard with key metrics."""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        r = self.result
        
        fig = plt.figure(figsize=(16, 10))
        fig.suptitle(f'Strategy Performance Dashboard - {r.strategy_name.upper()}', 
                     fontsize=18, fontweight='bold')
        
        # Create grid
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. Equity Curve
        ax1 = fig.add_subplot(gs[0, :])
        equity = r.equity_curve
        if equity:
            timestamps = [datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S") for e in equity]
            balances = [e["balance"] for e in equity]
            ax1.plot(timestamps, balances, linewidth=2, color='#2E86AB')
            ax1.axhline(y=r.initial_balance, color='gray', linestyle='--', alpha=0.5)
            ax1.set_title('Equity Curve', fontweight='bold')
            ax1.set_ylabel('Balance (₹)')
            ax1.grid(True, alpha=0.3)
        
        # 2. Key Metrics (Text)
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.axis('off')
        metrics_text = f"""
        Total Return: {r.total_return_pct:+.2f}%
        Net P&L: ₹{r.total_return_inr:+,.2f}
        
        Total Trades: {r.total_trades}
        Win Rate: {r.win_rate_pct:.1f}%
        Profit Factor: {r.profit_factor:.2f}x
        """
        ax2.text(0.1, 0.5, metrics_text, fontsize=12, verticalalignment='center',
                 family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # 3. Risk Metrics
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.axis('off')
        risk_text = f"""
        Max Drawdown: {r.max_drawdown_pct:.2f}%
        Sharpe Ratio: {r.sharpe_ratio:.2f}
        
        Avg Win: ₹{r.avg_win:.2f}
        Avg Loss: ₹{r.avg_loss:.2f}
        Avg R:R: {r.avg_rr_ratio:.2f}
        """
        ax3.text(0.1, 0.5, risk_text, fontsize=12, verticalalignment='center',
                 family='monospace', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
        
        # 4. Win/Loss Pie
        ax4 = fig.add_subplot(gs[1, 2])
        ax4.pie([r.winning_trades, r.losing_trades],
                labels=['Wins', 'Losses'],
                colors=['#06D6A0', '#EF476F'],
                autopct='%1.1f%%',
                startangle=90)
        ax4.set_title('Win/Loss Distribution', fontweight='bold')
        
        # 5. Monthly Returns
        ax5 = fig.add_subplot(gs[2, :])
        if r.daily_stats:
            monthly = {}
            for day in r.daily_stats:
                month = day["date"][:7]
                if month not in monthly:
                    monthly[month] = 0
                monthly[month] += day["pnl"]
            
            months = list(monthly.keys())
            returns = list(monthly.values())
            colors = ['#06D6A0' if ret >= 0 else '#EF476F' for ret in returns]
            ax5.bar(months, returns, color=colors, alpha=0.7)
            ax5.axhline(y=0, color='black', linewidth=0.8)
            ax5.set_title('Monthly Returns', fontweight='bold')
            ax5.set_ylabel('P&L (₹)')
            ax5.tick_params(axis='x', rotation=45)
            ax5.grid(True, alpha=0.3, axis='y')
        
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"🎯 Dashboard saved: {filepath}")
    
    def export_trades_csv(self, filepath: str):
        """Export all trades to CSV for further analysis."""
        import csv
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='') as f:
            if not self.result.all_trades:
                logger.warning("No trades to export")
                return
            
            writer = csv.DictWriter(f, fieldnames=self.result.all_trades[0].keys())
            writer.writeheader()
            writer.writerows(self.result.all_trades)
        
        logger.info(f"💾 Trades exported to: {filepath}")
