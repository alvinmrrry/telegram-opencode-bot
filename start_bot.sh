#!/bin/bash

# Telegram OpenCode Bot Startup Script

BOT_SCRIPT="/Users/jiancao/telegram_opencode_bot.py"
LOG_FILE="/tmp/telegram_bot.log"
NGROK_LOG="/tmp/ngrok.log"
PORT=8080

echo "Starting Telegram OpenCode Bot..."

# Kill existing processes
pkill -f ngrok 2>/dev/null
pkill -f telegram_opencode_bot.py 2>/dev/null
sleep 1

# Start ngrok
echo "Starting ngrok..."
nohup ngrok http $PORT > $NGROK_LOG 2>&1 &
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s localhost:4040/api/tunnels | python3 -c "import sys,json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
echo "ngrok URL: $NGROK_URL"

# Set Telegram webhook
TOKEN="8134791400:AAGP4mWwbiQbDH4HKbNBFQcUUZpfySrQR1c"
if [ -n "$NGROK_URL" ]; then
    echo "Setting Telegram webhook..."
    curl -s -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" -d "url=${NGROK_URL}/webhook"
    echo "Webhook set to: ${NGROK_URL}/webhook"
fi

# Start bot
echo "Starting bot..."
nohup python3 $BOT_SCRIPT > $LOG_FILE 2>&1 &
sleep 2

# Check status
echo ""
echo "=== Status ==="
echo "ngrok: $(pgrep -f ngrok > /dev/null && echo 'Running' || echo 'Stopped')"
echo "Bot: $(pgrep -f telegram_opencode_bot.py > /dev/null && echo 'Running' || echo 'Stopped')"
echo "Bot log: tail -f $LOG_FILE"
echo "ngrok log: tail -f $NGROK_LOG"
