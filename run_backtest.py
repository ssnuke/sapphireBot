"""
run_backtest.py
----------------
Main backtesting runner script.

Usage:
    python run_backtest.py                    # Backtest active strategy from config
    python run_backtest.py --all              # Backtest all strategies and compare
    python run_backtest.py --strategy ema_crossover --days 180
    python run_backtest.py --symbol ETH/USDT --timeframe 1h
"""

import sys
import os
import logging
import argparse
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import load_config, get
from utils.logger import setup_logger
from strategies.strategy_factory import load_strategy, STRATEGY_MAP
from core.backtest_engine import BacktestEngine, BacktestConfig
from core.performance_analyzer import PerformanceAnalyzer


def setup_backtest_logger():
    """Setup logger for backtesting."""
    setup_logger()
    logger = logging.getLogger("backtest")
    logger.setLevel(logging.INFO)
    return logger


def run_single_backtest(
    strategy_name: str,
    symbol: str,
    timeframe: str,
    days: int,
    logger: logging.Logger
) -> None:
    """
    Run backtest for a single strategy.
    
    Args:
        strategy_name: Name of strategy to test
        symbol: Trading pair (e.g., "BTC/USDT")
        timeframe: Candle interval (e.g., "15m")
        days: Number of days of historical data
        logger: Logger instance
    """
    logger.info("=" * 80)
    logger.info(f"🎯 BACKTESTING: {strategy_name.upper()}")
    logger.info("=" * 80)
    
    # Load strategy
    strategy = load_strategy(symbol=symbol, timeframe=timeframe)
    if strategy.get_name() != strategy_name:
        # Strategy name mismatch, reload with correct one
        logger.warning(f"Active strategy is {strategy.get_name()}, switching to {strategy_name}")
        strategy_class = STRATEGY_MAP.get(strategy_name)
        if not strategy_class:
            logger.error(f"Strategy '{strategy_name}' not found!")
            return
        strategy = strategy_class(symbol=symbol, timeframe=timeframe)
    
    # Create backtest config
    config = BacktestConfig(
        symbol=symbol,
        timeframe=timeframe,
        days=days,
        strategy=strategy,
        initial_balance=get("account.balance"),
        risk_per_trade_pct=get("risk.risk_per_trade_pct"),
        max_loss_day_pct=get("risk.max_loss_day_pct"),
        max_trades_per_day=get("risk.max_trades_per_day"),
        leverage=get("risk.leverage"),
        slippage_pct=get("backtesting.slippage_pct"),
        commission_pct=get("backtesting.commission_pct")
    )
    
    # Run backtest
    engine = BacktestEngine(config)
    result = engine.run()
    
    # Analyze results
    analyzer = PerformanceAnalyzer(result)
    
    # Generate report
    results_dir = get("backtesting.results_dir", "results/")
    report_path = analyzer.generate_report(output_dir=results_dir)
    
    # Print to console
    print("\n" + analyzer._build_report_text())
    
    # Generate charts if enabled
    if get("backtesting.generate_charts", True):
        try:
            analyzer.plot_all_charts(output_dir=results_dir)
            logger.info(f"📊 Charts generated in {results_dir}")
        except Exception as e:
            logger.warning(f"Could not generate charts: {e}")
            logger.info("💡 Install matplotlib: pip install matplotlib")
    
    # Export trades CSV if enabled
    if get("backtesting.export_trades_csv", True):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"{strategy_name}_{symbol.replace('/', '_')}_{timestamp}_trades.csv"
        analyzer.export_trades_csv(f"{results_dir}/{csv_filename}")
    
    logger.info("=" * 80)
    logger.info(f"✅ Backtest complete! Results saved to: {results_dir}")
    logger.info("=" * 80)


def run_all_strategies_comparison(
    symbol: str,
    timeframe: str,
    days: int,
    logger: logging.Logger
) -> None:
    """
    Run backtest for all available strategies and compare results.
    
    Args:
        symbol: Trading pair
        timeframe: Candle interval
        days: Days of historical data
        logger: Logger instance
    """
    logger.info("=" * 80)
    logger.info("🏆 STRATEGY COMPARISON MODE")
    logger.info("=" * 80)
    
    results = []
    
    for strategy_name in STRATEGY_MAP.keys():
        logger.info(f"\n▶️  Testing {strategy_name}...")
        
        # Load strategy
        strategy_class = STRATEGY_MAP[strategy_name]
        strategy = strategy_class(symbol=symbol, timeframe=timeframe)
        
        # Create config
        config = BacktestConfig(
            symbol=symbol,
            timeframe=timeframe,
            days=days,
            strategy=strategy,
            initial_balance=get("account.balance"),
            risk_per_trade_pct=get("risk.risk_per_trade_pct"),
            max_loss_day_pct=get("risk.max_loss_day_pct"),
            max_trades_per_day=get("risk.max_trades_per_day"),
            leverage=get("risk.leverage"),
            slippage_pct=get("backtesting.slippage_pct"),
            commission_pct=get("backtesting.commission_pct")
        )
        
        # Run backtest
        engine = BacktestEngine(config)
        result = engine.run()
        results.append(result)
        
        # Generate individual reports
        analyzer = PerformanceAnalyzer(result)
        results_dir = get("backtesting.results_dir", "results/")
        analyzer.generate_report(output_dir=results_dir)
        
        if get("backtesting.generate_charts", True):
            try:
                analyzer.plot_all_charts(output_dir=results_dir)
            except:
                pass
    
    # Print comparison table
    print("\n" + "=" * 100)
    print("📊 STRATEGY COMPARISON RESULTS")
    print("=" * 100)
    print(f"{'Strategy':<25} {'Return %':>10} {'Trades':>8} {'Win Rate':>10} {'Profit Factor':>15} {'Max DD %':>10}")
    print("-" * 100)
    
    for result in results:
        print(
            f"{result.strategy_name:<25} "
            f"{result.total_return_pct:>9.2f}% "
            f"{result.total_trades:>8} "
            f"{result.win_rate_pct:>9.1f}% "
            f"{result.profit_factor:>14.2f}x "
            f"{result.max_drawdown_pct:>9.2f}%"
        )
    
    print("=" * 100)
    
    # Find best strategy
    best = max(results, key=lambda r: r.total_return_pct)
    logger.info(f"\n🏆 BEST PERFORMER: {best.strategy_name.upper()}")
    logger.info(f"   Return: {best.total_return_pct:+.2f}% | Win Rate: {best.win_rate_pct:.1f}% | PF: {best.profit_factor:.2f}x")


def run_all_pairs_backtest(
    strategy_name: str,
    timeframe: str,
    days: int,
    logger: logging.Logger
) -> None:
    """Run backtest across all configured pairs and print combined summary."""
    pairs = get("trading.pairs")  # Reads ["BTC/USDT", "ETH/USDT", "SOL/USDT"] from config

    logger.info("=" * 80)
    logger.info(f"🌐 MULTI-PAIR BACKTEST: {strategy_name.upper()}")
    logger.info(f"   Pairs: {', '.join(pairs)}")
    logger.info("=" * 80)

    results = []
    total_net_profit = 0.0

    for symbol in pairs:
        logger.info(f"\n▶️  Testing {symbol}...")

        strategy_class = STRATEGY_MAP.get(strategy_name)
        if not strategy_class:
            logger.error(f"Strategy '{strategy_name}' not found!")
            return
        strategy = strategy_class(symbol=symbol, timeframe=timeframe)

        config = BacktestConfig(
            symbol=symbol,
            timeframe=timeframe,
            days=days,
            strategy=strategy,
            initial_balance=get("account.balance"),
            risk_per_trade_pct=get("risk.risk_per_trade_pct"),
            max_loss_day_pct=get("risk.max_loss_day_pct"),
            max_trades_per_day=get("risk.max_trades_per_day"),
            leverage=get("risk.leverage"),
            slippage_pct=get("backtesting.slippage_pct"),
            commission_pct=get("backtesting.commission_pct")
        )

        engine = BacktestEngine(config)
        result = engine.run()
        results.append(result)
        total_net_profit += result.total_return_inr

        # Save individual report + CSV per pair
        analyzer = PerformanceAnalyzer(result)
        results_dir = get("backtesting.results_dir", "results/")
        analyzer.generate_report(output_dir=results_dir)
        if get("backtesting.export_trades_csv", True):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{strategy_name}_{symbol.replace('/', '_')}_{timestamp}_trades.csv"
            analyzer.export_trades_csv(f"{results_dir}/{csv_filename}")

    # Print combined summary table
    print("\n" + "=" * 100)
    print(f"📊 MULTI-PAIR RESULTS — {strategy_name.upper()}")
    print("=" * 100)
    print(f"{'Symbol':<15} {'Return %':>10} {'Trades':>8} {'Win Rate':>10} {'Profit Factor':>15} {'Sharpe':>8} {'Max DD %':>10}")
    print("-" * 100)

    total_trades = 0
    total_wins = 0

    for r in results:
        print(
            f"{r.symbol:<15} "
            f"{r.total_return_pct:>+9.2f}% "
            f"{r.total_trades:>8} "
            f"{r.win_rate_pct:>9.1f}% "
            f"{r.profit_factor:>14.2f}x "
            f"{r.sharpe_ratio:>8.2f} "
            f"{r.max_drawdown_pct:>9.2f}%"
        )
        total_trades += r.total_trades
        total_wins += r.winning_trades

    combined_win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    combined_return_pct = (total_net_profit / (get("account.balance") * len(results))) * 100

    print("-" * 100)
    print(
        f"{'COMBINED':<15} "
        f"{combined_return_pct:>+9.2f}% "
        f"{total_trades:>8} "
        f"{combined_win_rate:>9.1f}% "
    )
    print("=" * 100)
    logger.info(f"✅ Multi-pair backtest complete. Combined net profit: ₹{total_net_profit:+.2f}")

def main():
    """Main entry point for backtesting."""
    parser = argparse.ArgumentParser(description="Backtest trading strategies")
    parser.add_argument("--strategy", type=str, help="Strategy to backtest (default: active from config)")
    parser.add_argument("--symbol", type=str, help="Trading pair (default: first from config)")
    parser.add_argument("--timeframe", type=str, help="Timeframe (default: from config)")
    parser.add_argument("--days", type=int, help="Days of historical data (default: from config)")
    parser.add_argument("--all", action="store_true", help="Compare all strategies")
    parser.add_argument("--pairs", action="store_true", help="Backtest across all configured pairs")

    
    args = parser.parse_args()
    
    # Load config and setup logger
    load_config()
    logger = setup_backtest_logger()
    
    # Get parameters
    strategy = args.strategy or get("strategy.active")
    symbol = args.symbol or get("trading.pairs")[0]
    timeframe = args.timeframe or get("trading.timeframe")
    days = args.days or get("backtesting.days_history", 90)
    
    logger.info(f"📋 Backtest Configuration:")
    logger.info(f"   Symbol:     {symbol}")
    logger.info(f"   Timeframe:  {timeframe}")
    logger.info(f"   Period:     {days} days")
    logger.info(f"   Balance:    ₹{get('account.balance'):,.2f}")
    
    # Run backtest
    if args.all or get("backtesting.compare_all_strategies", False):
        run_all_strategies_comparison(symbol, timeframe, days, logger)
    elif args.pairs:                                          # ← ADD THIS
        run_all_pairs_backtest(strategy, timeframe, days, logger)
    else:
        run_single_backtest(strategy, symbol, timeframe, days, logger)





if __name__ == "__main__":
    main()
