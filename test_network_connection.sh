#!/bin/bash

# Test Network Connection Script
# This script helps verify the backend is accessible from the network

echo "🔍 Testing HeartLink Network Connectivity"
echo "=========================================="

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -n1 | awk '{print $2}')
echo "📍 Detected local IP: $LOCAL_IP"

# Test backend HTTP endpoint
echo ""
echo "Testing backend API (HTTP)..."
curl -s -o /dev/null -w "Status: %{http_code}\n" http://$LOCAL_IP:8765/api/stats || echo "❌ Failed to connect"

# Test WebSocket connection using wscat (if installed)
if command -v wscat &> /dev/null; then
    echo ""
    echo "Testing WebSocket connection..."
    timeout 3 wscat -c ws://$LOCAL_IP:8765/socket.io/ 2>&1 | head -n 5
else
    echo ""
    echo "💡 Install wscat to test WebSocket: npm install -g wscat"
fi

echo ""
echo "✅ If you see status 200 above, the backend is accessible!"
echo "🌐 Frontend should be at: http://$LOCAL_IP:5173"
echo "🔌 Backend should be at: http://$LOCAL_IP:8765"


