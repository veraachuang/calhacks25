# Session Management System

Complete session management for the voice-based AI dating show, with file-based JSON storage.

## 📁 Structure

```
sessions/
├── session_20251025_210000.json  # Individual session files
├── session_20251025_210530.json
└── log.csv                         # Optional activity log
```

## 🎯 Core Features

### Session Lifecycle
- **Create**: New session with participant A
- **Join**: Participant B joins waiting session
- **Active**: Both participants connected
- **End**: Session archived with all data

### Data Management
- **Transcript**: Real-time conversation log
- **Phase tracking**: icebreaker → deep_dive → decision
- **Summary**: AI-generated conversation summary
- **Timestamps**: Full activity timeline

### Storage
- **JSON files**: One file per session on disk
- **In-memory cache**: Fast access to active sessions
- **CSV log**: Optional analytics/metrics export

## 🔧 API Usage

### Python (Backend)

```python
from app import session_manager

# Create session
session = session_manager.create_session("user_alice")
session_id = session['session_id']

# Join session
session_manager.join_session(session_id, "user_bob")

# Add transcript
session_manager.append_transcript(session_id, "A", "Hello!")
session_manager.append_transcript(session_id, "B", "Hi there!")

# Update phase
session_manager.update_phase(session_id, "deep_dive")

# Update summary
session_manager.update_summary(session_id, "Great connection!")

# End session
session_manager.end_session(session_id)

# List active sessions
active = session_manager.list_active_sessions()

# Get statistics
stats = session_manager.get_session_stats()
```

### HTTP REST API

```bash
# Get all active sessions
curl https://localhost:8765/api/sessions

# Get specific session
curl https://localhost:8765/api/sessions/session_1234

# Get transcript
curl https://localhost:8765/api/sessions/session_1234/transcript

# End session
curl -X POST https://localhost:8765/api/sessions/session_1234/end

# Get statistics
curl https://localhost:8765/api/stats
```

### Socket.IO Events

```javascript
// Client sends transcript (e.g., from ASR)
socket.emit('transcript_message', {
    session_id: 'session_1234',
    speaker: 'A',
    text: 'Hello, nice to meet you!'
});

// Client updates phase
socket.emit('update_phase', {
    session_id: 'session_1234',
    phase: 'deep_dive'
});

// Server broadcasts new transcript
socket.on('new_transcript', (data) => {
    console.log(`${data.speaker}: ${data.text}`);
});

// Server broadcasts phase change
socket.on('phase_changed', (data) => {
    console.log(`Phase: ${data.phase}`);
});

// Session info on join
socket.on('session_info', (data) => {
    console.log(`Session: ${data.session_id}, Role: ${data.role}`);
});
```

## 🧪 Testing

### Run Demo
```bash
python test_sessions.py
```

This creates a sample session, adds transcript entries, and shows all features.

### Interactive Mode
```bash
python test_sessions.py interactive
```

Interactive CLI for manual testing:
- `create` - Create new session
- `join` - Join session
- `transcript` - Add transcript entry
- `phase` - Update phase
- `summary` - Update summary
- `list` - List active sessions
- `end` - End session
- `quit` - Exit

## 📊 Session Data Structure

```json
{
  "session_id": "session_20251025_210000",
  "participants": {
    "A": "user_alice",
    "B": "user_bob"
  },
  "agent": {
    "id": "janitor_01",
    "spiciness": 2
  },
  "phase": "deep_dive",
  "transcript": [
    {
      "speaker": "A",
      "text": "Hey! Nice to meet you!",
      "timestamp": "2025-10-25T21:00:15Z"
    },
    {
      "speaker": "B",
      "text": "Hi! How's it going?",
      "timestamp": "2025-10-25T21:00:20Z"
    }
  ],
  "summary": "Alice and Bob are connecting well.",
  "status": "active",
  "created_at": "2025-10-25T21:00:00Z",
  "last_activity": "2025-10-25T21:00:20Z"
}
```

## 🔄 Integration with Video Chat

The session manager automatically integrates with the video chat:

1. **User joins room** → Session created or joined
2. **Video call starts** → Session becomes active
3. **Conversation happens** → Transcript tracked
4. **User disconnects** → Session ended

Check server console for session activity logs.

## 🛠️ Utility Functions

```python
# Find waiting session (for matchmaking)
waiting = session_manager.get_waiting_session()

# Cleanup idle sessions (run periodically)
session_manager.cleanup_idle_sessions(timeout_minutes=30)

# Get full transcript
transcript = session_manager.get_session_transcript(session_id)

# Get all sessions (including ended)
all_sessions = session_manager.list_all_sessions()
```

## 📈 CSV Log Format

The optional CSV log (`sessions/log.csv`) contains:

```csv
timestamp,session_id,speaker,text
2025-10-25T21:00:00Z,session_1234,SYSTEM,Session created by user_alice
2025-10-25T21:00:10Z,session_1234,SYSTEM,User user_bob joined session
2025-10-25T21:00:15Z,session_1234,A,Hey! Nice to meet you!
2025-10-25T21:00:20Z,session_1234,B,Hi! How's it going?
```

Perfect for analytics, replay, or debugging.

## 🎯 Next Steps

To integrate with ASR/AI:
1. Connect ASR output to `transcript_message` Socket.IO event
2. Have AI agent emit `transcript_message` with `speaker: "AGENT"`
3. Use REST API to query session state for AI context
4. Update `phase` based on AI analysis of conversation

All session data persists to disk automatically!

