#!/bin/bash

echo "🔧 Applying fixes..."
echo ""

# Install flask-cors
echo "📦 Installing Flask-CORS..."
pip install Flask-CORS==4.0.0

echo ""
echo "✅ Fixes applied!"
echo ""
echo "📋 Next steps:"
echo "   1. Restart backend: ./run_backend_ngrok.sh"
echo "   2. Restart frontend: cd heartlink-app && npm run dev"
echo "   3. Hard refresh browser (Cmd+Shift+R)"
echo ""
echo "🐛 Fixed issues:"
echo "   ✅ CORS errors (API calls now work)"
echo "   ✅ MediaRecorder error with video enabled"
echo "   ✅ Added detailed WebRTC logging"
echo ""

