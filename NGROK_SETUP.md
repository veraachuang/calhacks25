# 🌐 NgrokTunnel Setup for HeartLink

This guide helps you expose your HeartLink app via ngrok tunnels to bypass network restrictions and enable video chat functionality.

## Why Use Ngrok?

- **Network restrictions**: Local IP addresses (like 172.x.x.x) may block WebRTC traffic needed for video chat
- **Public access**: Share your app with others without complex network configuration
- **HTTPS support**: Ngrok provides HTTPS URLs which are required for many browser features

## Prerequisites

### 1. Install ngrok

**Option A: Using Homebrew (recommended for macOS)**
```bash
brew install ngrok
```

**Option B: Manual installation**
1. Visit https://ngrok.com/download
2. Download and extract ngrok
3. Move it to your PATH (e.g., `/usr/local/bin/`)

### 2. Sign up and authenticate

1. Create a free account at https://dashboard.ngrok.com/signup
2. Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
3. Authenticate ngrok:
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

## Quick Start

### Step 1: Start the tunnels

Make the tunnel script executable and run it:
```bash
chmod +x start_tunnels.sh
./start_tunnels.sh
```

This will start **both tunnels in a single ngrok process** (free plan limitation):
- Backend tunnel (port 8765)
- Frontend tunnel (port 5173)

### Step 2: Get your ngrok URLs

You'll see output with **two forwarding URLs**:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8765
Forwarding  https://xyz789.ngrok.io -> http://localhost:5173
```

Identify which URL goes to which port:
- The URL pointing to `8765` is your **BACKEND** URL
- The URL pointing to `5173` is your **FRONTEND** URL

### Step 3: Configure the frontend

1. In the `heartlink-app` directory, create a `.env` file:
   ```bash
   cd heartlink-app
   cp .env.example .env
   ```

2. Edit `.env` and add your **backend** ngrok URL:
   ```env
   VITE_BACKEND_URL=https://YOUR_BACKEND_NGROK_URL
   ```
   
   For example:
   ```env
   VITE_BACKEND_URL=https://abc123.ngrok.io
   ```

### Step 4: Start your servers

**Terminal 1: Start the backend (Flask) - Use HTTP mode for ngrok**
```bash
# Option A: Use the helper script
./run_backend_ngrok.sh

# Option B: Set the environment variable manually
NO_SSL=1 python app.py
```

**Note**: When using ngrok, run the backend **without SSL** because ngrok handles HTTPS termination.

**Terminal 2: Start the frontend (Vite)**
```bash
cd heartlink-app
npm run dev
```

### Step 5: Access your app

Use the **frontend** ngrok URL to access your app:
```
https://YOUR_FRONTEND_NGROK_URL
```

Share this URL with others to let them access your app from anywhere!

## Manual Setup (Alternative)

If you prefer to start tunnels manually, use the ngrok config file:

```bash
ngrok start --all --config ngrok.yml
```

This starts both tunnels at once (required for free plan). Then follow steps 2-5 above.

## Troubleshooting

### "ngrok: command not found"
- Make sure ngrok is installed and in your PATH
- Try reinstalling with `brew install ngrok`

### "ERR_NGROK_3004 - Invalid or incomplete HTTP response"
- Your backend is running with SSL but ngrok expects HTTP
- **Solution**: Restart the backend with: `NO_SSL=1 python app.py` or use `./run_backend_ngrok.sh`
- ngrok handles HTTPS termination, so your backend should use HTTP

### "Please sign up or log in"
- You need to authenticate ngrok with your auth token
- Run: `ngrok config add-authtoken YOUR_TOKEN`

### "ERR_NGROK_108 - Limited to 1 simultaneous ngrok agent sessions"
- Free plan allows only 1 ngrok process at a time
- **Solution**: Use the provided `ngrok.yml` config file and run: `ngrok start --all --config ngrok.yml`
- This runs both tunnels from a single process
- The `start_tunnels.sh` script already does this for you

### Video chat still not working
- Make sure you're using the **frontend** ngrok URL (not localhost)
- Verify the `.env` file has the correct **backend** ngrok URL
- Check that both ngrok terminals are still running
- Restart the Vite dev server after changing `.env`

### "Tunnel expired" or slow connection
- Free ngrok tunnels reset URLs periodically
- You'll need to update the `.env` file with new URLs
- Consider upgrading to ngrok Pro for stable URLs

### CORS errors
- The backend is configured with `cors_allowed_origins="*"` which should allow ngrok URLs
- If you still see CORS errors, check that you're using HTTPS URLs (not HTTP)

## Tips

- **Keep terminals open**: Don't close the ngrok terminal windows while using the app
- **New URLs each time**: Free ngrok generates new URLs each time you start a tunnel
- **Share the frontend URL**: Give others the frontend ngrok URL to access your app
- **SSL/HTTPS**: Ngrok automatically provides HTTPS, which is required for video chat
- **Monitor traffic**: Visit http://localhost:4040 to see the ngrok web interface and monitor traffic

## Advanced: ngrok Configuration File

For a more permanent setup, create `~/.ngrok.yml`:

```yaml
version: "2"
authtoken: YOUR_AUTH_TOKEN
tunnels:
  backend:
    proto: http
    addr: 8765
    host_header: localhost:8765
  frontend:
    proto: http
    addr: 5173
    host_header: localhost:5173
```

Then start both tunnels at once:
```bash
ngrok start --all
```

## Cost

- **Free tier**: Perfect for development and testing
  - Random URLs that change each time
  - 1 online ngrok process at a time (you'll need 2, so consider the paid tier or run them sequentially)
  
- **Paid tiers**: Consider upgrading for:
  - Multiple simultaneous tunnels
  - Custom/static domains
  - Faster speeds
  - More connections

Visit https://ngrok.com/pricing for details.

---

## Quick Reference

```bash
# 1. Install and authenticate (one-time setup)
brew install ngrok
ngrok config add-authtoken YOUR_TOKEN

# 2. Start tunnels
./start_tunnels.sh

# 3. Configure frontend
cd heartlink-app
echo "VITE_BACKEND_URL=https://YOUR_BACKEND_NGROK_URL" > .env

# 4. Start servers
python app.py  # In one terminal
cd heartlink-app && npm run dev  # In another terminal

# 5. Access via frontend ngrok URL
```

That's it! Your HeartLink app should now be accessible from anywhere with full video chat support. 🎉

