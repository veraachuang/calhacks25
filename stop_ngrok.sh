#!/bin/bash

# Stop all ngrok processes

echo "🔍 Looking for ngrok processes..."

NGROK_PIDS=$(ps aux | grep ngrok | grep -v grep | awk '{print $2}')

if [ -z "$NGROK_PIDS" ]; then
    echo "✅ No ngrok processes running"
    exit 0
fi

echo "Found ngrok processes:"
ps aux | grep ngrok | grep -v grep

echo ""
echo "🛑 Stopping ngrok..."

for PID in $NGROK_PIDS; do
    kill $PID 2>/dev/null
    echo "   Killed PID $PID"
done

sleep 1

# Verify they're gone
REMAINING=$(ps aux | grep ngrok | grep -v grep | wc -l)
if [ $REMAINING -eq 0 ]; then
    echo "✅ All ngrok processes stopped"
else
    echo "⚠️  Some processes still running, forcing kill..."
    killall -9 ngrok 2>/dev/null
    echo "✅ Force killed all ngrok processes"
fi

echo ""
echo "You can now run: ./start_tunnels.sh"

