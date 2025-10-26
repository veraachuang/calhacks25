# Frontend Integration Setup

The React frontend (`heartlink-app`) is now connected to the Flask backend!

## 🚀 Quick Start

### 1. Start Backend Server

```bash
# From project root
python app.py
```

The backend will start on `https://localhost:8765` with HTTPS (self-signed certificate).

### 2. Start React Frontend

```bash
# In another terminal
cd heartlink-app
npm run dev
```

The frontend will start on `http://localhost:5173` (or another port if 5173 is busy).

### 3. Open in Browser

Navigate to the URL shown in the terminal (usually `http://localhost:5173`).

**Important**: When the React app tries to connect to the backend, you may need to:
1. Visit `https://localhost:8765` directly in your browser first
2. Accept the security warning for the self-signed certificate
3. Then go back to the React app

## ✨ How It Works

### Profile Page (`/`)
- User fills out profile (name, personality, hobbies, etc.)
- Clicks "Find Your Match"
- **Connects to backend via Socket.IO**
- **Saves profile to session**
- Joins matchmaking room
- Waits for second user
- Navigates to HeartLink Scene

### HeartLink Scene (`/heartlink`)
- **Establishes WebRTC connection with peer**
- **Audio-only by default (flame animations)**
- Real-time transcription of speech
- AI mediator interjections
- Click "📹 Show Video" to switch to video mode
- Transcripts appear in chat box at bottom

## 🔧 Architecture

### Frontend Services

#### `socketService.js`
- Manages Socket.IO connection
- Handles join/leave room
- Stores session ID and user role

#### `webrtcService.js`
- Manages WebRTC peer connection
- Handles audio/video streams
- Toggles video on/off
- Manages ICE candidates and signaling

#### `apiService.js`
- REST API calls to backend
- Profile updates
- Session queries

### Backend Integration Points

#### Socket.IO Events
- `join` - Join matchmaking room
- `session_info` - Receive session ID and role (A or B)
- `user_joined` - Peer joined, start call
- `offer/answer/ice_candidate` - WebRTC signaling
- `audio_chunk` - Send audio for STT (auto-captured)
- `transcript_update` - Receive transcript from backend
- `ai_interjection` - AI mediator speaks

#### REST API Endpoints
- `POST /api/profile/update-bulk` - Save user profile
- `GET /api/profile/both?session_id=X` - Get both user profiles
- `GET /api/sessions` - List sessions
- `POST /api/sessions/:id/end` - End session

## 🎨 Features

### Audio-Only Mode (Default)
- Beautiful flame animations for each user
- Flame colors customizable from profile
- Voice-first experience
- Low bandwidth

### Video Mode (Toggle)
- Click "📹 Show Video" button
- Flames disappear, video feeds appear
- Still maintains flame aesthetic when off
- Can toggle back to audio-only

### Real-Time Transcripts
- Automatic speech-to-text via Fish Audio
- Shows last 5 messages in chat box
- Color-coded by speaker
- AI messages highlighted in pink

### AI Mediator
- Listens to conversation
- Makes interjections when appropriate
- Helps conversation flow
- Context-aware responses

## 🐛 Troubleshooting

### "Failed to connect to backend"
1. Make sure Flask server is running on port 8765
2. Visit `https://localhost:8765` and accept certificate
3. Check browser console for CORS errors

### "Cannot access microphone"
- Browser needs HTTPS to access microphone
- Make sure you accepted browser permissions
- Try refreshing the page

### "No peer available"
- Open app in two different browser tabs/windows
- Or open on two different devices on same network
- Both users need to click "Find Your Match"

### Video not working
- Check camera permissions in browser
- Make sure camera isn't in use by another app
- Try refreshing and accepting permissions again

### Transcripts not appearing
- Make sure microphone is working
- Speak clearly for a few seconds
- Check backend console for STT logs
- Fish Audio API may need setup (see backend docs)

## 🔐 Security Notes

### Development
- Uses self-signed certificate (you'll see warnings)
- CORS is wide open (`*`)
- No authentication

### Production
- Get real SSL certificate (Let's Encrypt)
- Restrict CORS to your domain
- Add user authentication
- Use secure session storage

## 📝 Profile Data Flow

```
React Profile Form
    ↓
socketService.connect()
    ↓
socketService.joinRoom('matchmaking')
    ↓
Backend creates/joins session
    ↓
Backend emits 'session_info' with session_id and role
    ↓
React calls apiService.updateProfile()
    ↓
Backend saves to session (temporary)
    ↓
React navigates to HeartLinkScene
```

## 🎥 WebRTC Flow

```
User A joins → Gets local audio stream
    ↓
User B joins → Backend emits 'user_joined' to A
    ↓
User A creates offer → sends to backend → backend forwards to B
    ↓
User B receives offer → creates answer → sends to backend → backend forwards to A
    ↓
ICE candidates exchanged
    ↓
Peer-to-peer connection established!
    ↓
Audio/video flows directly between users (not through server)
```

## 🧪 Testing

### Test Profile Submission
1. Fill out profile form
2. Open browser console (F12)
3. Click "Find Your Match"
4. Should see: "🔌 Connecting to backend..."
5. Should see: "📋 Got session info: {session_id: ..., role: 'A'}"
6. Should see: "✅ Profile saved successfully"

### Test WebRTC Connection
1. Open app in two browser tabs
2. Fill out profile in both, click "Find Your Match"
3. Both should navigate to HeartLinkScene
4. Connection status should show "🟢 Connected"
5. Speak in one tab, should see transcript in other

### Test Video Toggle
1. Once connected in HeartLinkScene
2. Click "📹 Show Video" button
3. Accept camera permissions if prompted
4. Flames should disappear, video feed should appear
5. Click "📹 Hide Video" to go back to flames

## 🚀 Production Build

### Build React App
```bash
cd heartlink-app
npm run build
```

### Serve from Flask
Update `app.py` to serve the React build:

```python
from flask import send_from_directory

# Serve React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join('heartlink-app/dist', path)):
        return send_from_directory('heartlink-app/dist', path)
    else:
        return send_from_directory('heartlink-app/dist', 'index.html')
```

Then run:
```bash
python app.py
```

Now everything runs on `https://localhost:8765`!

## 📚 Next Steps

- [ ] Add user authentication
- [ ] Persistent user profiles (not just session-based)
- [ ] Match history and results
- [ ] Better UI for "waiting for peer"
- [ ] Progress tracking through conversation phases
- [ ] End session button
- [ ] Replay transcripts after session
- [ ] Mobile responsive design improvements

Enjoy your HeartLink dating app! 💕🔥

