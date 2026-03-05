# Algo Trader — Live Deployment Guide

## Overview

This guide covers deploying the algo-trader bot for **24/7 live trading** on a Linux VPS or your own server.

---

## 📋 Prerequisites

- **Linux VPS** (Ubuntu 20.04+ recommended)
- **Python 3.9+** installed
- **Git** installed
- **API credentials** for Bybit (or your exchange)
- **Telegram bot token** (optional, for notifications)

---

## 🚀 Quick Deployment

### Option 1: Using Systemd (Recommended for VPS)

```bash
# SSH into your VPS
ssh user@your_vps_ip

# Clone the repo
git clone https://github.com/yourusername/algo_trader.git
cd algo_trader

# Run deployment script
chmod +x deploy.sh
sudo ./deploy.sh live
```

The script will:
1. ✅ Create a system user `algo`
2. ✅ Setup Python venv
3. ✅ Install dependencies
4. ✅ Configure systemd service
5. ✅ Setup Telegram notifications
6. ✅ Save API credentials securely
7. ✅ Start the bot

### Option 2: Using Docker (Best for Isolation)

```bash
# On your VPS
cd /home/user/algo_trader

# Create .env file with credentials
cat > .env << EOF
BYBIT_API_KEY=your_api_key_here
BYBIT_API_SECRET=your_api_secret_here
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
EOF

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f algo-trader

# Stop bot
docker-compose down
```

---

## 🔐 Security Best Practices

### 1. **Protect API Credentials**

Never commit API keys to git:

```bash
# Use environment variables
export BYBIT_API_KEY="your_key_here"
export BYBIT_API_SECRET="your_secret_here"

# Or systemd
sudo /etc/algo-trader/env
```

### 2. **File Permissions**

```bash
# Run bot as non-root user
sudo useradd -m algo
sudo chown -R algo:algo /home/algo/algo_trader
sudo chmod 600 /etc/algo-trader/env  # Credentials file
```

### 3. **Firewall**

```bash
# Only allow SSH (port 22)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw enable
```

### 4. **Monitoring**

```bash
# Monitor bot availability
curl -s http://localhost:8000/health  # If you add a health endpoint
```

---

## 📊 Viewing Logs

### Systemd Service

```bash
# Real-time logs
sudo tail -f /var/log/algo-trader/bot.log

# Full logs
sudo journalctl -u algo-trader -f

# Recent errors
sudo journalctl -u algo-trader --since "1 hour ago" --no-pager
```

### Docker

```bash
# Real-time logs
docker-compose logs -f algo-trader

# Last 50 lines
docker-compose logs --tail=50 algo-trader
```

---

## ⚙️ Managing the Bot

### Start/Stop/Restart (Systemd)

```bash
# Start
sudo systemctl start algo-trader

# Stop (graceful shutdown)
sudo systemctl stop algo-trader

# Restart
sudo systemctl restart algo-trader

# Check status
sudo systemctl status algo-trader

# Enable auto-start on reboot
sudo systemctl enable algo-trader
```

### Start/Stop (Docker)

```bash
# Start in background
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart algo-trader
```

---

## 📝 Configuration & Updates

### Update Bot Code

```bash
cd /home/algo/algo_trader
git pull origin main
sudo systemctl restart algo-trader
```

### Change Strategy or Risk Settings

```bash
# Edit config.json
nano /home/algo/algo_trader/config.json

# Apply changes
sudo systemctl restart algo-trader
```

### Enable Live Trading

In `config.json`:
```json
{
  "account": {
    "mode": "paper"  ← Change to "live"
  }
}
```

Then restart:
```bash
sudo systemctl restart algo-trader
```

---

## 🔔 Telegram Notifications

### Setup

In `config.json`:
```json
{
  "notifications": {
    "telegram_enabled": true,
    "telegram_bot_token": "YOUR_BOT_TOKEN",
    "telegram_chat_id": "YOUR_CHAT_ID",
    "notify_hourly_update": true
  }
}
```

### Get Your Telegram Info

1. **Create a bot:**
   - Chat with @BotFather on Telegram
   - Create a new bot
   - Copy the **bot token**

2. **Get your chat ID:**
   - Chat with @userinfobot
   - Copy the **ID** shown

3. **Update config and restart:**
   ```bash
   sudo systemctl restart algo-trader
   ```

---

## 🚨 Troubleshooting

### Bot Won't Start

```bash
# Check error
sudo systemctl status algo-trader

# View recent errors
sudo journalctl -u algo-trader -n 50 --no-pager
```

### API Connection Issues

```bash
# Check credentials
echo $BYBIT_API_KEY  # Should show your key

# Test connection
cd /home/algo/algo_trader
python3 -c "from core.order_manager import *; print('Import OK')"
```

### Out of Memory

```bash
# Check memory usage
docker stats  # If using Docker
free -h       # System memory

# Increase limit in compose file
docker-compose.yml → services → algo-trader → deploy → resources
```

### Logs Not Updating

```bash
# Check file permissions
ls -la /home/algo/algo_trader/logs/

# Ensure algo user can write
sudo chown algo:algo /home/algo/algo_trader/logs/
```

---

## 📈 Monitoring & Alerting

### Log Rotation

Logs are rotated daily (keep 7 days of history):
```bash
ls -la /home/algo/algo_trader/logs/
```

### Disk Space

```bash
# Check available space
df -h /home/algo

# Clean old results (keep last 30 days)
find /home/algo/algo_trader/results -name "*.json" -mtime +30 -delete
```

### CPU & Memory

```bash
# Monitor in real-time
watch -n 1 'ps aux | grep python3 | grep main.py'

# Check resource limits
systemctl show algo-trader -p MemoryLimit
```

---

## 🔄 Recovery & Persistence

The bot **automatically persists state** to `data/bot_state.json` and `data/open_positions.json`. On restart:

1. ✅ Loads open positions
2. ✅ Resumes daily PnL tracking
3. ✅ Continues trading with risk rules applied

```bash
# View current state
cat /home/algo/algo_trader/data/bot_state.json | python3 -m json.tool
```

---

## 🛑 Graceful Shutdown

The bot handles signals gracefully:

```bash
# Ctrl+C or:
sudo systemctl stop algo-trader

# Bot will:
# 1. Stop opening new trades
# 2. Save current state
# 3. Send final summary to Telegram
# 4. Exit cleanly without losing position data
```

---

## 📞 Support

For issues:
1. Check logs: `sudo journalctl -u algo-trader -f`
2. Test in paper mode first
3. Verify API credentials
4. Check Telegram setup
5. Review config.json syntax

---

## 🎉 You're Done!

Your bot is now running **24/7 on your VPS**. It will:

- ✅ Trade continuously **every candle close**
- ✅ Enforce risk rules and circuit breakers
- ✅ Save state and recover on restart
- ✅ Send **hourly summaries** to Telegram
- ✅ Handle network errors with retries
- ✅ Auto-scale risk as balance grows

Monitor via Telegram or check logs anytime.
