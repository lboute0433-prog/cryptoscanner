#!/bin/bash
# 🔍 HEATMAP — Production Deployment Verification
# Usage: bash verify_deployment.sh <server_ip>

SERVER_IP="${1:-46.225.234.71}"
SERVER_USER="root"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔍 HEATMAP DEPLOYMENT VERIFICATION${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""

# 1. SSH Connectivity
echo -e "${BLUE}1️⃣  SSH Connectivity${NC}"
if ssh -o ConnectTimeout=5 "${SERVER_USER}@${SERVER_IP}" "echo 'OK'" &>/dev/null; then
    echo -e "   ${GREEN}✅ SSH connection successful${NC}"
else
    echo -e "   ${RED}❌ Cannot connect via SSH${NC}"
    exit 1
fi
echo ""

# 2. Process Status
echo -e "${BLUE}2️⃣  PM2 Process Status${NC}"
PM2_STATUS=$(ssh "${SERVER_USER}@${SERVER_IP}" "pm2 list 2>/dev/null | grep heatmap")
if [ ! -z "$PM2_STATUS" ]; then
    echo -e "   ${GREEN}✅ Heatmap process found${NC}"
    ssh "${SERVER_USER}@${SERVER_IP}" "pm2 status | grep heatmap"
else
    echo -e "   ${YELLOW}⚠ Heatmap process not running${NC}"
fi
echo ""

# 3. API Endpoint Tests
echo -e "${BLUE}3️⃣  API Endpoint Tests${NC}"

# Test /api/heatmap/all
echo -n "   Testing /api/heatmap/all... "
RESPONSE=$(ssh "${SERVER_USER}@${SERVER_IP}" "curl -s -w '%{http_code}' http://localhost:5000/api/heatmap/all -o /tmp/heatmap_response.json")
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
    DATA=$(ssh "${SERVER_USER}@${SERVER_IP}" "cat /tmp/heatmap_response.json | head -100")
    echo -e "   Sample: ${YELLOW}${DATA:0:80}...${NC}"
else
    echo -e "${RED}❌ HTTP ${RESPONSE}${NC}"
fi

# Test /api/heatmap/<symbol>
echo -n "   Testing /api/heatmap/BTC... "
RESPONSE=$(ssh "${SERVER_USER}@${SERVER_IP}" "curl -s -w '%{http_code}' http://localhost:5000/api/heatmap/BTC -o /tmp/btc_response.json")
if [ "$RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ 200 OK${NC}"
else
    echo -e "${RED}❌ HTTP ${RESPONSE}${NC}"
fi
echo ""

# 4. Port Status
echo -e "${BLUE}4️⃣  Port Status${NC}"
if ssh "${SERVER_USER}@${SERVER_IP}" "netstat -tuln 2>/dev/null | grep -q 5000 || ss -tuln 2>/dev/null | grep -q 5000"; then
    echo -e "   ${GREEN}✅ Port 5000 listening${NC}"
else
    echo -e "   ${YELLOW}⚠ Port 5000 status unknown${NC}"
fi
echo ""

# 5. File Verification
echo -e "${BLUE}5️⃣  File Verification${NC}"
FILES=("app_local_complete.py" "heatmap_engine.py" "schema.sql")
for file in "${FILES[@]}"; do
    if ssh "${SERVER_USER}@${SERVER_IP}" "test -f /root/cryptoscanner/$file"; then
        SIZE=$(ssh "${SERVER_USER}@${SERVER_IP}" "wc -c < /root/cryptoscanner/$file")
        echo -e "   ${GREEN}✅${NC} ${file} (${SIZE} bytes)"
    else
        echo -e "   ${RED}❌${NC} ${file} missing"
    fi
done
echo ""

# 6. Python Dependencies
echo -e "${BLUE}6️⃣  Python Dependencies${NC}"
echo -n "   Checking Flask... "
if ssh "${SERVER_USER}@${SERVER_IP}" "python3 -c 'import flask' 2>/dev/null"; then
    echo -e "${GREEN}✅ Available${NC}"
else
    echo -e "${RED}❌ Missing${NC}"
fi
echo ""

# 7. Recent Logs
echo -e "${BLUE}7️⃣  Recent Logs (last 5 lines)${NC}"
ssh "${SERVER_USER}@${SERVER_IP}" "pm2 logs heatmap --lines 5 --nostream" 2>/dev/null || echo "   (Logs not available)"
echo ""

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ VERIFICATION COMPLETE${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "🌐 Access points:"
echo -e "   • API:      ${YELLOW}http://${SERVER_IP}:5000/api/heatmap/all${NC}"
echo -e "   • Dashboard:${YELLOW}http://${SERVER_IP}:5000${NC}"
echo ""
