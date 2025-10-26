#!/bin/bash

# Run Flask backend without SSL (for use with ngrok)
# ngrok handles HTTPS termination, so the backend should use HTTP

echo "🚀 Starting Flask backend for ngrok (HTTP mode)"
echo "================================================"
echo ""
echo "ℹ️  Running without SSL - ngrok will handle HTTPS"
echo ""

export NO_SSL=1
python server.py


