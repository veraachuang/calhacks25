from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from app import routes
from app import session_manager
from app import profile_manager
from app import agent_manager
import sys
import os
import socket
import base64
import requests
import json
import time
import anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src directory to path for Fish Audio imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from fish import stream_asr, stream_tts

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    max_http_buffer_size=10**8,
    ping_timeout=60,          # Wait 60s for pong response before disconnecting
    ping_interval=25,         # Send ping every 25s to keep connection alive
    async_mode='eventlet',    # Use eventlet for better async handling
    engineio_logger=False,    # Reduce logging noise
    logger=False,
    # Increase limits to handle audio streaming
    max_decode_packets=500,   # Allow more packets in single payload (increased from 100)
)

# Store active users and their sessions
active_users = {}  # socket_id -> user_info
user_sessions = {}  # socket_id -> session_id

# Store transcript buffers per user/room
transcript_buffers = {}

# Store last AI interjection time per room (to avoid spamming)
last_ai_interjection = {}

# Store last audio activity time per room (for silence detection)
last_audio_activity = {}

# Store last USER audio activity per room (for overlap prevention)
last_user_audio = {}

# JanitorAI configuration
JANITOR_AI_URL = "https://janitorai.com/hackathon/completions"
JANITOR_AI_KEY = "calhacks2047"

# Claude API configuration
CLAUDE_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"

# AI agent configuration (now handled by agent_manager.py)
# Note: Agent timing and turn counting is managed in agent_manager.py

# Audio quality thresholds (optimized for demo)
MIN_TRANSCRIPT_LENGTH = 5  # Minimum characters to be considered valid (increased to skip short noises)
MIN_AUDIO_SIZE = 2000  # Minimum audio bytes (increased to filter out more noise)
NOISE_KEYWORDS = ['[silence]', '[noise]', '[music]']  # Common noise patterns (removed um/uh/hmm for natural speech)

def parse_streaming_response(response_text):
    """
    Parse Server-Sent Events (SSE) streaming response from JanitorAI.

    Format: data: {"choices":[{"delta":{"content":"text"}}]}

    Returns the complete message by aggregating all delta chunks.
    """
    try:
        complete_message = []

        # Split by lines and process each data chunk
        lines = response_text.strip().split('\n')

        for line in lines:
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Remove 'data: ' prefix
            if line.startswith('data: '):
                json_str = line[6:]  # Remove 'data: '

                try:
                    chunk = json.loads(json_str)

                    # Extract content from delta
                    if 'choices' in chunk and len(chunk['choices']) > 0:
                        delta = chunk['choices'][0].get('delta', {})
                        content = delta.get('content', '')

                        if content:
                            complete_message.append(content)

                except json.JSONDecodeError:
                    continue

        result = ''.join(complete_message)
        print(f"Parsed streaming message: {result}")
        return result

    except Exception as e:
        print(f"Error parsing streaming response: {e}")
        return None

def claude_decision(context, silence_detected=False):
    """
    Use Claude Sonnet 4.5 to decide if AI should interject.

    Args:
        context: Recent conversation transcript
        silence_detected: True if there has been 3+ seconds of silence

    Returns:
        dict with keys: should_interject, intent, target_user, response_style
        Returns None if API call fails
    """
    if not claude_client:
        print("Claude API key not configured")
        return None

    try:
        silence_note = "\n\nIMPORTANT: There has been 3+ seconds of silence. You should interject to keep the conversation flowing." if silence_detected else ""

        message = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"""Analyze this conversation and decide if an AI assistant should interject:

{context}{silence_note}

Respond with ONLY valid JSON (no markdown):
{{
  "should_interject": true or false,
  "intent": "brief reason",
  "target_user": "A" or "B" or "both",
  "response_style": "conversational" or "informative" or "supportive" or "question"
}}"""
            }]
        )

        decision_text = message.content[0].text.strip()

        # Parse JSON (handle markdown if present)
        if decision_text.startswith('```json'):
            decision_text = decision_text[7:]
        if decision_text.startswith('```'):
            decision_text = decision_text[3:]
        if decision_text.endswith('```'):
            decision_text = decision_text[:-3]

        decision = json.loads(decision_text.strip())
        print(f"Claude decision: {decision}")
        return decision

    except Exception as e:
        print(f"Claude API error: {e}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/')
def index():
    return render_template('index.html')

# ========== SESSION API ENDPOINTS ==========

@app.route('/api/sessions', methods=['GET'])
def api_list_sessions():
    """Get all active sessions"""
    sessions = session_manager.list_active_sessions()
    return jsonify(sessions)

@app.route('/api/sessions/<session_id>', methods=['GET'])
def api_get_session(session_id):
    """Get specific session data"""
    session = session_manager.load_session(session_id)
    if session:
        return jsonify(session)
    return jsonify({"error": "Session not found"}), 404

@app.route('/api/sessions/<session_id>/transcript', methods=['GET'])
def api_get_transcript(session_id):
    """Get session transcript"""
    transcript = session_manager.get_session_transcript(session_id)
    return jsonify({"session_id": session_id, "transcript": transcript})

@app.route('/api/sessions/<session_id>/end', methods=['POST'])
def api_end_session(session_id):
    """End a session"""
    try:
        session = session_manager.end_session(session_id)
        return jsonify(session)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/sessions/<session_id>/reset', methods=['DELETE'])
def api_reset_session(session_id):
    """Delete/reset a session completely (for testing)"""
    try:
        import os
        session_path = session_manager._get_session_path(session_id)
        if os.path.exists(session_path):
            os.remove(session_path)
            print(f'🗑️ Deleted session file: {session_path}')
            return jsonify({"success": True, "message": f"Session {session_id} deleted"})
        else:
            return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get session statistics"""
    stats = session_manager.get_session_stats()
    return jsonify(stats)

# ========== PROFILE API ENDPOINTS ==========

@app.route('/api/profile/update', methods=['POST'])
def api_update_profile():
    """Update a user's session profile (temporary, doesn't affect base profile)"""
    data = request.get_json()
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    field = data.get('field')
    value = data.get('value')
    
    if not all([session_id, user_id, field]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        profile = profile_manager.update_session_profile(session_id, user_id, field, value)
        return jsonify({"success": True, "profile": profile})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/profile/update-bulk', methods=['POST'])
def api_update_profile_bulk():
    """Update multiple fields at once"""
    data = request.get_json()
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    updates = data.get('updates', {})
    
    if not all([session_id, user_id, updates]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        profile = profile_manager.update_session_profile_bulk(session_id, user_id, updates)
        return jsonify({"success": True, "profile": profile})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/profile/view', methods=['GET'])
def api_view_profile():
    """Get effective profile for a user in a session"""
    session_id = request.args.get('session_id')
    user_id = request.args.get('user_id')
    
    if not all([session_id, user_id]):
        return jsonify({"error": "Missing required parameters"}), 400
    
    profile = profile_manager.get_effective_profile(session_id, user_id)
    
    if profile:
        return jsonify(profile)
    return jsonify({"error": "Profile not found"}), 404

@app.route('/api/profile/both', methods=['GET'])
def api_view_both_profiles():
    """Get both participant profiles from a session"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    
    profiles = profile_manager.get_both_profiles(session_id)
    return jsonify(profiles)

@app.route('/api/profile/reset', methods=['POST'])
def api_reset_profile():
    """Reset session profile back to base profile"""
    data = request.get_json()
    session_id = data.get('session_id')
    user_id = data.get('user_id')
    
    if not all([session_id, user_id]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        profile = profile_manager.reset_profile_to_base(session_id, user_id)
        return jsonify({"success": True, "profile": profile})
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

@app.route('/api/profiles', methods=['GET'])
def api_list_profiles():
    """Get all base profiles"""
    profiles = profile_manager.list_all_profiles()
    return jsonify(profiles)

# ========== AGENT API ENDPOINTS ==========

@app.route('/api/agent/trigger', methods=['POST'])
def api_trigger_agent():
    """Manually trigger Janitor AI agent for a session"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    
    success, response_text, error = agent_manager.trigger_agent(session_id)
    
    if success:
        return jsonify({
            "success": True,
            "response": response_text,
            "used_fallback": error is not None,
            "fallback_reason": error
        })
    else:
        return jsonify({
            "success": False,
            "error": error
        }), 500

@app.route('/api/agent/stats/<session_id>', methods=['GET'])
def api_agent_stats(session_id):
    """Get agent statistics for a session"""
    stats = agent_manager.get_agent_stats(session_id)
    return jsonify(stats)

@app.route('/api/agent/tts', methods=['POST'])
def api_agent_tts():
    """Convert agent text to speech"""
    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({"error": "Missing text"}), 400
    
    try:
        # Generate audio using Fish Audio TTS
        audio_bytes = stream_tts(text)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return jsonify({
            "success": True,
            "audio": audio_base64,
            "format": "wav"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('user_id', {'id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    
    # End session if user was in one
    if request.sid in user_sessions:
        session_id = user_sessions[request.sid]
        try:
            # End the session (marks as ended, saves to disk for archival)
            session_manager.end_session(session_id)
            print(f'✅ Ended session {session_id} due to disconnect')
            
            # For MVP: Delete the session file immediately (no archival needed)
            # This keeps only active sessions in memory and on disk
            import os
            session_path = session_manager._get_session_path(session_id)
            if os.path.exists(session_path):
                os.remove(session_path)
                print(f'🗑️  Deleted session file {session_id}')
        except Exception as e:
            print(f'Error ending session: {e}')
        
        # Remove from tracking
        del user_sessions[request.sid]
    
    if request.sid in active_users:
        room = active_users[request.sid]
        del active_users[request.sid]
        # Notify others in the room
        emit('user_left', {'id': request.sid}, room=room)
    else:
        emit('user_left', {'id': request.sid}, broadcast=True)

@socketio.on('join')
def handle_join(data):
    room = data.get('room', 'default_room')
    join_room(room)
    active_users[request.sid] = room
    print(f'🚪 User {request.sid} joined room {room}')
    
    # Create or join a session
    try:
        # Check if this socket is ALREADY in a session (prevents double-joining)
        if request.sid in user_sessions:
            existing_user_session_id = user_sessions[request.sid]
            print(f'♻️  User {request.sid} already in session {existing_user_session_id}, skipping join')
            # Just confirm they're still in the session
            existing_user_session = session_manager.load_session(existing_user_session_id)
            if existing_user_session:
                # Determine their role
                role = 'A' if existing_user_session['participants']['A'] == request.sid else 'B'
                emit('session_info', {
                    'session_id': existing_user_session_id,
                    'role': role,
                    'status': existing_user_session['status']
                })
            return
        
        # MVP: Look for ANY waiting session (instead of hardcoded ID)
        waiting_session = session_manager.get_waiting_session()
        
        if waiting_session:
            # Join existing waiting session as User B
            session = session_manager.join_session(waiting_session['session_id'], request.sid)
            user_sessions[request.sid] = session['session_id']
            print(f'✅ User {request.sid} joined as User B in session {session["session_id"]}')
            print(f'📋 user_sessions now: {user_sessions}')
            
            # Attach profiles when session becomes active
            profile_manager.attach_profiles_to_session(session['session_id'])
            
            emit('session_info', {
                'session_id': session['session_id'],
                'role': 'B',
                'status': 'active'
            })

            # Notify BOTH users about each other
            user_a_sid = session['participants']['A']
            user_b_sid = request.sid

            print(f'📢 Notifying User A ({user_a_sid}) that User B ({user_b_sid}) joined')
            # Send to User A: User B has joined
            emit('user_joined', {'id': user_b_sid}, room=user_a_sid)

            print(f'📢 Notifying User B ({user_b_sid}) that User A ({user_a_sid}) is already here')
            # Send to User B: User A is already in the session
            emit('user_joined', {'id': user_a_sid}, room=user_b_sid)
        else:
            # Check if there's an active session (MVP: only 1 session at a time)
            active_sessions = session_manager.list_active_sessions()
            if len(active_sessions) > 0:
                # MVP limit: Only 1 active session (2 users) at a time
                print(f'⚠️ Active session exists (MVP limit: 2 users)')
                emit('session_error', {
                    'error': 'session_full',
                    'message': 'Matchmaking room is full (2 users max). Please wait or try again later.',
                    'details': {
                        'active_sessions': len(active_sessions)
                    }
                })
                # Don't add user to user_sessions
                return
            
            # Create new session with auto-generated ID (timestamp-based)
            session = session_manager.create_session(request.sid)
            user_sessions[request.sid] = session['session_id']
            print(f'✅ User {request.sid} created session {session["session_id"]} as User A')
            print(f'📋 user_sessions now: {user_sessions}')
            emit('session_info', {
                'session_id': session['session_id'],
                'role': 'A',
                'status': 'waiting'
            })
    except Exception as e:
        print(f'❌ Error managing session: {e}')
        import traceback
        traceback.print_exc()

@socketio.on('offer')
def handle_offer(data):
    print(f'Offer from {request.sid} to {data["target"]}')
    emit('offer', {
        'offer': data['offer'],
        'sender': request.sid
    }, to=data['target'])  # Use 'to' for direct socket messaging

@socketio.on('answer')
def handle_answer(data):
    print(f'Answer from {request.sid} to {data["target"]}')
    emit('answer', {
        'answer': data['answer'],
        'sender': request.sid
    }, to=data['target'])  # Use 'to' for direct socket messaging

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    emit('ice_candidate', {
        'candidate': data['candidate'],
        'sender': request.sid
    }, to=data['target'])  # Use 'to' for direct socket messaging

def is_meaningful_transcript(transcript, audio_size):
    """
    Determine if a transcript is meaningful (not noise or silence).
    """
    # Check audio size
    if audio_size < MIN_AUDIO_SIZE:
        return False

    # Check transcript length
    if len(transcript.strip()) < MIN_TRANSCRIPT_LENGTH:
        return False

    # Filter out very repetitive patterns
    words = transcript.lower().strip().split()
    if len(words) > 2 and len(set(words)) == 1:
        return False

    return True

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    """
    Handle incoming audio chunks for STT processing.
    Audio is sent as base64-encoded data.
    """
    try:
        user_id = request.sid
        room = active_users.get(user_id, 'default')
        session_id = user_sessions.get(user_id)

        if not session_id:
            print(f"⚠️ Audio chunk from {user_id} - no session_id!")
            print(f"   Active user_sessions: {user_sessions}")

        # Decode base64 audio data
        audio_data = base64.b64decode(data['audio'])

        # Check if audio is large enough (noise filter)
        if len(audio_data) < MIN_AUDIO_SIZE:
            return

        # Use Fish Audio for STT
        transcript = stream_asr(audio_data)

        # Check if transcript is meaningful
        if not is_meaningful_transcript(transcript, len(audio_data)):
            return

        import time

        # Determine speaker info
        speaker_role = None
        speaker_name = None

        # Store in session manager if user is in a session
        if session_id:
            try:
                session = session_manager.load_session(session_id)
                if session and 'participants' in session:
                    participants = session['participants']

                    # Determine speaker role (A or B)
                    if participants.get('A') == user_id:
                        speaker_role = 'A'
                    elif participants.get('B') == user_id:
                        speaker_role = 'B'
                    else:
                        print(f"⚠️ User {user_id} not found in session participants: {participants}")
                        speaker_role = None

                    if speaker_role:
                        # Get speaker name from profiles
                        try:
                            profiles = profile_manager.get_both_profiles(session_id)
                            speaker_profile = profiles.get(speaker_role)
                            if speaker_profile:
                                speaker_name = speaker_profile.get('name', f'User {speaker_role}')
                        except:
                            speaker_name = f'User {speaker_role}'

                        # Add to session transcript
                        session_manager.append_transcript(session_id, speaker_role, transcript)

                        print(f"✅ Added to session {session_id} - {speaker_role} ({speaker_name}): {transcript}")
                else:
                    print(f"⚠️ Session {session_id} missing participants field")
            except KeyError as e:
                print(f"❌ Session missing required fields: {e}")
            except Exception as e:
                print(f"❌ Error adding to session manager: {e}")
                import traceback
                traceback.print_exc()

        # Also maintain room buffer for AI interjection logic
        if room not in transcript_buffers:
            transcript_buffers[room] = []

        transcript_buffers[room].append({
            'user_id': user_id,
            'text': transcript,
            'timestamp': time.time()
        })

         # Emit transcript back to all users in room with speaker info
        emit('transcript_update', {
            'user_id': user_id,
            'speaker_role': speaker_role,
            'speaker_name': speaker_name,
            'text': transcript,
            'session_id': session_id
        }, room=room)

        print(f"Transcribed from {user_id}: {transcript}")

        # Update last audio activity timestamp for this room
        last_audio_activity[room] = time.time()

        # Update last USER audio activity (for AI overlap prevention)
        last_user_audio[room] = time.time()

        # Use agent_manager to determine if we should trigger
        if session_id:
            should_trigger = agent_manager.should_trigger_agent(session_id)

            if should_trigger:
                # Verify session is actually active
                session = session_manager.load_session(session_id)
                if not session or session.get('status') != 'active':
                    print(f"⏭️ Skipping AI interjection - session {session_id} not active")
                else:
                    print(f"🤖 Triggering agent for session {session_id} (agent_manager says should trigger)")
                    socketio.start_background_task(trigger_agent_background, session_id, room)
        else:
            print(f"⚠️ No session_id available, cannot check agent trigger")

    except Exception as e:
        print(f"Error processing audio chunk: {e}")
        emit('stt_error', {'error': str(e)})

@app.route('/api/transcript/buffer/<room_or_session>', methods=['GET'])
def get_transcript_buffer(room_or_session):
    """
    Get the current transcript buffer for a room or session.
    Supports both legacy room-based and new session-based transcripts.
    """
    # Try session manager first
    session_transcript = session_manager.get_session_transcript(room_or_session)

    if session_transcript:
        # Return session-based transcript
        return jsonify({
            'session_id': room_or_session,
            'transcript_count': len(session_transcript),
            'transcripts': session_transcript,
            'source': 'session_manager'
        })

    # Fallback to room-based buffer
    buffer = transcript_buffers.get(room_or_session, [])
    return jsonify({
        'room': room_or_session,
        'transcript_count': len(buffer),
        'transcripts': buffer,
        'source': 'room_buffer'
    })

@app.route('/api/transcript/clear/<room_or_session>', methods=['POST'])
def clear_transcript_buffer(room_or_session):
    """
    Clear the transcript buffer for a room or session.
    Clears both session manager and room buffer if they exist.
    """
    cleared = []

    # Clear session manager transcript
    try:
        session = session_manager.load_session(room_or_session)
        if session:
            session['transcript'] = []
            session_manager.sessions[room_or_session] = session
            cleared.append('session_manager')
    except:
        pass

    # Clear room buffer
    if room_or_session in transcript_buffers:
        transcript_buffers[room_or_session] = []
        cleared.append('room_buffer')

    return jsonify({
        'success': True,
        'room_or_session': room_or_session,
        'cleared': cleared
    })

@app.route('/api/tts', methods=['POST'])
def tts_endpoint():
    """
    Text-to-speech endpoint for AI responses.
    """
    try:
        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400

        text = data['text']

        if not text.strip():
            return jsonify({'error': 'Empty text'}), 400

        # Generate audio using Fish Audio TTS
        audio_bytes = stream_tts(text)
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        return jsonify({
            'audio': audio_base64,
            'format': 'wav'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500




def trigger_agent_background(session_id: str, room: str):
    """
    Background task to trigger Janitor AI agent
    Uses new agent_manager for proper orchestration
    """
    try:
        success, response_text, error = agent_manager.trigger_agent(session_id)

        if success:
            import time

            # Send text immediately to display without waiting for TTS
            socketio.emit('agent_response', {
                'success': True,
                'response': response_text,
                'audio': None,  # Audio will come separately
                'used_fallback': error is not None
            }, room=room)

            print(f"Agent responded in session {session_id}: {response_text[:100]}...")

            # Generate TTS audio in parallel (don't block on this)
            try:
                import time
                audio_bytes = stream_tts(response_text)
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

                # Check if users are currently speaking (within last 2 seconds)
                last_user_time = last_user_audio.get(room, 0)
                time_since_user_audio = time.time() - last_user_time

                # Wait for a brief pause in user speech before sending audio
                if time_since_user_audio < 2.0:
                    print(f"⏸️ Waiting for users to finish speaking (last audio {time_since_user_audio:.1f}s ago)...")
                    # Wait up to 4 seconds for users to finish
                    for _ in range(20):  # 20 * 0.2s = 4s max wait
                        time.sleep(0.2)
                        time_since_user_audio = time.time() - last_user_audio.get(room, 0)
                        if time_since_user_audio >= 2.0:
                            break

                # Send audio separately after generation and wait (full audio in one message)
                socketio.emit('agent_audio', {
                    'audio': audio_base64,
                    'format': 'wav'
                }, room=room)

                print(f"✅ Agent audio sent for session {session_id} (waited {time_since_user_audio:.1f}s)")

            except Exception as tts_error:
                print(f"❌ TTS generation failed: {tts_error}")
        else:
            print(f"Agent failed for session {session_id}: {error}")

    except Exception as e:
        print(f"Error in agent background task: {e}")

@socketio.on('trigger_agent')
def handle_trigger_agent(data):
    """
    Manual trigger for Janitor AI agent (updated to use agent_manager)
    """
    try:
        session_id = data.get('session_id')
        user_id = request.sid
        room = active_users.get(user_id, 'default')
        
        if not session_id:
            # Try to get session from user
            session_id = user_sessions.get(user_id)
        
        if not session_id:
            emit('agent_response', {'error': 'No session found'})
            return
        
        # Trigger agent using background task
        socketio.start_background_task(trigger_agent_background, session_id, room)
        
        # Immediately acknowledge
        emit('agent_triggered', {'session_id': session_id})
        
    except Exception as e:
        print(f"Error triggering agent: {e}")
        emit('agent_response', {'error': str(e)})

@socketio.on('transcript_message')
def handle_transcript_message(data):
    """Handle incoming transcript messages (from ASR)"""
    session_id = data.get('session_id')
    speaker = data.get('speaker')  # 'A' or 'B'
    text = data.get('text')
    
    if session_id and speaker and text:
        try:
            session_manager.append_transcript(session_id, speaker, text)
            # Broadcast transcript to all participants in the room
            emit('new_transcript', {
                'session_id': session_id,
                'speaker': speaker,
                'text': text
            }, room=session_id, broadcast=True)
        except Exception as e:
            print(f'Error appending transcript: {e}')

@socketio.on('update_phase')
def handle_update_phase(data):
    """Update conversation phase"""
    session_id = data.get('session_id')
    phase = data.get('phase')
    
    if session_id and phase:
        try:
            session_manager.update_phase(session_id, phase)
            emit('phase_changed', {
                'session_id': session_id,
                'phase': phase
            }, room=session_id, broadcast=True)
        except Exception as e:
            print(f'Error updating phase: {e}')

if __name__ == '__main__':
    # Initialize profile system
    profile_manager.init_profiles()
    
    # Clean up any leftover session files from previous runs
    # MVP: Delete ALL old sessions on startup (fresh start)
    import os
    import glob
    session_files = glob.glob('sessions/*.json')
    if session_files:
        print(f'\n🧹 Cleaning up {len(session_files)} old session files...')
        for session_file in session_files:
            try:
                os.remove(session_file)
                print(f'  🗑️  Deleted {os.path.basename(session_file)}')
            except Exception as e:
                print(f'  ⚠️  Could not delete {os.path.basename(session_file)}: {e}')
        print('✅ Cleanup complete\n')
    
    # Using a higher port number to avoid conflicts on large networks
    PORT = 8765  # Change this if needed
    
    # Check if SSL certificates exist and if SSL should be used
    # Disable SSL when using ngrok (set NO_SSL=1 environment variable)
    use_ssl = (os.path.exists('cert.pem') and os.path.exists('key.pem') 
               and not os.getenv('NO_SSL', '').lower() in ['1', 'true', 'yes'])
    
    if use_ssl:
        print(f"\n🚀 Server starting on port {PORT} with HTTPS")
        print(f"📱 Local access: https://localhost:{PORT}")
        print(f"🌐 Network access: https://[YOUR_LOCAL_IP]:{PORT}")
        print(f"⚠️  Remote users: Accept the browser security warning to proceed\n")
        socketio.run(
            app, 
            debug=True, 
            host='0.0.0.0', 
            port=PORT,
            ssl_context=('cert.pem', 'key.pem')
        )
    else:
        print(f"\n🚀 Server starting on port {PORT} with HTTP (no SSL certs found)")
        print(f"📱 Local access: http://localhost:{PORT}")
        print(f"🌐 Network access: http://[YOUR_LOCAL_IP]:{PORT}")
        print(f"💡 For HTTPS: Generate cert.pem and key.pem with: openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365\n")
        socketio.run(
            app, 
            debug=True, 
            host='0.0.0.0', 
            port=PORT
        )
