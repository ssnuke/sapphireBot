# 🚀 Quick Start - Backtesting System

## Installation

```bash
# Install all dependencies
pip install -r requirements.txt
```

**New packages added:**

- `matplotlib` - For chart generation
- `numpy` - For performance calculations

---

## Run Your First Backtest

### Option 1: Use the default active strategy

```bash
python run_backtest.py
```

This will:
- ✅ Backtest the active strategy from `config.json`
- ✅ Fetch 90 days of BTC/USDT data
- ✅ Generate performance report
- ✅ Create visual charts
- ✅ Export detailed trade log

**Results Location:** `results/` folder

---

### Option 2: Test a specific strategy

```bash
# Test EMA Crossover
python run_backtest.py --strategy ema_crossover

# Test RSI Mean Reversion
python run_backtest.py --strategy rsi_mean_reversion

# Test Opening Range Breakout
python run_backtest.py --strategy opening_range_breakout
```

---

### Option 3: Custom parameters

```bash
# Test ETH with 180 days of data
python run_backtest.py --symbol ETH/USDT --days 180

# Test on 1-hour timeframe
python run_backtest.py --timeframe 1h --days 180

# Full custom test
python run_backtest.py --strategy ema_crossover --symbol SOL/USDT --timeframe 15m --days 90
```

---

### Option 4: Compare all strategies

```bash
python run_backtest.py --all
```

This runs backtests on all 3 strategies and shows a comparison table.

---

## Understanding Your Results

### 1. Text Report

Location: `results/{strategy}_{symbol}_{timestamp}.txt`

**Key Sections:**
- **Account Performance** - Final balance, total return
- **Trade Statistics** - Win rate, number of trades
- **Profit & Loss** - Gross profit/loss, profit factor
- **Risk Metrics** - Max drawdown, Sharpe ratio
- **Performance Assessment** - Is strategy ready for live trading?

**What to look for:**
- ✅ Win Rate ≥55%
- ✅ Profit Factor ≥1.5
- ✅ Max Drawdown ≤20%
- ✅ Total Return >0%

---

### 2. Visual Charts

All saved to `results/` folder:

1. **`*_equity.png`** - Balance over time
   - Look for smooth upward trend

2. **`*_drawdown.png`** - Risk visualization
   - Shows largest losing periods

3. **`*_distribution.png`** - Win/loss histogram
   - More wins than losses = good

4. **`*_monthly.png`** - Monthly returns
   - Consistent green bars = stable strategy

5. **`*_dashboard.png`** - Complete overview
   - All metrics in one view

---

### 3. Trade Log CSV

Location: `results/{strategy}_{symbol}_{timestamp}_trades.csv`

**Contains:**
- Every trade's entry/exit prices
- Stop loss and take profit levels
- P&L per trade
- Exit reasons

**Use for:**
- Detailed analysis in Excel/Google Sheets
- Finding patterns in losing trades
- Verifying strategy logic

---

## Data Sources

**Where does historical data come from?**

1. **Exchange APIs** (via CCXT library)
   - Binance (default) - most reliable
   - Bybit (alternative)
   - Free and comprehensive

2. **Smart Caching**
   - First run: Downloads from exchange
   - Future runs: Uses cached data (instant)
   - Cache location: `data/cache/`

3. **No manual download needed!**
   - Everything is automatic
   - Just run the backtest script

---

## Quick Examples

### Run the example script

```bash
python quick_backtest_example.py
```

This demonstrates:
- Basic backtesting
- Parameter optimization
- Multi-symbol testing

Edit the file to uncomment additional examples.

---

## Position Tracking (Live Trading)

The system now tracks ALL open positions in real-time:

**Features:**
- ✅ Monitors stop-loss automatically
- ✅ Monitors take-profit levels
- ✅ Calculates unrealized P&L
- ✅ Partial exits (50% at TP1, rest at TP2)
- ✅ Complete trade history

**Check Open Positions:**

When running `main.py` (live/paper trading), you'll now see:

```
📊 Daily Summary | Trades: 2 | PnL: ₹+45.50 | Balance: ₹10,045.50 | 
   Open: 1 (Unrealized: ₹+12.30) | Remaining: 3 trades
```

---

## Troubleshooting

### "Matplotlib not installed"

```bash
pip install matplotlib
```

### "CCXT not installed"

```bash
pip install ccxt
```

### "No data available"

- Check internet connection
- Default uses Binance (most reliable)
- Try: `--days 30` for less data

### "No trades executed"

- Strategy may be too conservative
- Check strategy parameters
- Try different timeframe or symbol

---

## Next Steps

1. ✅ **Run first backtest** - See if your strategy is profitable
2. 📊 **Review charts** - Visualize performance
3. 🔍 **Compare strategies** - Use `--all` flag
4. 🎯 **Optimize** - Adjust parameters, re-test
5. 📄 **Paper trade winner** - Test in real-time (paper mode)
6. 🚀 **Go live** - Only after paper trading succeeds

---

## Complete Documentation

For detailed information, see:

- **`BACKTESTING_GUIDE.md`** - Comprehensive guide
- **`IMPLEMENTATION_SUMMARY.md`** - Technical details
- **Code comments** - In-depth explanations

---

## Support

Check these files if you need help:
1. This README (quick reference)
2. `BACKTESTING_GUIDE.md` (detailed guide)
3. Code comments in `core/` modules

---

**Happy backtesting! 🎯**

*Remember: Past performance doesn't guarantee future results.*
