#!/bin/bash

HOST="46.225.234.71"
PORT="5000"
BASE_URL="http://$HOST:$PORT"

echo "Testing with CORRECT endpoint paths..."
echo ""

# Test new paths
echo "1. Funding Rates Endpoint:"
curl -s "$BASE_URL/api/institutional-flows/funding-rates" -w "\nStatus: %{http_code}\n" 2>&1 | head -5

echo ""
echo "2. Correlations Matrix:"
curl -s "$BASE_URL/api/correlations/matrix" -w "\nStatus: %{http_code}\n" 2>&1 | head -5

echo ""
echo "3. Correlations Clusters:"
curl -s "$BASE_URL/api/correlations/clusters" -w "\nStatus: %{http_code}\n" 2>&1 | head -5

echo ""
echo "4. Admin Alerts Config (GET - check all):"
curl -s "$BASE_URL/api/admin/alerts/config" -w "\nStatus: %{http_code}\n" 2>&1 | head -10

echo ""
echo "5. Smart Signals endpoint (to verify score_min):"
curl -s "$BASE_URL/api/smart_signals" | python3 -m json.tool 2>/dev/null | head -20

