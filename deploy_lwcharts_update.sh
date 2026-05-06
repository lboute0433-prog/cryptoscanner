#!/bin/bash
# 🚀 UPDATE: Déployer LightweightCharts version sur Hetzner
# Remplace app_local_complete.py par app_lwcharts.py
# Usage: bash deploy_lwcharts_update.sh <server_ip>

set -e

SERVER_IP="${1:-46.225.234.71}"
SERVER_USER="root"
TARGET_PATH="/root/cryptoscanner"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔄 UPDATE: LightweightCharts Version${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📍 Server:${NC} ${SERVER_IP}"
echo -e "${YELLOW}📁 Target:${NC} ${TARGET_PATH}"
echo ""

# Check SSH
echo -e "${BLUE}▶ Vérifying SSH...${NC}"
if ! ssh -o ConnectTimeout=5 "${SERVER_USER}@${SERVER_IP}" "echo 'OK'" &>/dev/null; then
    echo -e "${RED}❌ Cannot connect to ${SERVER_IP}${NC}"
    exit 1
fi
echo -e "${GREEN}✅ SSH OK${NC}"
echo ""

# Check Python syntax locally
echo -e "${BLUE}▶ Vérifying Python syntax...${NC}"
if ! python3 -m py_compile app_lwcharts.py 2>/dev/null; then
    echo -e "${RED}❌ Syntax error in app_lwcharts.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Syntax OK${NC}"
echo ""

# Upload new version
echo -e "${BLUE}▶ Uploading app_lwcharts.py...${NC}"
if ! scp app_lwcharts.py "${SERVER_USER}@${SERVER_IP}:${TARGET_PATH}/app_lwcharts.py"; then
    echo -e "${RED}❌ Upload failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Upload complete${NC}"
echo ""

# Verify syntax on server
echo -e "${BLUE}▶ Vérifying syntax on server...${NC}"
if ! ssh "${SERVER_USER}@${SERVER_IP}" "python3 -m py_compile ${TARGET_PATH}/app_lwcharts.py"; then
    echo -e "${RED}❌ Syntax error on server${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Server syntax OK${NC}"
echo ""

# Backup old version
echo -e "${BLUE}▶ Backing up old version...${NC}"
ssh "${SERVER_USER}@${SERVER_IP}" "cd ${TARGET_PATH} && cp app_local_complete.py app_local_complete.py.backup.$(date +%s)"
echo -e "${GREEN}✅ Backup created${NC}"
echo ""

# Check if PM2 is running
echo -e "${BLUE}▶ Checking PM2...${NC}"
if ! ssh "${SERVER_USER}@${SERVER_IP}" "pm2 status heatmap" &>/dev/null; then
    echo -e "${YELLOW}⚠️  PM2 process 'heatmap' not found${NC}"
    echo "Manual restart needed:"
    echo "  ssh root@${SERVER_IP}"
    echo "  cd ${TARGET_PATH}"
    echo "  pm2 start app_lwcharts.py --name heatmap"
else
    echo -e "${GREEN}✅ PM2 process found${NC}"
fi
echo ""

# Offer to stop/restart
read -p "Stop current process and start new version? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}▶ Stopping old process...${NC}"
    ssh "${SERVER_USER}@${SERVER_IP}" "pm2 stop heatmap || true"
    sleep 2

    echo -e "${BLUE}▶ Starting new version...${NC}"
    ssh "${SERVER_USER}@${SERVER_IP}" "cd ${TARGET_PATH} && pm2 start app_lwcharts.py --name heatmap --interpreter python3"
    sleep 3

    echo -e "${GREEN}✅ Process restarted${NC}"
    echo ""

    echo -e "${BLUE}▶ Checking status...${NC}"
    ssh "${SERVER_USER}@${SERVER_IP}" "pm2 status"
    echo ""

    echo -e "${BLUE}▶ Testing API...${NC}"
    sleep 2
    if curl -s "http://${SERVER_IP}:5000/api/heatmap/all" | grep -q "cryptos"; then
        echo -e "${GREEN}✅ API responding${NC}"
    else
        echo -e "${RED}⚠️  API not responding yet${NC}"
        echo "Check logs: ssh root@${SERVER_IP} 'pm2 logs heatmap'"
    fi
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📊 Dashboard:${NC} http://${SERVER_IP}:5000"
echo -e "${YELLOW}📡 API:${NC} http://${SERVER_IP}:5000/api/heatmap/all"
echo ""
echo "Next steps:"
echo "  1. Verify dashboard in browser: http://${SERVER_IP}:5000"
echo "  2. Test chart interactions (zoom/scroll)"
echo "  3. Monitor logs: ssh root@${SERVER_IP} 'pm2 logs heatmap'"
echo ""
