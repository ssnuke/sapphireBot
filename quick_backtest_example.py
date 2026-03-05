"""
quick_backtest_example.py
-------------------------
Quick example showing how to run a backtest programmatically.
Useful for custom analysis or parameter optimization.
"""

from core.backtest_engine import BacktestEngine, BacktestConfig
from core.performance_analyzer import PerformanceAnalyzer
from strategies.ema_crossover import EMACrossoverStrategy
from strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from strategies.opening_range_breakout import OpeningRangeBreakoutStrategy


def example_single_backtest():
    """Example: Run a single backtest."""
    print("="*60)
    print("Example 1: Single Strategy Backtest")
    print("="*60)
    
    # Create strategy instance
    strategy = EMACrossoverStrategy(symbol="BTC/USDT", timeframe="15m")
    
    # Configure backtest
    config = BacktestConfig(
        symbol="BTC/USDT",
        timeframe="15m",
        days=90,  # 3 months of data
        strategy=strategy,
        initial_balance=10000.0,
        risk_per_trade_pct=0.25,
        max_loss_day_pct=3.0,
        max_trades_per_day=5,
        leverage=5
    )
    
    # Run backtest
    engine = BacktestEngine(config)
    result = engine.run()
    
    # Analyze results
    analyzer = PerformanceAnalyzer(result)
    analyzer.generate_report(output_dir="results/")
    analyzer.plot_all_charts(output_dir="results/")
    
    print(f"\n✅ Final Balance: ₹{result.final_balance:,.2f}")
    print(f"📈 Total Return: {result.total_return_pct:+.2f}%")
    print(f"🎯 Win Rate: {result.win_rate_pct:.1f}%")
    print(f"📊 Profit Factor: {result.profit_factor:.2f}x")


def example_parameter_optimization():
    """Example: Test different EMA periods."""
    print("\n" + "="*60)
    print("Example 2: Parameter Optimization")
    print("="*60)
    
    # Test different EMA combinations
    ema_combinations = [
        (9, 21),   # Default
        (8, 21),   # Faster entry
        (12, 26),  # Slower, more conservative
        (5, 15),   # Very aggressive
    ]
    
    results = []
    
    for fast, slow in ema_combinations:
        print(f"\n🔍 Testing EMA {fast}/{slow}...")
        
        # Create custom strategy with parameters
        strategy = EMACrossoverStrategy(
            symbol="BTC/USDT",
            timeframe="15m",
            fast=fast,
            slow=slow
        )
        
        config = BacktestConfig(
            symbol="BTC/USDT",
            timeframe="15m",
            days=90,
            strategy=strategy,
            initial_balance=10000.0,
            risk_per_trade_pct=0.25,
            leverage=5
        )
        
        engine = BacktestEngine(config)
        result = engine.run()
        
        results.append({
            "params": f"EMA {fast}/{slow}",
            "return": result.total_return_pct,
            "win_rate": result.win_rate_pct,
            "profit_factor": result.profit_factor,
            "trades": result.total_trades
        })
    
    # Print comparison
    print("\n" + "="*80)
    print("📊 PARAMETER COMPARISON")
    print("="*80)
    print(f"{'Parameters':<15} {'Return %':>10} {'Win Rate':>10} {'PF':>8} {'Trades':>8}")
    print("-"*80)
    
    for r in results:
        print(
            f"{r['params']:<15} "
            f"{r['return']:>9.2f}% "
            f"{r['win_rate']:>9.1f}% "
            f"{r['profit_factor']:>7.2f}x "
            f"{r['trades']:>8}"
        )
    
    # Find best
    best = max(results, key=lambda x: x['return'])
    print("="*80)
    print(f"🏆 Best: {best['params']} with {best['return']:+.2f}% return")


def example_multi_symbol_backtest():
    """Example: Test strategy across multiple symbols."""
    print("\n" + "="*60)
    print("Example 3: Multi-Symbol Backtest")
    print("="*60)
    
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    results = []
    
    for symbol in symbols:
        print(f"\n🔍 Testing {symbol}...")
        
        strategy = RSIMeanReversionStrategy(symbol=symbol, timeframe="15m")
        
        config = BacktestConfig(
            symbol=symbol,
            timeframe="15m",
            days=90,
            strategy=strategy,
            initial_balance=10000.0,
            risk_per_trade_pct=0.25,
            leverage=5
        )
        
        engine = BacktestEngine(config)
        result = engine.run()
        
        results.append({
            "symbol": symbol,
            "return": result.total_return_pct,
            "win_rate": result.win_rate_pct,
            "max_dd": result.max_drawdown_pct,
            "trades": result.total_trades
        })
    
    # Print comparison
    print("\n" + "="*80)
    print("📊 SYMBOL COMPARISON - RSI Mean Reversion")
    print("="*80)
    print(f"{'Symbol':<12} {'Return %':>10} {'Win Rate':>10} {'Max DD':>10} {'Trades':>8}")
    print("-"*80)
    
    for r in results:
        print(
            f"{r['symbol']:<12} "
            f"{r['return']:>9.2f}% "
            f"{r['win_rate']:>9.1f}% "
            f"{r['max_dd']:>9.2f}% "
            f"{r['trades']:>8}"
        )
    
    print("="*80)


if __name__ == "__main__":
    # Run examples
    
    # Example 1: Basic backtest
    example_single_backtest()
    
    # Example 2: Parameter optimization (commented out by default - takes longer)
    # example_parameter_optimization()
    
    # Example 3: Multi-symbol testing (commented out by default - takes longer)
    # example_multi_symbol_backtest()
    
    print("\n✅ Examples complete! Check results/ folder for outputs.")
    print("💡 Uncomment other examples in the code to run them.")
