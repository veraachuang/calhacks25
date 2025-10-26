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

# Start both tunnels using the config file
echo "🔧 Starting both tunnels with ngrok config file..."
ngrok start --all --config ngrok.yml

echo ""
echo "💡 If ngrok exited, you'll see the URLs above"
echo ""
echo "📋 Next steps:"
echo "   1. Look for TWO forwarding URLs in the ngrok output above"
echo "   2. Identify which is backend (→ 8765) and frontend (→ 5173)"
echo "   3. Create a .env file with the BACKEND URL:"
echo "      cd heartlink-app"
echo "      echo 'VITE_BACKEND_URL=https://YOUR_BACKEND_NGROK_URL' > .env"
echo "   4. Start backend: ./run_backend_ngrok.sh"
echo "   5. Start frontend: cd heartlink-app && npm run dev"
echo "   6. Access your app via the FRONTEND ngrok URL"
echo ""
echo "💡 Tip: Keep the ngrok window open while using the app"
echo "🌐 Monitor traffic at: http://localhost:4040"
echo ""

