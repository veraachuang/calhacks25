# 1-1 Video Chat Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Find Your Local IP Address
```bash
python find_ip.py
```
This will display your local IP and the connection URL to share.

**Alternative manual methods:**
- **Mac/Linux**: `ifconfig | grep "inet " | grep -v 127.0.0.1`
- **Windows**: `ipconfig` (look for "IPv4 Address")

### 3. Run the Server
```bash
python app.py
```

The server will start on port **8765** (less likely to conflict on large networks).

### 4. Connect Clients

#### Machine 1 (Server + Client):
- Open browser: `https://localhost:8765`
- Accept the browser security warning (self-signed certificate)

#### Machine 2 (Client):
- Use the IP from step 2: `https://[SERVER_IP]:8765`
  - Example: `https://192.168.50.123:8765`
- **IMPORTANT:** Click "Advanced" → "Proceed" when you see the security warning
- This is necessary for camera/microphone access to work!

### 5. Start Video Chat

1. **Both users** enter the **same room name** (e.g., "room1") and click "Join Room"
2. Allow camera and microphone permissions when prompted
3. **Either user** clicks "Start Call" to initiate the connection
4. Video and audio will connect automatically via WebRTC

## How It Works

- **Flask + Socket.IO**: Handles WebRTC signaling (connection setup)
- **WebRTC**: Peer-to-peer video/audio streaming (no media goes through server)
- **Room System**: Multiple pairs can use different rooms simultaneously

## Tech Stack

- Backend: Python Flask + Flask-SocketIO
- Frontend: HTML5 + WebRTC API + Socket.IO Client
- Video/Audio: WebRTC (peer-to-peer)
- Signaling: Socket.IO
- Security: HTTPS with self-signed certificate (required for camera/mic access)

## Troubleshooting

### Can't connect from another machine?
- Make sure both machines are on the same WiFi network
- Check firewall settings (port 8765 should be open)
- Verify the server IP address is correct
- On large public networks, try a different port if 8765 is blocked (edit PORT in app.py)

### Camera/Mic not working?
- **Make sure you're using HTTPS** (not HTTP)
- Accept the browser security warning for the self-signed certificate
- Allow browser permissions for camera/microphone when prompted
- Check browser console for errors (F12)
- Try a different browser (Chrome/Firefox recommended)

### Video is one-way only?
- Make sure both users joined the same room
- Check that both users allowed camera/mic permissions
- Try refreshing and rejoining

## Notes

- Uses Google's free STUN servers for NAT traversal
- Works on local network without external TURN server
- For production, consider adding authentication and HTTPS

