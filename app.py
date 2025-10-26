from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from app import routes
from app import session_manager
from app import profile_manager
from app import agent_manager
import sys
import os
import base64
import requests
import json

# Add src directory to path for Fish Audio imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from fish import stream_asr, stream_tts

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=10**8)

# Store active users and their sessions
active_users = {}  # socket_id -> user_info
user_sessions = {}  # socket_id -> session_id

# Store transcript buffers per user/room
transcript_buffers = {}

# Store last AI interjection time per room (to avoid spamming)
last_ai_interjection = {}

# JanitorAI configuration
JANITOR_AI_URL = "https://janitorai.com/hackathon/completions"
JANITOR_AI_KEY = "calhacks2047"

# AI agent configuration
AI_INTERJECTION_COOLDOWN = 10  # seconds between AI interjections
AI_CONTEXT_WINDOW = 20  # number of recent transcripts to consider

# Audio quality thresholds
MIN_TRANSCRIPT_LENGTH = 3  # Minimum characters to be considered valid
MIN_AUDIO_SIZE = 1000  # Minimum audio bytes (to filter out noise)
NOISE_KEYWORDS = ['[silence]', '[noise]', '[music]', 'um', 'uh', 'hmm']  # Common noise patterns

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
            session_manager.end_session(session_id)
            print(f'Ended session {session_id} due to disconnect')
        except Exception as e:
            print(f'Error ending session: {e}')
        del user_sessions[request.sid]
    
    if request.sid in active_users:
        del active_users[request.sid]
    
    emit('user_left', {'id': request.sid}, broadcast=True)

@socketio.on('join')
def handle_join(data):
    room = data.get('room', 'default_room')
    join_room(room)
    active_users[request.sid] = room
    print(f'User {request.sid} joined room {room}')
    
    # Create or join a session
    try:
        # Check if there's a waiting session
        waiting_session = session_manager.get_waiting_session()
        
        if waiting_session:
            # Join existing session
            session = session_manager.join_session(waiting_session['session_id'], request.sid)
            user_sessions[request.sid] = session['session_id']
            print(f'User {request.sid} joined session {session["session_id"]}')
            
            # Attach profiles when session becomes active
            profile_manager.attach_profiles_to_session(session['session_id'])
            
            emit('session_info', {
                'session_id': session['session_id'],
                'role': 'B',
                'status': 'active'
            })
        else:
            # Create new session
            session = session_manager.create_session(request.sid, session_id=room)
            user_sessions[request.sid] = session['session_id']
            print(f'User {request.sid} created session {session["session_id"]}')
            emit('session_info', {
                'session_id': session['session_id'],
                'role': 'A',
                'status': 'waiting'
            })
    except Exception as e:
        print(f'Error managing session: {e}')
    
    emit('user_joined', {'id': request.sid}, room=room, skip_sid=request.sid)

@socketio.on('offer')
def handle_offer(data):
    print(f'Offer from {request.sid} to {data["target"]}')
    emit('offer', {
        'offer': data['offer'],
        'sender': request.sid
    }, room=data['target'])

@socketio.on('answer')
def handle_answer(data):
    print(f'Answer from {request.sid} to {data["target"]}')
    emit('answer', {
        'answer': data['answer'],
        'sender': request.sid
    }, room=data['target'])

@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    emit('ice_candidate', {
        'candidate': data['candidate'],
        'sender': request.sid
    }, room=data['target'])

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

        # Decode base64 audio data
        audio_data = base64.b64decode(data['audio'])

        # Check if audio is large enough (noise filter)
        if len(audio_data) < MIN_AUDIO_SIZE:
            return

        # Perform STT using Fish Audio ASR
        transcript = stream_asr(audio_data)

        # Check if transcript is meaningful
        if not is_meaningful_transcript(transcript, len(audio_data)):
            return

        import time

        # Store in session manager if user is in a session
        if session_id:
            try:
                session = session_manager.load_session(session_id)
                if session:
                    # Determine speaker role (A or B)
                    speaker = 'A' if session['user_a'] == user_id else 'B'

                    # Add to session transcript
                    session_manager.append_transcript(session_id, speaker, transcript)

                    print(f"Added to session {session_id} - {speaker}: {transcript}")
            except Exception as e:
                print(f"Error adding to session manager: {e}")

        # Also maintain room buffer for AI interjection logic
        if room not in transcript_buffers:
            transcript_buffers[room] = []

        transcript_buffers[room].append({
            'user_id': user_id,
            'text': transcript,
            'timestamp': time.time()
        })

         # Emit transcript back to all users in room
        emit('transcript_update', {
            'user_id': user_id,
            'text': transcript,
            'session_id': session_id
        }, room=room)

        print(f"Transcribed from {user_id}: {transcript}")

        # Check if Agent should respond (using new agent_manager)
        if session_id and agent_manager.should_trigger_agent(session_id):
            # Trigger agent asynchronously
            socketio.start_background_task(trigger_agent_background, session_id, room)

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

def check_if_ai_should_interject(room):
    """
    Determine if the AI should interject in the conversation.
    Uses heuristics like pauses, question patterns, and cooldown periods.
    """
    import time

    # Check cooldown
    last_time = last_ai_interjection.get(room, 0)
    if time.time() - last_time < AI_INTERJECTION_COOLDOWN:
        return False

    buffer = transcript_buffers.get(room, [])
    if len(buffer) < 3:  # Need at least 3 transcripts
        return False

    # Get recent transcripts
    recent = buffer[-5:]
    recent_text = " ".join([t['text'].lower() for t in recent])

    # Check for trigger patterns
    trigger_patterns = [
        '?',  # Questions
        'what do you think',
        'any suggestions',
        'help',
        'advice',
        'how about',
        'should we',
        'can you',
        'what if'
    ]

    for pattern in trigger_patterns:
        if pattern in recent_text:
            return True

    # Check if conversation has been going for a while (10+ transcripts without AI)
    if len(buffer) >= 10:
        # Check if last 10 transcripts don't have AI interjection
        return True

    return False

def ai_interject(room):
    """
    Background task to have AI analyze conversation and provide interjection.
    """
    import time

    try:
        # Get transcript buffer
        buffer = transcript_buffers.get(room, [])

        if not buffer:
            return

        # Get recent context
        recent_context = buffer[-AI_CONTEXT_WINDOW:]

        # Combine transcripts into context
        context = "\n".join([
            f"User: {t['text']}"
            for t in recent_context
        ])

        # Call JanitorAI to determine if interjection is appropriate
        check_payload = {
            "model": "ignored",
            "messages": [
                {"role": "system", "content": "You are an AI assistant listening to a conversation. Analyze if you should provide helpful input now. Respond with ONLY 'YES' or 'NO' followed by a brief reason."},
                {"role": "user", "content": f"Conversation:\n{context}\n\nShould I interject with helpful information or suggestions?"}
            ],
            "max_tokens": 50
        }

        headers = {
            "Authorization": f"Bearer {JANITOR_AI_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(JANITOR_AI_URL, headers=headers, json=check_payload, timeout=30, stream=False)
        response.raise_for_status()

        # Parse streaming SSE response
        decision = parse_streaming_response(response.text)

        if not decision:
            print("Failed to parse streaming response")
            return

        # If AI decides to interject
        if decision.strip().upper().startswith('YES'):
            # Generate actual interjection
            interject_payload = {
                "model": "ignored",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant participating in a video call. Provide brief, natural, and helpful input to the conversation. Keep it conversational and concise (2-3 sentences max)."},
                    {"role": "user", "content": f"Conversation:\n{context}\n\nProvide a helpful comment or suggestion:"}
                ],
                "max_tokens": 150
            }

            response = requests.post(JANITOR_AI_URL, headers=headers, json=interject_payload, timeout=30, stream=False)
            response.raise_for_status()

            # Parse streaming response
            ai_message = parse_streaming_response(response.text)

            if not ai_message:
                print("Failed to parse AI interjection response")
                return

            # Update last interjection time
            last_ai_interjection[room] = time.time()

            # Emit AI interjection to room
            socketio.emit('ai_interjection', {
                'success': True,
                'message': ai_message,
                'context_used': len(recent_context)
            }, room=room)

            print(f"AI interjected in room {room}: {ai_message}")
        else:
            print(f"AI decided not to interject: {decision}")

    except Exception as e:
        print(f"Error in AI interjection: {e}")

def trigger_agent_background(session_id: str, room: str):
    """
    Background task to trigger Janitor AI agent
    Uses new agent_manager for proper orchestration
    """
    try:
        success, response_text, error = agent_manager.trigger_agent(session_id)
        
        if success:
            # Generate TTS audio for agent response
            try:
                audio_bytes = stream_tts(response_text)
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
                
                socketio.emit('agent_response', {
                    'success': True,
                    'response': response_text,
                    'audio': audio_base64,
                    'format': 'wav',
                    'used_fallback': error is not None
                }, room=room)
                
                print(f"Agent responded in session {session_id}: {response_text[:100]}...")
                
            except Exception as tts_error:
                # Send text even if TTS fails
                socketio.emit('agent_response', {
                    'success': True,
                    'response': response_text,
                    'audio': None,
                    'tts_error': str(tts_error),
                    'used_fallback': error is not None
                }, room=room)
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
    
    # Using a higher port number to avoid conflicts on large networks
    PORT = 8765  # Change this if needed
    print(f"\n🚀 Server starting on port {PORT} with HTTPS")
    print(f"📱 Local access: https://localhost:{PORT}")
    print(f"🌐 Network access: https://[YOUR_LOCAL_IP]:{PORT}")
    print(f"⚠️  Remote users: Accept the browser security warning to proceed\n")
    
    # Run with HTTPS using self-signed certificate
    # ssl_context expects a tuple of (certfile, keyfile)
    socketio.run(
        app, 
        debug=True, 
        host='0.0.0.0', 
        port=PORT,
        ssl_context=('cert.pem', 'key.pem')
    )
