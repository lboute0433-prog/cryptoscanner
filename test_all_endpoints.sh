#!/bin/bash

HOST="46.225.234.71"
PORT="5000"
BASE_URL="http://$HOST:$PORT"

echo "==============================================="
echo "TESTING ALL CRYPTOSCANNER ENDPOINTS"
echo "==============================================="
echo ""

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name ... "
    response=$(curl -s "$url" -w "\n%{http_code}" 2>&1 | tail -1)
    
    if [[ "$response" == "200" ]]; then
        echo "✅ 200 OK"
        return 0
    elif [[ "$response" == "401" ]]; then
        echo "⚠️  401 (Auth required - normal)"
        return 0
    elif [[ "$response" == "405" ]]; then
        echo "⚠️  405 (Method not allowed - try POST)"
        return 0
    else
        echo "❌ $response"
        return 1
    fi
}

echo "📊 MARKET DATA ENDPOINTS:"
test_endpoint "Market" "$BASE_URL/api/market"
test_endpoint "Signals" "$BASE_URL/api/signals"
test_endpoint "Smart Signals" "$BASE_URL/api/smart_signals"
test_endpoint "News" "$BASE_URL/api/news"
test_endpoint "Whales" "$BASE_URL/api/whales"
test_endpoint "Macro" "$BASE_URL/api/macro/all"

echo ""
echo "📈 VISUALIZATION ENDPOINTS:"
test_endpoint "RSI Heatmap" "$BASE_URL/api/heatmap/scatter"
test_endpoint "COT Data" "$BASE_URL/api/cot/btc"
test_endpoint "Liquidations" "$BASE_URL/api/liquidations"
test_endpoint "Funding Rates" "$BASE_URL/api/funding"

echo ""
echo "🔐 AUTH-PROTECTED ENDPOINTS:"
test_endpoint "Watchlist" "$BASE_URL/api/watchlist"
test_endpoint "Portfolio" "$BASE_URL/api/portfolio"
test_endpoint "Correlations" "$BASE_URL/api/correlations"

echo ""
echo "📋 ADMIN ENDPOINTS:"
curl -s -X GET "$BASE_URL/api/admin/alerts/config/smart_signals" -w "\n%{http_code}" 2>&1 | tail -1 > /tmp/admin_test.txt
admin_code=$(cat /tmp/admin_test.txt)
echo -n "Testing Admin Alerts Config ... "
if [[ "$admin_code" == "200" ]]; then
    echo "✅ 200 OK"
elif [[ "$admin_code" == "401" ]]; then
    echo "⚠️  401 (Auth required - normal)"
else
    echo "❌ $admin_code"
fi

echo ""
echo "==============================================="
echo "ENDPOINT TEST COMPLETE"
echo "==============================================="
