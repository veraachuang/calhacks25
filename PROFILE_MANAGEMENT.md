# Profile Management System

User profile system with permanent base profiles and temporary session-specific edits.

## 🎯 Core Concept

- **Base Profiles**: Permanent JSON files in `/profiles/` (user_A.json, user_B.json)
- **Session Profiles**: Temporary copies in session data
- **Updates**: Only affect session copy, never modify base files
- **Reset**: Session ends → all edits discarded, base profiles unchanged

## 📁 Structure

```
profiles/
├── user_A.json  # Permanent base profile for User A
└── user_B.json  # Permanent base profile for User B

sessions/
└── session_1234.json  # Contains temporary profile copies
```

## 📊 Profile Schema

```json
{
  "user_id": "user_A",
  "name": "User A",
  "personality_type": "introvert",
  "hobbies": ["reading", "photography"],
  "goal": "find new friends",
  "age": 25,
  "interests": ["technology", "art"]
}
```

Customize fields as needed - the system supports any JSON structure.

## 🔧 Python API

### Initialization

```python
from app import profile_manager

# Initialize profile system (creates default profiles if missing)
profile_manager.init_profiles()
```

### Load Profiles

```python
# Load permanent base profile from disk
base_profile = profile_manager.load_profile("user_A")

# Load temporary session profile (with any edits)
session_profile = profile_manager.load_session_profile(session_id, socket_id)

# Get effective profile (session if exists, otherwise base)
profile = profile_manager.get_effective_profile(session_id, socket_id)

# Get both profiles from a session
profiles = profile_manager.get_both_profiles(session_id)
# Returns: {"A": {...}, "B": {...}}
```

### Update Profiles (Temporary)

```python
# Update single field in session profile
profile_manager.update_session_profile(
    session_id,
    user_socket_id,
    "hobbies",
    ["art", "music", "gaming"]
)

# Bulk update multiple fields
profile_manager.update_session_profile_bulk(
    session_id,
    user_socket_id,
    {
        "hobbies": ["rock climbing", "traveling"],
        "goal": "find adventure buddy",
        "personality_type": "ambivert"
    }
)

# Reset to base profile
profile_manager.reset_profile_to_base(session_id, user_socket_id)
```

### Utility

```python
# Attach base profiles to a new session
profile_manager.attach_profiles_to_session(session_id)

# List all base profiles
all_profiles = profile_manager.list_all_profiles()
```

## 🌐 REST API Endpoints

### View Profile

```bash
# Get effective profile for a user in a session
GET /api/profile/view?session_id=session_1234&user_id=socket_abc123

# Get both profiles from a session
GET /api/profile/both?session_id=session_1234

# List all base profiles
GET /api/profiles
```

### Update Profile (Temporary)

```bash
# Update single field
POST /api/profile/update
Content-Type: application/json

{
  "session_id": "session_1234",
  "user_id": "socket_abc123",
  "field": "hobbies",
  "value": ["art", "music", "gaming"]
}

# Bulk update
POST /api/profile/update-bulk
Content-Type: application/json

{
  "session_id": "session_1234",
  "user_id": "socket_abc123",
  "updates": {
    "hobbies": ["rock climbing", "traveling"],
    "goal": "find adventure buddy",
    "personality_type": "ambivert"
  }
}
```

### Reset Profile

```bash
# Reset session profile to base
POST /api/profile/reset
Content-Type: application/json

{
  "session_id": "session_1234",
  "user_id": "socket_abc123"
}
```

## 📱 Frontend Integration

### JavaScript Example

```javascript
// Get session info when user joins
socket.on('session_info', (data) => {
    const sessionId = data.session_id;
    const mySocketId = socket.id;
    
    // Load user's profile
    fetch(`/api/profile/view?session_id=${sessionId}&user_id=${mySocketId}`)
        .then(r => r.json())
        .then(profile => {
            console.log('My profile:', profile);
            displayProfile(profile);
        });
});

// Update profile
function updateMyProfile(field, value) {
    fetch('/api/profile/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: currentSessionId,
            user_id: socket.id,
            field: field,
            value: value
        })
    })
    .then(r => r.json())
    .then(data => {
        console.log('Updated profile:', data.profile);
    });
}

// Example: User updates hobbies
updateMyProfile('hobbies', ['gaming', 'music', 'art']);

// Example: Reset to original
fetch('/api/profile/reset', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        session_id: currentSessionId,
        user_id: socket.id
    })
});
```

## 🔄 Lifecycle

### Session Start
1. Two users join room
2. Session created/joined
3. Profiles automatically attached from base files
4. Each user gets a temporary copy

### During Session
1. User updates profile via API
2. Only session copy is modified
3. Base files remain unchanged
4. Other user can see updates (if you add sync)

### Session End
1. Session marked as ended
2. Session JSON archived with final profile state
3. Base profiles remain unchanged
4. Next session starts fresh from base files

## 🧪 Testing

### Run Demo
```bash
python test_profiles.py
```

Shows:
- Base profile loading
- Session creation
- Profile updates (temporary)
- Base profiles unchanged
- Profile reset

### Interactive Mode
```bash
python test_profiles.py interactive
```

Commands:
- `init` - Initialize profiles
- `load` - Load base profile
- `create` - Create session with profiles
- `update` - Update session profile
- `view` - View session profiles
- `reset` - Reset to base
- `list` - List all base profiles

## 💡 Integration with Video Chat

Profiles are automatically integrated:

1. **User joins room** → Session created
2. **Second user joins** → Session active + profiles attached
3. **During call** → Users can update their session profiles
4. **Call ends** → Profiles reset for next session

## 🎨 Customizing Base Profiles

Edit `profiles/user_A.json` and `profiles/user_B.json`:

```json
{
  "user_id": "user_A",
  "name": "Alice",
  "personality_type": "ambivert",
  "hobbies": ["painting", "yoga", "cooking"],
  "goal": "find meaningful connections",
  "age": 28,
  "interests": ["art", "wellness", "food"],
  "custom_field": "any value you want"
}
```

The system supports any JSON structure - add your own fields!

## 🔐 Security Note

Since profiles are stored as plain JSON files:
- Don't store sensitive data (passwords, SSN, etc.)
- Keep PII minimal
- Consider encryption for production
- This is a prototype - use a database for production

## 📊 Example Use Cases

### AI Host Context
```python
# Get both profiles to provide AI context
profiles = profile_manager.get_both_profiles(session_id)
context = f"User A likes {profiles['A']['hobbies']}, User B likes {profiles['B']['hobbies']}"
# Send to AI for conversation prompts
```

### Matchmaking Score
```python
profile_a = profile_manager.get_both_profiles(session_id)['A']
profile_b = profile_manager.get_both_profiles(session_id)['B']

# Calculate compatibility based on interests overlap
common_interests = set(profile_a['interests']) & set(profile_b['interests'])
score = len(common_interests)
```

### Profile Comparison View
```python
# Show both profiles side-by-side for decision phase
@app.route('/api/comparison')
def comparison():
    profiles = profile_manager.get_both_profiles(session_id)
    return render_template('comparison.html', profiles=profiles)
```

## 🎯 Next Steps

The profile system is ready! To enhance:
1. Add profile editing UI to the video chat page
2. Broadcast profile updates via Socket.IO
3. Add profile validation
4. Store profile change history in transcript
5. Use profiles for AI personality matching

All profile data persists and integrates seamlessly with sessions!

