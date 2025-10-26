#!/bin/bash

# HeartLink Tunnel Setup Script
# This script helps you expose your local services via ngrok

echo "🌐 HeartLink Tunnel Setup"
echo "=========================="
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok is not installed!"
    echo ""
    echo "📦 Install ngrok:"
    echo "   1. Visit: https://ngrok.com/download"
    echo "   2. Or use Homebrew: brew install ngrok"
    echo "   3. Sign up at: https://dashboard.ngrok.com/signup"
    echo "   4. Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "   5. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

echo "✅ ngrok is installed"
echo ""

# Check if ngrok config exists
if ! ngrok config check &> /dev/null; then
    echo "⚠️  ngrok is not authenticated"
    echo ""
    echo "🔑 To authenticate:"
    echo "   1. Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "   2. Run: ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    exit 1
fi

echo "🚀 Starting ngrok tunnels..."
echo ""
echo "📝 Note: This will start BOTH tunnels in a single ngrok process"
echo "   - Backend tunnel (port 8765)"
echo "   - Frontend tunnel (port 5173)"
echo ""

# Start both tunnels using the config file in background
echo "🔧 Starting both tunnels with ngrok config file..."
echo ""

# Run ngrok in background
ngrok start --all --config ngrok.yml > /dev/null 2>&1 &
NGROK_PID=$!

echo "⏳ Waiting for ngrok to initialize..."
sleep 3

# Check if ngrok is running
if ! kill -0 $NGROK_PID 2>/dev/null; then
    echo "❌ Error: ngrok failed to start"
    echo ""
    echo "Try running manually to see the error:"
    echo "  ngrok start --all --config ngrok.yml"
    exit 1
fi

echo "✅ ngrok started (PID: $NGROK_PID)"
echo ""

# Automatically update .env file
echo "🔄 Auto-updating .env file with ngrok URLs..."
./update_ngrok_env.sh

echo "📋 Next steps:"
echo "   1. Start backend: ./run_backend_ngrok.sh"
echo "   2. Start frontend: cd heartlink-app && npm run dev"
echo "   3. Access your app via the FRONTEND ngrok URL shown above"
echo ""
echo "💡 Tips:"
echo "   - ngrok is running in background (PID: $NGROK_PID)"
echo "   - Monitor traffic at: http://localhost:4040"
echo "   - If ngrok URLs change, run: ./update_ngrok_env.sh"
echo "   - To stop ngrok: kill $NGROK_PID"
echo ""

