# 🔍 HeartLink Troubleshooting Guide

## Debug Page Test

I've created a debug page to help diagnose connection issues:

### Step 1: Access the Debug Page

Navigate to: **`/debug`** on your frontend URL

Examples:
- Local: `http://localhost:5173/debug`  
- Ngrok: `https://your-frontend-url.ngrok.io/debug`

### Step 2: Run Connection Test

Click "Run Connection Test" button and observe the logs.

## Common Issues & Solutions

### Issue: "Connection timeout" or "connect_error"

**Symptoms:**
- Button stays on "🔄 Connecting..."
- Debug page shows connection timeout
- Browser console shows WebSocket errors

**Solutions:**

1. **Check backend is running:**
   ```bash
   # Make sure you're running with NO_SSL for ngrok
   ./run_backend_ngrok.sh
   
   # Should see output like:
   # 🚀 Server starting on port 8765 with HTTP
   ```

2. **Check .env file:**
   ```bash
   cat heartlink-app/.env
   
   # Should show:
   # VITE_BACKEND_URL=https://YOUR_BACKEND_NGROK_URL
   ```

3. **Verify ngrok is running:**
   - Check you have BOTH tunnels running
   - Run: `./start_tunnels.sh`
   - You should see 2 forwarding URLs (one for 8765, one for 5173)

4. **Restart Vite dev server:**
   ```bash
   # Stop the frontend (Ctrl+C)
   # Then restart:
   cd heartlink-app
   npm run dev
   ```
   
   **Important:** Vite needs to be restarted after changing `.env` files!

### Issue: "No session_info received"

**Symptoms:**
- Socket connects successfully
- Room join happens
- But no session_info event received

**Solutions:**

1. **Check backend logs:**
   Look for these messages in the terminal running `./run_backend_ngrok.sh`:
   ```
   🚪 User XXX joined room matchmaking
   ✅ User XXX created session YYY as User A
   ```

2. **Backend might have crashed:**
   - Check for Python errors in backend terminal
   - Restart: `./run_backend_ngrok.sh`

3. **Old session data:**
   ```bash
   # Clear old sessions
   ./reset_session.sh
   
   # Then restart backend
   ./run_backend_ngrok.sh
   ```

### Issue: Mixed HTTP/HTTPS errors

**Symptoms:**
- "Mixed content" warnings in console
- "ERR_NGROK_3004"
- Connection attempts fail immediately

**Solutions:**

1. **Backend must run on HTTP when using ngrok:**
   ```bash
   # ❌ WRONG: python app.py (uses HTTPS with SSL certs)
   # ✅ RIGHT: ./run_backend_ngrok.sh (uses HTTP)
   ```

2. **Frontend .env must point to HTTPS ngrok URL:**
   ```bash
   # ❌ WRONG: VITE_BACKEND_URL=http://...
   # ✅ RIGHT: VITE_BACKEND_URL=https://abc123.ngrok.io
   ```

3. **Access frontend via ngrok HTTPS URL:**
   ```bash
   # ❌ WRONG: http://localhost:5173
   # ✅ RIGHT: https://xyz789.ngrok.io (your frontend ngrok URL)
   ```

## Complete Setup Checklist

Use this checklist to verify your setup:

- [ ] ngrok installed and authenticated
- [ ] `.env` file created in `heartlink-app/` with backend ngrok URL
- [ ] ngrok tunnels running (`./start_tunnels.sh`)
- [ ] Backend running in HTTP mode (`./run_backend_ngrok.sh`)
- [ ] Frontend dev server restarted after creating `.env`
- [ ] Accessing via **frontend ngrok URL** (not localhost)

## Step-by-Step Debug Process

### Terminal 1: Start ngrok
```bash
./start_tunnels.sh
```
Note down both URLs:
- Backend (→ 8765): `https://abc123.ngrok.io`
- Frontend (→ 5173): `https://xyz789.ngrok.io`

### Terminal 2: Configure and start backend
```bash
# Make sure to use the backend ngrok URL
echo "Backend URL: https://abc123.ngrok.io"

# Start backend in HTTP mode
./run_backend_ngrok.sh
```

Expected output:
```
🚀 Server starting on port 8765 with HTTP
📱 Local access: http://localhost:8765
```

### Terminal 3: Configure and start frontend
```bash
cd heartlink-app

# Create .env with backend URL (use the one from ngrok output)
echo "VITE_BACKEND_URL=https://abc123.ngrok.io" > .env

# Verify it's correct
cat .env

# Start frontend
npm run dev
```

### Browser: Test connection
1. Open the **frontend ngrok URL**: `https://xyz789.ngrok.io/debug`
2. Click "Run Connection Test"
3. All steps should show ✅ green checkmarks

## Still Having Issues?

### Check Browser Console
1. Open Developer Tools (F12)
2. Go to Console tab
3. Look for:
   - `🔌 Connecting to:` - Shows what URL it's trying to connect to
   - `✅ Connected to backend:` - Should appear within 1-2 seconds
   - `📋 Session info received:` - Should appear after joining room

### Check Backend Logs
Look in the terminal running `./run_backend_ngrok.sh` for:
```
Client connected: <socket_id>
🚪 User <socket_id> joined room matchmaking
✅ User <socket_id> created session <session_id> as User A
```

### Network Tab
1. Open Developer Tools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. Look for:
   - Connection to backend URL
   - Should show "101 Switching Protocols" (success)
   - Click on it to see frames being sent/received

## Quick Fixes

### "Everything was working, now it's not"

```bash
# 1. Kill all processes
# Press Ctrl+C in all terminal windows

# 2. Clear sessions
./reset_session.sh

# 3. Restart everything
# Terminal 1:
./start_tunnels.sh

# Terminal 2:
./run_backend_ngrok.sh

# Terminal 3:
cd heartlink-app
npm run dev

# 4. Access via ngrok frontend URL
```

### "ngrok URLs changed"

Free ngrok generates new URLs each time. When this happens:

```bash
# 1. Stop everything (Ctrl+C in all terminals)

# 2. Start ngrok and note NEW URLs
./start_tunnels.sh

# 3. Update .env with NEW backend URL
cd heartlink-app
echo "VITE_BACKEND_URL=https://NEW_BACKEND_URL" > .env

# 4. Restart backend and frontend
./run_backend_ngrok.sh  # Terminal 2
npm run dev             # Terminal 3 (in heartlink-app/)
```

---

## Contact

If you're still stuck, check:
1. Debug page logs (`/debug`)
2. Browser console (F12 → Console)
3. Backend terminal output
4. ngrok web interface: http://localhost:4040

Include screenshots of these when asking for help!

