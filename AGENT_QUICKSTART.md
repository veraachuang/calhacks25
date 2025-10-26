# Agent Manager Quick Start

## 🚀 Quick Test

```bash
# Test prompt building (no API calls)
python test_agent.py prompt

# Test fallback responses
python test_agent.py fallback

# Full demo (includes real API call - requires confirmation)
python test_agent.py

# Interactive mode
python test_agent.py interactive
```

## 💻 Basic Usage

### Python

```python
from app import agent_manager

# Trigger agent for a session
success, response, error = agent_manager.trigger_agent(session_id)

if success:
    print(f"Janitor: {response}")
```

### REST API

```bash
# Trigger agent
curl -X POST https://localhost:8765/api/agent/trigger \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_1234"}'

# Get stats
curl https://localhost:8765/api/agent/stats/session_1234
```

### Socket.IO (JavaScript)

```javascript
// Trigger agent manually
socket.emit('trigger_agent', {
    session_id: 'session_1234'
});

// Listen for response
socket.on('agent_response', (data) => {
    console.log('Janitor:', data.response);
    // Audio included as base64 in data.audio
});
```

## 🎯 Key Features

✅ **Synchronous** - Waits for complete LLM response (no streaming)  
✅ **Retry Logic** - 3 attempts with exponential backoff  
✅ **Cooldown** - 6 second minimum between responses  
✅ **Fallbacks** - Safe defaults when API fails  
✅ **Profile-aware** - Uses participant profiles in prompts  
✅ **TTS Integration** - Auto-generates speech from text  
✅ **Session Persistence** - All responses saved to transcript  

## 🔧 Configuration

Edit `app/agent_manager.py`:

```python
MAX_TURNS_IN_PROMPT = 12     # Conversation history
AGENT_COOLDOWN_SEC = 6       # Seconds between responses
REPLY_MAX_CHARS = 600        # Max response length
```

## 🤖 Agent Personality

Edit `AGENT_RULES` in `app/agent_manager.py` to customize:

```python
AGENT_RULES = """You are "Janitor," a friendly, witty dating-show host.
Be brief (≤3 sentences), keep balance between A and B..."""
```

## 📊 Automatic Triggering

Agent responds automatically when:
- 4+ user turns since last agent message
- Users ask questions (contains "?")
- Users mention "janitor" or "host"
- Cooldown period has passed

## 🛡️ Error Handling

- **Timeouts**: Retries with backoff
- **API errors**: Uses fallback responses
- **Rate limits**: Safe fallback without retry spam

## 📝 Response Format

Agent responses are saved to session transcript:

```json
{
  "speaker": "Janitor",
  "text": "Great conversation! A, tell us more...",
  "timestamp": "2025-10-25T22:30:00Z"
}
```

## 🎵 TTS Integration

Agent responses automatically include audio:

```javascript
socket.on('agent_response', (data) => {
    // Text response
    console.log(data.response);
    
    // Audio (base64 WAV)
    if (data.audio) {
        playAudio(data.audio);
    }
});
```

## 📚 Full Documentation

See `AGENT_MANAGEMENT.md` for complete details.

## 🧪 Testing Without API Calls

```python
from app import agent_manager

# Build prompt without calling API
payload = agent_manager.build_agent_prompt(session_id)
print(payload)

# Get fallback response
fallback = agent_manager.get_fallback_response()
print(fallback)

# Check if should trigger
should_trigger = agent_manager.should_trigger_agent(session_id)
```

## 🎯 Common Patterns

### Manual Trigger with Error Handling

```python
success, response, error = agent_manager.trigger_agent(session_id)

if success:
    if error:
        print(f"Used fallback: {error}")
    print(f"Janitor: {response}")
else:
    print(f"Failed: {error}")
```

### Check Before Triggering

```python
if agent_manager.should_trigger_agent(session_id):
    success, response, error = agent_manager.trigger_agent(session_id)
```

### Get Agent Activity

```python
stats = agent_manager.get_agent_stats(session_id)
print(f"Agent messages: {stats['agent_messages']}/{stats['total_messages']}")
print(f"Cooldown: {stats['cooldown_remaining']:.1f}s")
```

Ready to use! 🎉

