import { io } from 'socket.io-client';

// Use environment variable for backend URL (ngrok tunnel) or fall back to localhost
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || `https://${window.location.hostname}`;

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
      transports: ['polling', 'websocket'], // Try polling first, then upgrade to websocket
      rejectUnauthorized: false, // Allow self-signed certificates
      secure: isSecure,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 10,
      timeout: 20000,           // 20s connection timeout
      forceNew: false,          // Reuse existing connection
      multiplex: true,          // Allow multiplexing
    });

    this.socket.on('connect', () => {
      console.log('✅ Connected to backend:', this.socket.id);
      console.log('🌐 Backend URL:', BACKEND_URL);
      console.log('🔌 Transport:', this.socket.io.engine.transport.name);
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ Connection error:', error.message);
      console.error('🔍 Details:', {
        url: BACKEND_URL,
        transport: this.socket.io.opts.transports,
        attempt: this.socket.io._reconnectionAttempts
      });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ Disconnected from backend:', reason);
      if (reason === 'io server disconnect') {
        // Server disconnected, need to reconnect manually
        console.log('🔄 Server disconnected, attempting to reconnect...');
        this.socket.connect();
      }
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log('🔄 Reconnected after', attemptNumber, 'attempts');
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log('🔄 Reconnection attempt', attemptNumber);
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('❌ Reconnection error:', error.message);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('❌ Reconnection failed after all attempts');
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

