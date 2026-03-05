# 🤖 Algo Trader — Live Bot Implementation (v2)

Complete system for **24/7 automated crypto trading** with:
- ✅ **Live order execution** (via order_manager)
- ✅ **State persistence & recovery** (automatic on restart)
- ✅ **Telegram/Webhook notifications** (hourly updates + alerts)
- ✅ **Network retry logic** (exponential backoff)
- ✅ **Secure credential management** (env vars)
- ✅ **Docker & Systemd deployment** (production-ready)

---

## 🎯 What's New (v2)

### Core Features Added

| Feature | Description | File |
|---------|-------------|------|
| **Order Manager** | Places real orders via CCXT with retries | `core/order_manager.py` |
| **Persistence** | Saves positions & state to disk | `core/position_tracker.py` |
| **Notifications** | Telegram + webhook alerts | `utils/notifier.py` |
| **State Manager** | Recovers bot state on restart | `utils/state_manager.py` |
| **Live Main Loop** | Full trading loop with error handling | `main.py` |

### Configuration Updates

```json
"account": {
  "api_key": "",              // optional, or set env var BYBIT_API_KEY
  "api_secret": ""            // optional, or set env var BYBIT_API_SECRET
},
"notifications": {
  "telegram_enabled": false,
  "relegram_webhook": "",
  "notify_hourly_update": true
}
```

---

## 🚀 Deployment Methods

### Method 1: Docker (Recommended)

**Fastest way to get running on any cloud.**

```bash
# 1. Clone repo
git clone https://github.com/yourusername/algo_trader.git
cd algo_trader

# 2. Create .env with credentials
cat > .env << EOF
BYBIT_API_KEY=your_key
BYBIT_API_SECRET=your_secret
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id
EOF

# 3. Start the bot
docker-compose up -d

# 4. Monitor
docker-compose logs -f algo-trader

# 5. Stop
docker-compose down
```

**Features:**
- Isolated container environment
- Auto-restart on failure
- Persistent volumes (data, logs, config)
- Resource limits (512MB, 1 CPU)
- JSON logging with rotation

---

### Method 2: Systemd Service (VPS)

**Best for long-term, stable deployment on your own VPS.**

```bash
# 1. SSH to VPS
ssh user@your_vps.com

# 2. Run deployment script
cd algo_trader
chmod +x deploy.sh
sudo ./deploy.sh live

# 3. Bot runs in background (systemd)
sudo systemctl status algo-trader

# 4. View logs
sudo tail -f /var/log/algo-trader/bot.log
```

**Features:**
- System user isolation (`algo`)
- Automatic startup on boot
- Graceful restart handling
- Log rotation (7-day keep)
- Systemd service management

---

### Method 3: Manual (Development)

**For local testing or debugging.**

```bash
# 1. Create Python venv
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set credentials
export BYBIT_API_KEY="your_key"
export BYBIT_API_SECRET="your_secret"

# 4. Run bot
python3 main.py
```

---

## 🔐 Credential Management

### Option A: Environment Variables (Recommended)

```bash
# Set before running bot
export BYBIT_API_KEY="pk_live_..."
export BYBIT_API_SECRET="sk_live_..."

# Or in systemd:
# /etc/algo-trader/env
# BYBIT_API_KEY=pk_live_...
# BYBIT_API_SECRET=sk_live_...

# Or in docker-compose:
# .env file with BYBIT_API_KEY=...
```

### Option B: Config File (LESS SECURE)

In `config.json`:
```json
{
  "account": {
    "api_key": "pk_live_...",
    "api_secret": "sk_live_..."
  }
}
```

⚠️ **Warning:** Never commit `.env` or `config.json` with credentials to git!

```bash
# .gitignore
.env
config.json
data/
logs/
```

---

## 📊 State Persistence

The bot saves state automatically to two files:

### 1. `data/bot_state.json` (Session state)

```json
{
  "version": "1.0",
  "last_save": "2026-03-05T14:30:00",
  "balance": 10250.50,
  "daily_pnl": 250.50,
  "trades_today": 3,
  "restart_count": 2,
  "error_count": 0
}
```

### 2. `data/open_positions.json` (Position recovery)

```json
{
  "trade_counter": 42,
  "open_positions": [
    {
      "trade_id": "BTC/USDT_42",
      "symbol": "BTC/USDT",
      "entry_price": 42150.75,
      "entry_time": "2026-03-05T14:00:00",
      "quantity": 0.01,
      ...
    }
  ]
}
```

**On restart:**
1. Load `bot_state.json` → restore balance, PnL counters
2. Load `open_positions.json` → tracked open trades
3. Resume trading with all positions managed correctly

---

## 🔔 Telegram Notifications

### Setup

**1. Create Telegram Bot (BotFather)**

```
Chat with @BotFather on Telegram
/newbot
Name: MyAlgoTrader
Username: my_algot

Copy the token: 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
```

**2. Get Your Chat ID**

```
Chat with @userinfobot
Copy the ID: 987654321
```

**3. Update Config**

```json
{
  "notifications": {
    "telegram_enabled": true,
    "telegram_bot_token": "123456:ABC-DEF...",
    "telegram_chat_id": "987654321",
    "notify_on_trade_open": true,
    "notify_on_trade_close": true,
    "notify_hourly_update": true
  }
}
```

**4. Restart**

```bash
docker-compose restart algo-trader
# or
sudo systemctl restart algo-trader
```

### Messages Sent

**Trade Open** 📈
```
📈 Trade Opened
Symbol: BTC/USDT
Direction: LONG
Entry: $42150.75
Stop Loss: $41950.00
Risk: ₹2500.00
TP1: $42789.50
TP2: $43428.25
```

**Hourly Update** ⏰
```
📈 Hourly Update
Time: 14:00 UTC
Balance: ₹10,250.50
Daily P&L: ₹+250.50
Open Positions: 1
Unrealized P&L: ₹+125.00
```

**Daily Summary** 📊
```
📊 Daily Summary
Date: 2026-03-05
Trades: 3
P&L: ₹+250.50
Balance: ₹10,250.50
Max Loss Remaining: ₹2,749.50
```

---

## 🛠️ Advanced Configuration

### Circuit Breakers

In `config.json`, set trading limits:

```json
{
  "risk": {
    "max_loss_day_pct": 3.0,      // Stop if down 3% daily
    "max_loss_week_pct": 6.0,     // Stop if down 6% weekly
    "max_trades_per_day": 5,      // Max 5 trades/day
    "max_open_positions": 2       // Max 2 concurrent trades
  }
}
```

### Strategy Selection

```json
{
  "strategy": {
    "active": "ema_crossover",
    "_available": [
      "ema_crossover",
      "rsi_mean_reversion",
      "opening_range_breakout"
    ]
  }
}
```

### Auto-Scaling Risk

When balance grows by 10%, risk per trade auto-scales:

```json
{
  "scaling": {
    "trigger_pct": 10.0
  }
}
```

Example:
- Start: Balance ₹10,000, Risk ₹25/trade (0.25%)
- Profit: Balance ₹11,000 (10% growth) → Risk ₹27.50/trade

---

## 🔧 Troubleshooting

### Bot Won't Start

```bash
# Check Docker logs
docker-compose logs algo-trader

# Check Systemd logs
sudo journalctl -u algo-trader -n 100

# Check syntax
python3 -m py_compile main.py

# Check imports
python3 -c "from main import *"
```

### API Connection Issues

```bash
# Test credentials
python3 - << 'EOF'
import os
os.environ["BYBIT_API_KEY"] = "your_key"
os.environ["BYBIT_API_SECRET"] = "your_secret"
from core.order_manager import *
om = OrderManager(bybit_exchange)
print(om.fetch_balance())
EOF

# Check rate limits
curl https://api.bybit.com/v3/public/time
```

### Missing Positions on Restart

```bash
# Check state files exist
ls -la data/bot_state.json
ls -la data/open_positions.json

# Verify format
cat data/open_positions.json | python3 -m json.tool
```

### High Memory Usage

```bash
# Check resource limits (Docker)
docker stats algo-trader

# Reduce data history in config
"backtesting": { "days_history": 30 }

# Restart bot
docker-compose restart algo-trader
```

---

## 📈 Monitoring Checklist

**Daily:**
- ✅ Check hourly Telegram summaries
- ✅ Verify error count (should be 0)
- ✅ Monitor balance/PnL trend

**Weekly:**
- ✅ Review bot logs
- ✅ Check disk space used by logs
- ✅ Verify all trades closed properly

**Monthly:**
- ✅ Analyze strategy performance
- ✅ Update risk parameters if needed
- ✅ Rotate archived logs

**Commands:**

```bash
# View recent logs
docker-compose logs algo-trader --tail 100

# Check bot status
docker-compose ps

# Monitor CPU/Memory
docker stats

# View current state  
cat data/bot_state.json | python3 -m json.tool

# Count trades
tail -n +2 logs/trades.csv | wc -l
```

---

## 🚨 Emergency Stop

```bash
# Graceful shutdown (bot saves state)
docker-compose down
# or
sudo systemctl stop algo-trader

# Bot will:
# 1. Stop opening new trades
# 2. Monitor existing positions
# 3. Save state to disk
# 4. Send final summary to Telegram
```

---

## 📝 File Reference

| File | Purpose |
|------|---------|
| `main.py` | Live trading loop with persistence |
| `core/order_manager.py` | Places & tracks real orders |
| `core/position_tracker.py` | Manages open/closed positions |
| `core/risk_manager.py` | Enforces risk rules |
| `utils/notifier.py` | Telegram/webhook notifications |
| `utils/state_manager.py` | Session state persistence |
| `Dockerfile` | Docker container definition |
| `docker-compose.yml` | Multi-container setup |
| `algo-trader.service` | Systemd service file |
| `deploy.sh` | Automated VPS deployment |
| `config.json` | All configuration |

---

## 🎯 Next Steps

1. **Test in paper mode first:**
   ```json
   { "account": { "mode": "paper" } }
   ```
   Run for 1-2 weeks, verify strategy performance.

2. **Setup Telegram notifications:**
   Use bot token + chat ID from BotFather.

3. **Secure API credentials:**
   Use environment variables, never commit to git.

4. **Deploy to production:**
   Use Docker or Systemd (see deployment guide).

5. **Monitor continuously:**
   Check logs, balance, and Telegram alerts daily.

---

## 📞 Support & Debugging

For issues:
1. Check [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
2. Review logs (docker or systemd)
3. Test connectivity to exchange
4. Verify config.json syntax
5. Trace execution step-by-step

---

**🎉 Happy trading! Your 24/7 bot is ready.**
