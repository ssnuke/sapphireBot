# Backtesting System - Complete Guide

## 🎯 Overview

Professional-grade backtesting system for validating trading strategies on historical data before risking real capital. Includes position tracking, performance analytics, and visual reporting.

---

## 📦 Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

**New Dependencies Added:**
- `matplotlib` - Chart generation
- `numpy` - Numerical calculations

---

## 🚀 Quick Start

### 1. Run Basic Backtest (Active Strategy)

```bash
python run_backtest.py
```

This will backtest the currently active strategy from `config.json` on default settings.

### 2. Backtest Specific Strategy

```bash
python run_backtest.py --strategy ema_crossover
python run_backtest.py --strategy rsi_mean_reversion
python run_backtest.py --strategy opening_range_breakout
```

### 3. Custom Parameters

```bash
# Test on ETH with 180 days of data
python run_backtest.py --symbol ETH/USDT --days 180

# Test on 1-hour timeframe
python run_backtest.py --timeframe 1h --days 180

# Full custom backtest
python run_backtest.py --strategy ema_crossover --symbol BTC/USDT --timeframe 15m --days 90
```

### 4. Compare All Strategies

```bash
python run_backtest.py --all
```

This runs backtests on all available strategies and generates a comparison table.

---

## 📊 Data Sources

### Automatic Data Fetching (Default)

Data is automatically fetched from exchange APIs via CCXT:

- **Default Exchange**: Binance (most reliable historical data)
- **Alternative**: Bybit (configured in `config.json → backtesting.data_source`)
- **Data Cache**: Automatically cached in `data/cache/` to avoid repeated API calls

### Where Data Comes From

1. **Primary Source**: CCXT Library
   - Connects to Binance/Bybit APIs
   - Fetches OHLCV (Open, High, Low, Close, Volume) data
   - Free and reliable for crypto futures

2. **Cache System**:
   - First run: Downloads from exchange
   - Subsequent runs: Loads from local cache (instant)
   - Cache files: `data/cache/BTC_USDT_15m_90d.json`

3. **Manual CSV Import** (Optional):
   ```python
   from core.data_fetcher import DataFetcher
   
   fetcher = DataFetcher()
   data = fetcher.import_from_csv("my_data.csv")
   ```

### CSV Format for Manual Import

```csv
timestamp,open,high,low,close,volume
2024-01-01 00:00:00,42000,42500,41800,42200,1500
2024-01-01 00:15:00,42200,42600,42100,42400,1800
```

---

## 🔧 Configuration

Edit `config.json` to customize backtesting behavior:

```json
"backtesting": {
  "enabled": true,
  "data_source": "binance",        // "binance", "bybit", or "csv"
  "days_history": 90,               // Amount of historical data
  "cache_data": true,               // Use cached data for speed
  "cache_dir": "data/cache",
  "slippage_pct": 0.05,            // 0.05% slippage simulation
  "commission_pct": 0.04,           // 0.04% taker fee
  "results_dir": "results/",
  "generate_charts": true,          // Create performance charts
  "export_trades_csv": true,        // Export trade log
  "compare_all_strategies": false
}
```

---

## 📈 Understanding Results

### 1. Text Report

Saved to: `results/{strategy}_{symbol}_{timestamp}.txt`

**Key Metrics:**

- **Total Return %**: Overall profit/loss percentage
- **Win Rate**: Percentage of winning trades (target: >55%)
- **Profit Factor**: Gross profit ÷ Gross loss (target: >1.5)
- **Max Drawdown**: Largest peak-to-trough decline (keep <20%)
- **Sharpe Ratio**: Risk-adjusted return metric
- **Average R:R**: Average risk/reward ratio per trade

**Performance Grades:**

- ✅ **Excellent**: Strategy exceeds targets
- ✓ **Good**: Strategy meets minimum requirements
- ⚠️ **Needs Improvement**: Below acceptable thresholds
- ❌ **Poor**: Strategy not viable

### 2. Visual Charts

All charts saved to `results/` folder:

#### A. Equity Curve (`*_equity.png`)
- Shows balance growth over time
- Indicates strategy consistency
- **Look for**: Smooth upward trend

#### B. Drawdown Chart (`*_drawdown.png`)
- Visualizes risk exposure
- Shows largest losing periods
- **Target**: Max drawdown <20%

#### C. Trade Distribution (`*_distribution.png`)
- Histogram of win/loss amounts
- Pie chart of win rate
- **Look for**: More/larger wins than losses

#### D. Monthly Returns (`*_monthly.png`)
- Bar chart of monthly P&L
- Identifies seasonal patterns
- **Look for**: Consistent positive months

#### E. Dashboard (`*_dashboard.png`)
- Comprehensive performance overview
- All key metrics in one view
- Best for quick assessment

### 3. Trade Log CSV

Detailed trade-by-trade breakdown:

`results/{strategy}_{symbol}_{timestamp}_trades.csv`

Columns:
- Entry/Exit prices and times
- Stop loss and take profit levels
- P&L per trade
- Exit reason (stop_loss, take_profit_1, etc.)

**Use for:**
- Detailed trade analysis
- Finding patterns in losses
- Importing to Excel/Google Sheets

---

## 🎓 Professional Analysis Tips

### 1. Minimum Viable Strategy (JP Morgan Standards)

A strategy must meet ALL these criteria before live trading:

- ✅ **Win Rate**: ≥50% (ideally ≥55%)
- ✅ **Profit Factor**: ≥1.5 (ideally ≥2.0)
- ✅ **Max Drawdown**: ≤20% (ideally ≤10%)
- ✅ **Positive Returns**: Over 90-day test period
- ✅ **Sample Size**: At least 30 trades in backtest
- ✅ **Sharpe Ratio**: ≥1.0 (ideally ≥1.5)

### 2. Red Flags to Watch For

❌ **Win Rate <45%**: Strategy loses more than it wins
❌ **Profit Factor <1.0**: Losses exceed profits
❌ **Max Drawdown >30%**: Excessive risk
❌ **<20 Trades**: Not enough data to be statistically significant
❌ **Erratic Equity Curve**: High volatility, unreliable

### 3. Optimization Workflow

1. **Run Initial Backtest** (90 days)
   ```bash
   python run_backtest.py --strategy ema_crossover
   ```

2. **Analyze Results**
   - Check performance grade
   - Review charts for patterns
   - Examine trade log for loss clusters

3. **Adjust Strategy Parameters**
   - Modify strategy file (e.g., `strategies/ema_crossover.py`)
   - Tune indicator periods, thresholds
   - Adjust stop loss/take profit logic

4. **Re-test on Different Periods**
   ```bash
   # Test on 180 days for robustness
   python run_backtest.py --strategy ema_crossover --days 180
   
   # Test on different symbols
   python run_backtest.py --symbol ETH/USDT
   python run_backtest.py --symbol SOL/USDT
   ```

5. **Compare All Strategies**
   ```bash
   python run_backtest.py --all
   ```

6. **Forward Test** (Paper Trading)
   - Once backtest passes all criteria
   - Run in paper mode for 2-4 weeks
   - Must match backtest performance

---

## 📊 Position Tracking (Live & Backtest)

The `PositionTracker` class monitors all open trades:

### Features:
- ✅ Real-time unrealized P&L calculation
- ✅ Automatic stop loss / take profit monitoring
- ✅ Partial exits (50% at TP1, rest at TP2)
- ✅ Trade history and status tracking

### Integration in Live Trading:

```python
from core.position_tracker import PositionTracker

tracker = PositionTracker()

# Open position
position = tracker.open_position(
    symbol="BTC/USDT",
    strategy="ema_crossover",
    signal="buy",
    entry_price=42000,
    entry_time="2024-01-01 10:00:00",
    sizing=sizing_dict
)

# Update positions each candle
closed_trades = tracker.update_all_positions(current_candle, "BTC/USDT")

# Get open positions summary
open_positions = tracker.get_open_positions_summary()
```

---

## 🔍 Troubleshooting

### Issue: "Matplotlib not installed"

**Solution:**
```bash
pip install matplotlib
```

### Issue: "Insufficient data: got X candles"

**Cause**: Not enough historical data available
**Solution**: 
- Reduce `--days` parameter
- Check exchange data availability
- Some coins have limited history

### Issue: "No trades executed in backtest"

**Possible Causes:**
1. Strategy too conservative (no signals generated)
2. Risk limits too strict
3. Data quality issues

**Solutions:**
- Review strategy signal generation logic
- Check `config.json` risk parameters
- Verify data with `print(candles)` in strategy

### Issue: "Connection timeout fetching data"

**Solutions:**
- Check internet connection
- Reduce `days` parameter (fetch less data)
- Use cached data: Already fetched once? It's cached automatically

---

## 📁 Project Structure

```
algo_trader/
├── core/
│   ├── backtest_engine.py       # Main backtesting logic
│   ├── data_fetcher.py          # Historical data fetching
│   ├── position_tracker.py      # Open position management
│   ├── performance_analyzer.py  # Results analysis & charts
│   └── risk_manager.py          # Risk management
├── strategies/
│   ├── ema_crossover.py
│   ├── rsi_mean_reversion.py
│   └── opening_range_breakout.py
├── data/
│   └── cache/                   # Cached historical data
├── results/                     # Backtest results (reports & charts)
├── run_backtest.py              # Main backtest runner
└── config.json                  # Configuration
```

---

## 🎯 Next Steps

1. **Run Your First Backtest**:
   ```bash
   python run_backtest.py
   ```

2. **Review the Results**:
   - Check `results/` folder for report
   - Open charts to visualize performance

3. **Compare Strategies**:
   ```bash
   python run_backtest.py --all
   ```

4. **Optimize Best Strategy**:
   - Tune parameters based on results
   - Re-test with different timeframes/pairs

5. **Paper Trade Winner**:
   - Best strategy moves to paper trading
   - Monitor for 2-4 weeks
   - Compare live vs backtest performance

6. **Go Live** (Only after success in paper):
   - Update `config.json → account.mode = "live"`
   - Add API credentials
   - Start with minimum position sizes

---

## 📞 Support

For questions or issues:
1. Check troubleshooting section above
2. Review code comments in core modules
3. Examine example outputs in `results/`

---

**Remember**: Past performance doesn't guarantee future results. Always paper trade before going live!

Good luck! 🚀
