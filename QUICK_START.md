# 🚀 HeartLink Quick Start (with Auto-Config)

## One-Time Setup

```bash
# 1. Install ngrok
brew install ngrok

# 2. Authenticate ngrok
ngrok config add-authtoken YOUR_TOKEN
```

Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken

## Every Time You Start Development

### Terminal 1: Start ngrok (auto-updates .env)
```bash
./start_tunnels.sh
```

This automatically:
- ✅ Starts both ngrok tunnels (backend + frontend)
- ✅ Extracts the ngrok URLs from the API
- ✅ Updates `heartlink-app/.env` with the backend URL
- ✅ Shows you the frontend URL to access

### Terminal 2: Start backend
```bash
./run_backend_ngrok.sh
```

### Terminal 3: Start frontend
```bash
cd heartlink-app
npm run dev
```

### Browser: Access the app
Use the **frontend ngrok URL** shown in Terminal 1 output.

## If ngrok URLs Change

ngrok free tier generates new URLs each time. When they change:

```bash
# Just run this script:
./update_ngrok_env.sh

# Then restart the frontend (Ctrl+C, then npm run dev)
cd heartlink-app
npm run dev
```

The script automatically:
- Fetches current ngrok URLs from the API
- Updates `.env` with the new backend URL
- Shows you the new frontend URL

## Manual .env Update (if needed)

If the auto-update script doesn't work, manually create:

```bash
cd heartlink-app
echo "VITE_BACKEND_URL=https://YOUR_BACKEND_NGROK_URL" > .env
```

**Important**: Always restart the Vite dev server after changing `.env`!

## Troubleshooting

### "Could not find backend tunnel"
The auto-update script queries ngrok's API at `http://localhost:4040`. If this fails:
1. Check ngrok is running: `curl http://localhost:4040/api/tunnels`
2. Or manually update the `.env` file (see above)

### "Changes not working"
You **must restart** the Vite dev server after `.env` changes:
```bash
# In the heartlink-app terminal, press Ctrl+C then:
npm run dev
```

### View ngrok URLs
```bash
# View ngrok web interface:
open http://localhost:4040

# Or query the API:
curl -s http://localhost:4040/api/tunnels | jq
```

## Summary

**Fully automatic workflow:**
```bash
# Terminal 1
./start_tunnels.sh   # Auto-updates .env ✨

# Terminal 2  
./run_backend_ngrok.sh

# Terminal 3
cd heartlink-app && npm run dev

# Browser
# Use frontend ngrok URL from Terminal 1
```

That's it! 🎉

