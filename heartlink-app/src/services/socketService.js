import { io } from 'socket.io-client';

// Use environment variable for backend URL (ngrok tunnel) or fall back to localhost
const BACKEND_URL = `https://${window.location.hostname}:8765`;

class SocketService {
  constructor() {
    this.socket = null;
    this.sessionId = null;
    this.userRole = null;
  }

  connect() {
    if (this.socket?.connected) {
      console.log('♻️  Already connected, reusing socket');
      return this.socket;
    }

    console.log('🔌 Connecting to:', BACKEND_URL);
    
    // Determine if we should use secure based on the URL
    const isSecure = BACKEND_URL.startsWith('https://');
    
    this.socket = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
      rejectUnauthorized: false, // Allow self-signed certificates
      secure: isSecure,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      timeout: 10000,
    });

    this.socket.on('connect', () => {
      console.log('✅ Connected to backend:', this.socket.id);
      console.log('🌐 Backend URL:', BACKEND_URL);
    });
    
    this.socket.on('connect_error', (error) => {
      console.error('❌ Connection error:', error.message);
      console.error('🔍 Check that backend is running and VITE_BACKEND_URL is correct');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ Disconnected from backend:', reason);
    });

    this.socket.on('session_info', (data) => {
      console.log('📋 Session info received:', data);
      this.sessionId = data.session_id;
      this.userRole = data.role;
    });

    return this.socket;
  }

  joinRoom(roomName) {
    if (!this.socket) {
      this.connect();
    }
    console.log('🚪 Joining room:', roomName);
    this.socket.emit('join', { room: roomName });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  getSocket() {
    return this.socket;
  }

  getSessionId() {
    return this.sessionId;
  }

  getUserRole() {
    return this.userRole;
  }
}

// Singleton instance
const socketService = new SocketService();
export default socketService;

