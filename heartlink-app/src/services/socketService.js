import { io } from 'socket.io-client';
import { BACKEND_URL } from '../config';

// Backend URL is now configured via config.js
// This allows for cross-device connectivity on the same network

class SocketService {
  constructor() {
    this.socket = null;
    this.sessionId = null;
    this.userRole = null;
  }

  connect() {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io(BACKEND_URL, {
      transports: ['websocket', 'polling'],
      rejectUnauthorized: false, // For self-signed cert
    });

    this.socket.on('connect', () => {
      console.log('✅ Connected to backend:', this.socket.id);
    });

    this.socket.on('disconnect', () => {
      console.log('❌ Disconnected from backend');
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

