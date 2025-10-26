# 🚀 Quick Start - React Frontend Connected!

Your React frontend is now fully connected to the Flask backend!

## Start Both Servers

### Terminal 1: Backend
```bash
python app.py
```
Server starts at `https://localhost:8765` or `https://10.0.16.56:8765` (network)

### Terminal 2: Frontend
```bash
cd heartlink-app
npm run dev
```
Frontend starts at:
- Local: `http://localhost:5173`
- Network: `http://10.0.16.56:5173` (your local IP)

## Access Points

### **On Your Machine**
- Open `http://localhost:5173`

### **On Other Devices (Same WiFi)**
- Open `http://10.0.16.56:5173` (use your actual IP)
- First visit `https://10.0.16.56:8765` to accept certificate
- Then go to `http://10.0.16.56:5173`

## First Time Setup

1. **Find your IP**: The frontend will show it in terminal, or run `python find_ip.py`
2. **Accept Certificate**: Visit `https://[YOUR_IP]:8765` and accept the security warning
3. **Open React App**: Visit `http://[YOUR_IP]:5173`

## Test the App

### Single Device Test
1. Open `http://localhost:5173` in Chrome
2. Fill out profile, click "Find Your Match"
3. Open `http://localhost:5173` in another Chrome tab (or Firefox)
4. Fill out second profile, click "Find Your Match"
5. Both should connect to HeartLinkScene
6. Start talking - transcripts appear!
7. AI mediator will interject

### Two Device Test
Same as above, but open on two computers on same WiFi

## What's Integrated

✅ **ProfilePage → Backend**
- Socket.IO connection
- Profile saved to session
- Matchmaking room join

✅ **HeartLinkScene → Backend**
- WebRTC audio/video connection
- Automatic speech-to-text
- Real-time transcripts in chat
- AI interjections displayed
- Video toggle (flames ↔ video)

✅ **Services Created**
- `socketService.js` - Socket.IO management
- `webrtcService.js` - WebRTC + audio capture
- `apiService.js` - REST API calls

## Features Working

🎤 **Audio-Only by Default**
- Flame animations
- Voice transcription
- Low bandwidth

📹 **Video Toggle**
- Click "Show Video" button
- Flames → Video feeds
- Can toggle back anytime

💬 **Real-Time Chat**
- Last 5 transcripts shown
- User messages + AI messages
- Auto-scrolling

🤖 **AI Mediator**
- Listens to conversation
- Makes helpful interjections
- Context-aware

## Troubleshooting

**"Failed to connect to backend"**
→ Visit https://localhost:8765 and accept certificate first

**No transcripts appearing**
→ Make sure Fish Audio API is set up (check backend)
→ Speak clearly for a few seconds
→ Check backend console for STT logs

**Video not working**
→ Accept camera permissions when prompted
→ Make sure camera isn't in use elsewhere

**Peer not connecting**
→ Open in two separate tabs/browsers
→ Both need to click "Find Your Match"

## Architecture

```
React App (localhost:5173)
    ↓ Socket.IO
Flask Backend (localhost:8765)
    ↓ WebRTC Signaling
Peer-to-Peer Audio/Video
    ↓ Audio chunks
Fish Audio STT → Transcripts
    ↓
AI Agent (JanitorAI/Claude)
    ↓
AI Interjections
```

## Next Steps

See `FRONTEND_SETUP.md` for detailed documentation!

Happy coding! 💕🔥

