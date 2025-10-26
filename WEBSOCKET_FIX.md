# WebSocket Connection Fix

## The Problem
- Frontend at `http://localhost:5173` or `http://172.20.10.8:5173` 
- Backend at `https://localhost:8765` or `https://172.20.10.8:8765` (HTTPS with self-signed cert)
- Browser blocks connection due to self-signed certificate

## The Solution

### Step 1: Accept the Self-Signed Certificate (REQUIRED)

**Before the frontend can connect**, you MUST visit the backend URL in your browser and accept the security warning:

#### For localhost:
1. Open a new browser tab
2. Visit: `https://localhost:8765`
3. You'll see a security warning
4. Click "Advanced" → "Proceed to localhost (unsafe)" or similar
5. You should see JSON data (the API stats)

#### For network access (172.20.10.8):
1. Open a new browser tab
2. Visit: `https://172.20.10.8:8765`
3. Accept the security warning
4. You should see JSON data

### Step 2: Verify Backend Connection

After accepting the certificate, test the connection:

```bash
# Test localhost
curl -k https://localhost:8765/api/stats

# Test network IP
curl -k https://172.20.10.8:8765/api/stats
```

Both should return JSON with session statistics.

### Step 3: Reload Your Frontend

After accepting the certificate, refresh your frontend page:
- `http://localhost:5173` 
- `http://172.20.10.8:5173`

The WebSocket should now connect successfully!

## Why This Happens

1. **Self-signed certificates** are not trusted by browsers by default
2. **HTTPS is required** for WebRTC (audio/video streaming) on network connections
3. Browsers block "insecure" HTTPS connections silently
4. You must **manually accept** the certificate once per domain (localhost, 172.20.10.8, etc.)

## Network Access Troubleshooting

If `172.20.10.8` still doesn't work after accepting the certificate:

### 1. Check Firewall
```bash
# macOS - allow incoming connections on port 8765
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /path/to/python
```

### 2. Verify Both Devices Are on Same Network
- Both devices must be on the same WiFi network
- Some public/guest WiFi networks block peer-to-peer connections

### 3. Test from the Remote Device
From the device trying to connect:
1. Visit `https://172.20.10.8:8765` and accept certificate
2. Then visit `http://172.20.10.8:5173`

### 4. Check Backend is Listening on All Interfaces
The backend should show:
```
🚀 Server starting on port 8765 with HTTPS
📱 Local access: https://localhost:8765
🌐 Network access: https://[YOUR_LOCAL_IP]:8765
```

If it says "0.0.0.0" in the logs, it's listening on all interfaces ✅

## Quick Test Commands

```bash
# Find your local IP
ifconfig | grep "inet " | grep -v 127.0.0.1

# Check if backend is running
lsof -i :8765

# Test backend (replace IP with yours)
curl -k https://172.20.10.8:8765/api/stats

# Test frontend is serving
curl http://172.20.10.8:5173
```

## Still Having Issues?

Check the browser console (F12) for detailed error messages:
- "net::ERR_CERT_AUTHORITY_INVALID" → Accept certificate first
- "net::ERR_CONNECTION_REFUSED" → Backend not running or firewall blocking
- "WebSocket connection failed" → Certificate not accepted for that specific domain

Remember: You need to accept the certificate separately for:
- `localhost` 
- `172.20.10.8` (your local IP)
- Any other device's IP trying to connect


