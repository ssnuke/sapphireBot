#!/bin/bash
#
# quick-start.sh - Start the algo-trader bot with Docker (easiest way)
#
# Usage:
#   chmod +x quick-start.sh
#   ./quick-start.sh
#
# Prerequisites:
#   - Docker installed
#   - docker-compose installed
#   - Bybit API key & secret
#   - (Optional) Telegram bot token

set -e

echo "🤖 Algo Trader — Quick Start with Docker"
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Install from: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed"
    exit 1
fi

echo "✅ Docker found"
echo ""

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file for credentials..."
    cat > .env << EOF
# Exchange API Credentials (REQUIRED for live mode)
BYBIT_API_KEY=
BYBIT_API_SECRET=

# Telegram Notifications (Optional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EOF
    echo "⚠️  Edit .env file before running in LIVE mode"
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Check API credentials for live mode
MODE=$(grep '"mode"' config.json | head -1 | grep -o '"[^"]*"' | tail -1 | tr -d '"')
echo "📋 Current mode: $MODE"

if [ "$MODE" = "live" ]; then
    API_KEY=$(grep BYBIT_API_KEY .env | cut -d'=' -f2)
    API_SECRET=$(grep BYBIT_API_SECRET .env | cut -d'=' -f2)
    
    if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ]; then
        echo "❌ LIVE mode requires API credentials in .env"
        echo "   Edit .env and add your Bybit API key & secret"
        exit 1
    fi
    echo "✅ API credentials configured"
fi

echo ""
echo "🔨 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting bot..."
docker-compose up -d

sleep 2

if docker-compose ps | grep -q "algo-trader.*Up"; then
    echo ""
    echo "✅ Bot is running!"
    echo ""
    echo "📊 View logs (real-time):"
    echo "   docker-compose logs -f algo-trader"
    echo ""
    echo "🛑 Stop bot:"
    echo "   docker-compose down"
    echo ""
    echo "📁 Files:"
    echo "   - Config:    config.json"
    echo "   - Logs:      logs/bot.log"
    echo "   - Trades:    logs/trades.csv"
    echo "   - State:     data/bot_state.json"
    echo "   - Positions: data/open_positions.json"
    echo ""
    echo "🔔 Telegram:"
    if grep -q '"telegram_enabled": true' config.json; then
        echo "   ✅ Enabled - check Telegram for hourly updates"
    else
        echo "   ⏭️  Disabled - edit config.json to enable"
    fi
else
    echo "❌ Bot failed to start"
    docker-compose logs algo-trader
    exit 1
fi
