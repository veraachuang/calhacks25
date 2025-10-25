from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from app import routes

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active users
active_users = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    emit('user_id', {'id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    if request.sid in active_users:
        del active_users[request.sid]
    emit('user_left', {'id': request.sid}, broadcast=True)

@socketio.on('join')
def handle_join(data):
    room = data.get('room', 'default_room')
    join_room(room)
    active_users[request.sid] = room
    print(f'User {request.sid} joined room {room}')
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
