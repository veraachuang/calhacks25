#!/bin/bash
# Quick reset script for testing

echo "🗑️  Resetting matchmaking session..."
curl -X DELETE -k https://localhost:8765/api/sessions/matchmaking/reset 2>/dev/null

echo ""
echo "✅ Session reset!"
echo ""
echo "📋 Current status:"
curl -s -k https://localhost:8765/api/sessions/matchmaking 2>/dev/null | python3 -m json.tool || echo "No matchmaking session exists (ready for testing!)"
echo ""
echo "🎬 Now open TWO fresh browser windows and test!"


