#!/bin/bash
# 🚀 HEATMAP OI+VOLUME — Automated Deployment to Hetzner
# Usage: bash deploy_to_hetzner.sh <server_ip> <target_path>

set -e

# Configuration
SERVER_IP="${1:-46.225.234.71}"
TARGET_PATH="${2:-/root/cryptoscanner}"
SERVER_USER="root"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 HEATMAP OI+VOLUME — DEPLOYMENT TO HETZNER${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📍 Server:${NC} ${SERVER_IP}"
echo -e "${YELLOW}📁 Target:${NC} ${TARGET_PATH}"
echo -e "${YELLOW}👤 User:${NC} ${SERVER_USER}"
echo ""

# Verify SSH connectivity
echo -e "${BLUE}▶ Checking SSH connectivity...${NC}"
if ! ssh -o ConnectTimeout=5 "${SERVER_USER}@${SERVER_IP}" "echo 'SSH OK'" &>/dev/null; then
    echo -e "${RED}❌ Cannot connect to ${SERVER_IP}${NC}"
    echo "Please ensure:"
    echo "  1. Server is online"
    echo "  2. SSH key is configured (~/.ssh/id_rsa)"
    echo "  3. Port 22 is open"
    exit 1
fi
echo -e "${GREEN}✅ SSH connectivity verified${NC}"
echo ""

# Create target directory on server
echo -e "${BLUE}▶ Creating target directory...${NC}"
ssh "${SERVER_USER}@${SERVER_IP}" "mkdir -p ${TARGET_PATH}"
echo -e "${GREEN}✅ Directory ready${NC}"
echo ""

# Upload files via SCP
echo -e "${BLUE}▶ Uploading files to server...${NC}"
FILES=("app_local_complete.py" "heatmap_engine.py" "schema.sql")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  📦 Uploading ${YELLOW}${file}${NC}..."
        scp "$file" "${SERVER_USER}@${SERVER_IP}:${TARGET_PATH}/"
        echo -e "  ${GREEN}✓${NC} ${file}"
    else
        echo -e "  ${RED}✗ File not found: ${file}${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ All files uploaded${NC}"
echo ""

# Verify Python syntax on server
echo -e "${BLUE}▶ Verifying Python syntax on server...${NC}"
ssh "${SERVER_USER}@${SERVER_IP}" "cd ${TARGET_PATH} && python3 -m py_compile app_local_complete.py" && \
    echo -e "${GREEN}✅ Syntax verified${NC}" || \
    { echo -e "${RED}❌ Syntax error in uploaded file${NC}"; exit 1; }
echo ""

# Check if PM2 is installed, install if needed
echo -e "${BLUE}▶ Checking PM2...${NC}"
if ! ssh "${SERVER_USER}@${SERVER_IP}" "which pm2" &>/dev/null; then
    echo -e "  ${YELLOW}⚠ PM2 not found, installing...${NC}"
    ssh "${SERVER_USER}@${SERVER_IP}" "npm install -g pm2"
    echo -e "${GREEN}✅ PM2 installed${NC}"
else
    echo -e "${GREEN}✅ PM2 already installed${NC}"
fi
echo ""

# Stop existing process if running
echo -e "${BLUE}▶ Checking for existing heatmap process...${NC}"
if ssh "${SERVER_USER}@${SERVER_IP}" "pm2 list | grep -q heatmap"; then
    echo -e "  ${YELLOW}⚠ Stopping existing heatmap process...${NC}"
    ssh "${SERVER_USER}@${SERVER_IP}" "pm2 stop heatmap && pm2 delete heatmap"
    echo -e "${GREEN}✅ Process stopped${NC}"
else
    echo -e "${GREEN}✓ No existing process${NC}"
fi
echo ""

# Start application with PM2
echo -e "${BLUE}▶ Starting application with PM2...${NC}"
ssh "${SERVER_USER}@${SERVER_IP}" "cd ${TARGET_PATH} && pm2 start app_local_complete.py --name heatmap --interpreter python3"
echo -e "${GREEN}✅ Application started${NC}"
echo ""

# Save PM2 configuration
echo -e "${BLUE}▶ Saving PM2 configuration...${NC}"
ssh "${SERVER_USER}@${SERVER_IP}" "pm2 save"
echo -e "${GREEN}✅ PM2 configured for auto-restart${NC}"
echo ""

# Wait for application to start
echo -e "${BLUE}▶ Waiting for application to initialize (5 seconds)...${NC}"
sleep 5
echo -e "${GREEN}✓${NC}"
echo ""

# Verify API endpoints
echo -e "${BLUE}▶ Verifying API endpoints...${NC}"
API_RESPONSES=0
for endpoint in "/api/heatmap/all" "/api/heatmap/BTC"; do
    RESPONSE=$(ssh "${SERVER_USER}@${SERVER_IP}" "curl -s -o /dev/null -w '%{http_code}' http://localhost:5000${endpoint}")
    if [ "$RESPONSE" = "200" ]; then
        echo -e "  ${GREEN}✓${NC} ${endpoint}: ${GREEN}${RESPONSE} OK${NC}"
        ((API_RESPONSES++))
    else
        echo -e "  ${RED}✗${NC} ${endpoint}: ${RED}${RESPONSE}${NC}"
    fi
done

if [ $API_RESPONSES -eq 2 ]; then
    echo -e "${GREEN}✅ All API endpoints responding${NC}"
else
    echo -e "${RED}⚠ Some endpoints not responding${NC}"
fi
echo ""

# Show PM2 status
echo -e "${BLUE}▶ Process status:${NC}"
ssh "${SERVER_USER}@${SERVER_IP}" "pm2 status"
echo ""

# Display logs
echo -e "${BLUE}▶ Recent logs:${NC}"
ssh "${SERVER_USER}@${SERVER_IP}" "pm2 logs heatmap --lines 10 --nostream"
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "📊 ${YELLOW}Dashboard${NC}: https://${SERVER_IP}:5000"
echo -e "📡 ${YELLOW}API Endpoints${NC}:"
echo -e "   • https://${SERVER_IP}:5000/api/heatmap/all"
echo -e "   • https://${SERVER_IP}:5000/api/heatmap/<symbol>"
echo ""
echo -e "🔧 ${YELLOW}Useful Commands${NC}:"
echo -e "   • View logs:     ${BLUE}ssh ${SERVER_USER}@${SERVER_IP} 'pm2 logs heatmap'${NC}"
echo -e "   • Stop process:  ${BLUE}ssh ${SERVER_USER}@${SERVER_IP} 'pm2 stop heatmap'${NC}"
echo -e "   • Restart:       ${BLUE}ssh ${SERVER_USER}@${SERVER_IP} 'pm2 restart heatmap'${NC}"
echo -e "   • Delete process:${BLUE}ssh ${SERVER_USER}@${SERVER_IP} 'pm2 delete heatmap'${NC}"
echo ""
echo -e "📝 ${YELLOW}Next Steps${NC}:"
echo -e "   1. Configure nginx reverse proxy (optional)"
echo -e "   2. Set up SSL/TLS certificates"
echo -e "   3. Add rate limiting middleware"
echo -e "   4. Integrate cs_token authentication"
echo ""
