#!/bin/bash
set -e

HOSTNAME="46.225.234.71"
USERNAME="root"

echo "Deploying RSI fixes to $HOSTNAME..."

# Copy files via SCP (requires SSH key setup)
scp -q rsi_engine.py root@$HOSTNAME:/app/rsi_engine.py || {
    echo "❌ SCP failed - checking SSH key..."
    ssh-keyscan -H $HOSTNAME >> ~/.ssh/known_hosts 2>/dev/null || true
    scp rsi_engine.py root@$HOSTNAME:/app/rsi_engine.py
}

echo "✓ rsi_engine.py deployed"

# Get app.py size
APP_SIZE=$(wc -c < app.py)
echo "📤 Deploying app.py ($APP_SIZE bytes)..."
scp -q app.py root@$HOSTNAME:/app/app.py
echo "✓ app.py deployed"

# Restart service
echo "🔄 Restarting service..."
ssh root@$HOSTNAME "sudo systemctl restart cryptoscanner"
sleep 2

# Check service status
echo "📋 Service status..."
ssh root@$HOSTNAME "sudo systemctl status cryptoscanner --no-pager" || true

# Get last 10 logs
echo "📋 Recent logs..."
ssh root@$HOSTNAME "sudo journalctl -u cryptoscanner -n 10 --no-pager"

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo "Heatmap cache warmer should now be running in background..."
