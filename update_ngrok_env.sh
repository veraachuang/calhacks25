#!/bin/bash

# Script to automatically update .env with current ngrok backend URL
# Run this after starting ngrok tunnels

echo "🔍 Fetching current ngrok URLs..."
echo ""

# Check if ngrok is running
if ! curl -s http://localhost:4040/api/tunnels &> /dev/null; then
    echo "❌ Error: ngrok is not running or API is not accessible"
    echo ""
    echo "Please start ngrok first:"
    echo "  ./start_tunnels.sh"
    echo ""
    exit 1
fi

# Fetch tunnel info from ngrok API
TUNNELS_JSON=$(curl -s http://localhost:4040/api/tunnels)

# Extract backend URL (the one pointing to port 8765)
BACKEND_URL=$(echo "$TUNNELS_JSON" | grep -o '"public_url":"https://[^"]*"' | grep -o 'https://[^"]*' | while read url; do
    # Check if this tunnel points to 8765
    CONFIG=$(echo "$TUNNELS_JSON" | grep -A 20 "\"public_url\":\"$url\"")
    if echo "$CONFIG" | grep -q '"addr":".*:8765"' || echo "$CONFIG" | grep -q '"addr":"http://localhost:8765"'; then
        echo "$url"
        break
    fi
done)

# Extract frontend URL (the one pointing to port 5173)
FRONTEND_URL=$(echo "$TUNNELS_JSON" | grep -o '"public_url":"https://[^"]*"' | grep -o 'https://[^"]*' | while read url; do
    # Check if this tunnel points to 5173
    CONFIG=$(echo "$TUNNELS_JSON" | grep -A 20 "\"public_url\":\"$url\"")
    if echo "$CONFIG" | grep -q '"addr":".*:5173"' || echo "$CONFIG" | grep -q '"addr":"http://localhost:5173"'; then
        echo "$url"
        break
    fi
done)

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Could not find backend tunnel (port 8765)"
    echo ""
    echo "Available tunnels:"
    echo "$TUNNELS_JSON" | grep -o '"public_url":"https://[^"]*"' | sed 's/"public_url":"//;s/"//'
    echo ""
    exit 1
fi

echo "✅ Found ngrok URLs:"
echo "   Backend (8765):  $BACKEND_URL"
echo "   Frontend (5173): $FRONTEND_URL"
echo ""

# Update .env file
ENV_FILE="heartlink-app/.env"
echo "📝 Updating $ENV_FILE..."

# Create or overwrite .env file
echo "VITE_BACKEND_URL=$BACKEND_URL" > "$ENV_FILE"

echo "✅ Updated $ENV_FILE"
echo ""
echo "📋 Contents:"
cat "$ENV_FILE"
echo ""
echo "⚠️  IMPORTANT: Restart your Vite dev server for changes to take effect!"
echo ""
echo "   cd heartlink-app"
echo "   # Press Ctrl+C to stop the current server"
echo "   npm run dev"
echo ""
echo "🌐 Access your app at: $FRONTEND_URL"
echo ""

