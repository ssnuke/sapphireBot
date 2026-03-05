#!/bin/bash
#
# deploy.sh - Deploy the algo-trader bot on a Linux VPS
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh  [ paper | live ]
#
# This script:
#   1. Creates a system user 'algo'
#   2. Clones/pulls the repo
#   3. Sets up Python venv
#   4. Installs dependencies
#   5. Configures systemd service
#   6. Optionally enables Telegram notifications
#   7. Starts the bot

set -e

MODE="${1:-paper}"
BOT_HOME="/home/algo/algo_trader"
VENV="$BOT_HOME/venv"
SERVICE_NAME="algo-trader"

echo "🚀 Deploying Algo Trader Bot in $MODE mode..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
  echo "❌ This script must be run as root (use sudo)"
  exit 1
fi

# 1. Create algo user if not exists
if ! id -u algo > /dev/null 2>&1; then
  echo "👤 Creating system user 'algo'..."
  useradd -m -s /bin/bash -d /home/algo algo
fi

# 2. Create bot directory
mkdir -p "$BOT_HOME"
chown -R algo:algo /home/algo

# 3. Clone or pull the repo
echo "📦 Setting up repository..."
if [ -d "$BOT_HOME/.git" ]; then
  cd "$BOT_HOME"
  echo "Pulling latest changes..."
  sudo -u algo git pull origin main
else
  echo "Cloning repository..."
  # If you have a private repo, use SSH (requires key setup)
  cd /home/algo
  sudo -u algo git clone https://github.com/yourusername/algo_trader.git
fi

cd "$BOT_HOME"

# 4. Create Python venv
echo "🐍 Setting up Python virtual environment..."
if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
  chown -R algo:algo "$VENV"
fi

# 5. Install dependencies
echo "📚 Installing dependencies..."
sudo -u algo "$VENV/bin/pip" install --upgrade pip
sudo -u algo "$VENV/bin/pip" install -r requirements.txt

# 6. Create necessary directories
echo "📁 Creating data/logs directories..."
mkdir -p "$BOT_HOME/data/cache"
mkdir -p "$BOT_HOME/logs"
mkdir -p "$BOT_HOME/results"
chown -R algo:algo "$BOT_HOME/data" "$BOT_HOME/logs" "$BOT_HOME/results"

# 7. Configure mode in config.json
echo "⚙️  Setting bot mode to '$MODE'..."
if [ "$MODE" = "live" ]; then
  echo "⚠️  LIVE MODE ENABLED"
  sed -i 's/"mode": "paper"/"mode": "live"/' "$BOT_HOME/config.json"
else
  sed -i 's/"mode": "live"/"mode": "paper"/' "$BOT_HOME/config.json"
fi

# 8. Setup Telegram notifications (optional)
echo ""
echo "🔔 Setup Telegram notifications? (optional)"
read -p "Enter Telegram bot token (or press Enter to skip): " BOT_TOKEN
if [ -n "$BOT_TOKEN" ]; then
  read -p "Enter Telegram chat ID (your Telegram ID): " CHAT_ID
  # Update config.json
  sed -i "s/\"telegram_bot_token\": \"\"/\"telegram_bot_token\": \"$BOT_TOKEN\"/" "$BOT_HOME/config.json"
  sed -i "s/\"telegram_chat_id\": \"\"/\"telegram_chat_id\": \"$CHAT_ID\"/" "$BOT_HOME/config.json"
  sed -i 's/"telegram_enabled": false/"telegram_enabled": true/' "$BOT_HOME/config.json"
  echo "✅ Telegram configured"
else
  echo "⏭️  Telegram skipped"
fi

# 9. Setup API credentials via environment
echo ""
echo "🔐 Setup exchange API credentials..."
read -p "Enter Bybit API key (or press Enter to skip): " API_KEY
if [ -n "$API_KEY" ]; then
  read -p "Enter Bybit API secret: " API_SECRET
  
  # Create systemd environment file
  mkdir -p /etc/algo-trader
  cat > /etc/algo-trader/env << EOF
BYBIT_API_KEY=$API_KEY
BYBIT_API_SECRET=$API_SECRET
EOF
  chmod 600 /etc/algo-trader/env
  echo "✅ Credentials saved securely"
else
  echo "⏭️  Credentials not configured (use config.json instead)"
fi

# 10. Install systemd service
echo ""
echo "🔧 Installing systemd service..."
cp "$BOT_HOME/algo-trader.service" /etc/systemd/system/algo-trader.service

# Update systemd service to source env file if it exists
if [ -f /etc/algo-trader/env ]; then
  sed -i '/^\[Service\]/a EnvironmentFile=/etc/algo-trader/env' /etc/systemd/system/algo-trader.service
fi

systemctl daemon-reload
systemctl enable algo-trader

# 11. Create log rotation
echo "📋 Setting up log rotation..."
cat > /etc/logrotate.d/algo-trader << EOF
/home/algo/algo_trader/logs/*.log {
  daily
  rotate 7
  compress
  delaycompress
  notifempty
  create 0640 algo algo
  sharedscripts
  postrotate
    systemctl reload algo-trader > /dev/null 2>&1 || true
  endscript
}
EOF

# 12. Test the setup
echo ""
echo "✅ Testing bot installation..."
cd "$BOT_HOME"
"$VENV/bin/python3" -c "from utils.config_loader import load_config; load_config(); print('✅ Config loads OK')"

# 13. Start the service
echo ""
echo "🚀 Starting the bot service..."
systemctl start algo-trader
sleep 2

if systemctl is-active --quiet algo-trader; then
  echo "✅ Bot is running!"
  echo ""
  echo "📊 View logs:"
  echo "  tail -f /var/log/algo-trader/bot.log"
  echo ""
  echo "🛑 Stop bot:"
  echo "  sudo systemctl stop algo-trader"
  echo ""
  echo "📝 Restart bot:"
  echo "  sudo systemctl restart algo-trader"
  echo ""
  echo "✉️  Status:"
  echo "  sudo systemctl status algo-trader"
else
  echo "❌ Bot failed to start. Check logs:"
  systemctl status algo-trader
  exit 1
fi

echo ""
echo "🎉 Deployment complete!"
