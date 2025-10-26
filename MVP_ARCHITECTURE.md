# MVP Architecture: Room vs Session

## 🎯 Current MVP Design (2-User Maximum)

The MVP uses a **single global session** for matchmaking, supporting exactly **2 concurrent users**.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  Socket.IO Room: "matchmaking"          │
│              (Broadcast channel for real-time events)   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│    IN-MEMORY Session (auto-generated ID)                │
│    session_20251026_123456                              │
│                                                         │
│          Participants:                                  │
│            A: [socket_id_1]  ←  User 1                 │
│            B: [socket_id_2]  ←  User 2                 │
│                                                         │
│    Status: "waiting" → "active" → "ended" → DELETED    │
│                                                         │
│    ✅ Saved to disk only while active (in-memory cache) │
│    🗑️  Deleted when both users disconnect              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Key Concepts

#### 1. **Socket.IO Room** (`"matchmaking"`)
- **Purpose**: Real-time broadcast channel
- **Usage**: Broadcasting events to all connected users
- **Examples**: 
  - `transcript_update` - Share transcribed speech
  - `ai_interjection` - AI assistant messages
  - `user_joined` - Notify when peer connects

#### 2. **Session** (`matchmaking.json`)
- **Purpose**: Persistent storage for conversation data
- **Usage**: Track participants, transcript, phase, profiles
- **Lifecycle**:
  - `waiting` - User A waiting for User B
  - `active` - Both users connected
  - `ended` - Session completed

#### 3. **WebRTC Signaling** (Direct Socket-to-Socket)
- **Purpose**: Peer-to-peer connection setup
- **Usage**: Exchange SDP offers/answers and ICE candidates
- **Method**: Direct targeting with `to=socket_id`
- **Examples**:
  - `offer` - User B → User A (start call)
  - `answer` - User A → User B (accept call)
  - `ice_candidate` - Exchange network info

### Connection Flow

```
User 1 (becomes User A):
  1. Opens profile page
  2. Clicks "Enter HeartLink"
  3. socket.emit('join', { room: 'matchmaking' })
  4. Backend: No waiting session → creates NEW session with auto-generated ID
     session_id = 'session_20251026_123456'
  5. Receives: session_info { session_id, role: 'A', status: 'waiting' }
  6. Waits for User B...

User 2 (becomes User B):
  1. Opens profile page
  2. Clicks "Enter HeartLink"
  3. socket.emit('join', { room: 'matchmaking' })
  4. Backend: Finds waiting session → joins it as User B
  5. Receives: session_info { session_id, role: 'B', status: 'active' }
  6. Initiates WebRTC call to User A

User 3 (rejected):
  1. Opens profile page
  2. Clicks "Enter HeartLink"
  3. socket.emit('join', { room: 'matchmaking' })
  4. Backend: Active session exists (no waiting session) → rejects
  5. Receives: session_error { error: 'session_full', message: '...' }
  6. Shows error: "Matchmaking room is full (2 users max)"

Both users disconnect:
  1. socket disconnects
  2. Backend: end_session() called
  3. Session file DELETED immediately
  4. Next user creates a fresh new session ✨
```

### Data Storage

#### Global Variables (Backend)
```python
active_users = {}          # socket_id → room_name
user_sessions = {}         # socket_id → session_id
transcript_buffers = {}    # room → [transcript_entries]
last_ai_interjection = {}  # room → timestamp
last_audio_activity = {}   # room → timestamp
```

#### Session File (Example: `sessions/session_20251026_123456.json`)
```json
{
  "session_id": "session_20251026_123456",
  "participants": {
    "A": "socket_id_xxx",
    "B": "socket_id_yyy"
  },
  "agent": {
    "id": "janitor_01",
    "spiciness": 2
  },
  "phase": "icebreaker",
  "transcript": [
    {
      "speaker": "A",
      "text": "Hello!",
      "timestamp": "2025-10-26T..."
    }
  ],
  "summary": "",
  "status": "active",
  "created_at": "2025-10-26T...",
  "last_activity": "2025-10-26T...",
  "participant_profiles": {
    "A": { "name": "Alice", ... },
    "B": { "name": "Bob", ... }
  }
}
```

## 🔧 Recent Fixes

### Fix #1: WebRTC Signaling (Direct vs Broadcast)

**Problem**: WebRTC signaling used `room=` parameter instead of direct socket targeting.

**Before**:
```python
emit('offer', {...}, room=data['target'])  # WRONG - 'target' is a socket_id, not a room
```

**After**:
```python
emit('offer', {...}, to=data['target'])  # CORRECT - direct socket-to-socket
```

**Why**: WebRTC offers/answers are point-to-point, not broadcasts. Using `room=` would fail because `data['target']` is a socket ID, not a room name.

### Fix #2: Session Full Handling

**Problem**: Third user attempting to join got confusing error messages.

**Before**:
```python
emit('session_info', {
    'error': 'Session is full or already active'  # Vague
})
```

**After**:
```python
emit('session_error', {
    'error': 'session_full',
    'message': 'Matchmaking room is full (2 users max)...',
    'details': { ... }
})
# Don't add to active_users or user_sessions
return  # Early exit
```

**Why**: Clear error type allows frontend to show specific user-friendly message.

### Fix #3: Frontend Error Messages

**Added**:
```javascript
socket.once('session_error', (data) => {
  reject(new Error(data.message));
});

// In catch block:
if (error.message.includes('full')) {
  alert('⚠️ Matchmaking room is full!\n\nThe MVP supports 2 users max.');
}
```

## 🚨 Current Limitations

### Hard Limits (MVP)
1. **2 users maximum** - Third user gets "session full" error
2. **Single session** - All users compete for same session
3. **No queuing** - Users must manually retry when session ends
4. **No session recovery** - Disconnect = session ends

### Session Cleanup
- **Manual reset required**: Delete `sessions/matchmaking.json` between tests
- **Automatic cleanup**: Ended sessions are deleted on next join attempt
- **No timeout**: Sessions don't automatically expire

### Network Considerations
- **HTTPS required**: Self-signed certificates for local network
- **Certificate acceptance**: Each domain (localhost, 172.20.10.8) needs manual acceptance
- **Same network**: Both users must be on same WiFi/LAN
- **Firewall**: May need to allow port 8765

## 🚀 Future Scalability (Not Implemented)

To support multiple concurrent sessions:

```python
# Generate unique session IDs
session_id = f"session_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

# Matchmaking logic
waiting_session = session_manager.get_waiting_session()
if waiting_session:
    # Join existing waiting session
    session_manager.join_session(waiting_session['session_id'], request.sid)
else:
    # Create new session
    session_manager.create_session(request.sid, session_id=session_id)

# Users join session-specific rooms
join_room(session_id)  # Instead of join_room('matchmaking')
```

This would allow:
- ✅ Multiple concurrent 2-person sessions
- ✅ True matchmaking queue
- ✅ Session-specific broadcasts
- ✅ Unlimited users (paired into sessions)

## 📝 Testing the MVP

### Test Case 1: Normal 2-User Flow
```bash
# Terminal 1: Start backend
python app.py

# Browser 1: User A
http://localhost:5173
→ Enter profile → Click "Enter HeartLink"
→ Status: "🟡 Waiting for peer..."

# Browser 2: User B
http://localhost:5173
→ Enter profile → Click "Enter HeartLink"
→ Status: "🟢 Connected"
→ Both browsers: Call connects, audio/video works
```

### Test Case 2: Session Full (3rd User)
```bash
# Browser 1 & 2: Connected (as above)

# Browser 3: User C
http://localhost:5173
→ Enter profile → Click "Enter HeartLink"
→ Alert: "⚠️ Matchmaking room is full! (2 users max)"
→ Returns to profile page
```

### Test Case 3: Network Access
```bash
# Device 1: Get local IP
ifconfig | grep "inet " | grep -v 127.0.0.1
# Example: 172.20.10.8

# Device 2: 
1. Visit https://172.20.10.8:8765 → Accept certificate
2. Visit http://172.20.10.8:5173 → Use app normally
```

### Reset Between Tests
```bash
# Option 1: Delete session file
rm sessions/matchmaking.json

# Option 2: Use reset script
./reset_session.sh

# Option 3: Restart backend (auto-cleans ended sessions)
```

## 📚 Related Documentation

- `SESSION_MANAGEMENT.md` - Complete session manager API
- `WEBSOCKET_FIX.md` - Network connection troubleshooting
- `VIDEO_CHAT_SETUP.md` - WebRTC setup guide
- `QUICKSTART_FRONTEND.md` - Frontend dev guide

## 🎓 Key Takeaways

1. **Rooms ≠ Sessions**: Rooms are for real-time broadcast, sessions are for persistence
2. **WebRTC is P2P**: Use direct socket targeting (`to=`), not room broadcasts
3. **MVP is intentionally limited**: Single session = simple, predictable behavior
4. **Scalability requires refactoring**: Multi-session support needs matchmaking logic
5. **Network access needs HTTPS**: Self-signed certs work but need manual acceptance

