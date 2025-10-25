from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from app import routes
from app import session_manager
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

        # Initialize buffer if not exists
        if room not in transcript_buffers:
            transcript_buffers[room] = []

        # Add transcript to buffer with timestamp
        import time
        transcript_buffers[room].append({
            'user_id': user_id,
            'text': transcript,
            'timestamp': time.time()
        })

        # Emit transcript back to all users in room
        emit('transcript_update', {
            'user_id': user_id,
            'text': transcript
        }, room=room)

        print(f"Transcribed from {user_id}: {transcript}")

        # Check if AI should interject
        should_interject = check_if_ai_should_interject(room)
        if should_interject:
            # Trigger AI interjection asynchronously
            socketio.start_background_task(ai_interject, room)

    except Exception as e:
        print(f"Error processing audio chunk: {e}")
        emit('stt_error', {'error': str(e)})

@app.route('/api/transcript/buffer/<room>', methods=['GET'])
def get_transcript_buffer(room):
    """
    Get the current transcript buffer for a room.
    """
    buffer = transcript_buffers.get(room, [])
    return jsonify({
        'room': room,
        'transcript_count': len(buffer),
        'transcripts': buffer
    })

@app.route('/api/transcript/clear/<room>', methods=['POST'])
def clear_transcript_buffer(room):
    """
    Clear the transcript buffer for a room.
    """
    if room in transcript_buffers:
        transcript_buffers[room] = []
    return jsonify({'success': True, 'room': room})

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

@socketio.on('trigger_ai')
def handle_trigger_ai(data):
    """
    Manual trigger to send transcript buffer to JanitorAI.
    """
    try:
        user_id = request.sid
        room = active_users.get(user_id, 'default')

        # Get transcript buffer
        buffer = transcript_buffers.get(room, [])

        if not buffer:
            emit('ai_response', {'error': 'No transcripts in buffer'})
            return

        # Combine all transcripts into context
        context = "\n".join([
            f"User: {t['text']}"
            for t in buffer[-AI_CONTEXT_WINDOW:]
        ])

        # Get custom prompt or use default
        user_prompt = data.get('prompt', 'Provide insights or suggestions based on this conversation.')
        system_prompt = data.get('system_prompt', 'You are a helpful AI assistant analyzing a video call conversation.')

        # Prepare JanitorAI request
        payload = {
            "model": "ignored",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Conversation:\n{context}\n\n{user_prompt}"}
            ],
            "max_tokens": data.get('max_tokens', 500)
        }

        headers = {
            "Authorization": f"Bearer {JANITOR_AI_KEY}",
            "Content-Type": "application/json"
        }

        # Call JanitorAI
        response = requests.post(JANITOR_AI_URL, headers=headers, json=payload, timeout=30, stream=False)
        response.raise_for_status()

        # Parse streaming response
        ai_message = parse_streaming_response(response.text)

        if not ai_message:
            emit('ai_response', {'error': 'Failed to parse AI response'})
            return

        # Emit AI response to room
        emit('ai_response', {
            'success': True,
            'response': ai_message,
            'context_used': len(buffer)
        }, room=room)

        print(f"AI Response sent to room {room}: {ai_message[:100]}...")

    except Exception as e:
        print(f"Error triggering AI: {e}")
        emit('ai_response', {'error': str(e)})

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
