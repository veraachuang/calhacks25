from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from app import routes
from app import session_manager
from app import profile_manager

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active users and their sessions
active_users = {}  # socket_id -> user_info
user_sessions = {}  # socket_id -> session_id

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
