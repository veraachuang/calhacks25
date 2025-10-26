const configuration = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ]
};

class WebRTCService {
  constructor() {
    this.peerConnection = null;
    this.localStream = null;
    this.remoteStream = null;
    this.socket = null;
    this.remoteId = null;
    this.isVideoEnabled = false;
    this.onRemoteStream = null;
    this.onLocalStream = null;
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.isRecording = false;
    this.isCallInitiated = false; // Flag to prevent duplicate calls
  }

  setSocket(socket) {
    this.socket = socket;
    this.setupSocketListeners();
  }

  setupSocketListeners() {
    if (!this.socket) return;

    this.socket.on('user_joined', (data) => {
      console.log('👤 User joined:', data.id);
      console.log('   My socket ID:', this.socket.id);
      console.log('   Setting remoteId to:', data.id);
      this.remoteId = data.id;
    });

    this.socket.on('user_left', (data) => {
      console.log('👋 User left:', data.id);
      this.hangUp();
    });

    this.socket.on('offer', async (data) => {
      console.log('📞 Received offer from:', data.sender);
      console.log('   My socket ID:', this.socket.id);
      console.log('   Offer details:', data.offer.type);
      this.remoteId = data.sender;
      await this.handleOffer(data.offer);
    });

    this.socket.on('answer', async (data) => {
      console.log('✅ Received answer from:', data.sender);
      console.log('   My socket ID:', this.socket.id);
      console.log('   Answer details:', data.answer.type);
      await this.handleAnswer(data.answer);
    });

    this.socket.on('ice_candidate', async (data) => {
      console.log('🧊 Received ICE candidate from:', data.sender);
      console.log('   Candidate type:', data.candidate?.candidate ? 'valid' : 'null');
      await this.handleIceCandidate(data.candidate);
    });
  }

  async getLocalMedia(enableVideo = false) {
    try {
      this.isVideoEnabled = enableVideo;
      this.localStream = await navigator.mediaDevices.getUserMedia({
        video: enableVideo,
        audio: true
      });

      console.log('🎤 Got local media:', enableVideo ? 'audio + video' : 'audio only');
      
      // Check local track states
      this.localStream.getTracks().forEach(track => {
        console.log(`   Local ${track.kind} track:`, {
          enabled: track.enabled,
          muted: track.muted,
          readyState: track.readyState
        });
      });
      
      if (this.onLocalStream) {
        this.onLocalStream(this.localStream);
      }

      // Start automatic audio capture for STT
      this.startAudioCapture();

      return this.localStream;
    } catch (error) {
      console.error('❌ Error getting local media:', error);
      throw error;
    }
  }

  startAudioCapture() {
    if (!this.localStream || !this.socket) return;

    try {
      // Create audio-only stream for STT (even if video is enabled)
      const audioTrack = this.localStream.getAudioTracks()[0];
      if (!audioTrack) {
        console.warn('⚠️ No audio track available for capture');
        return;
      }
      
      const audioOnlyStream = new MediaStream([audioTrack]);
      this.mediaRecorder = new MediaRecorder(audioOnlyStream, { mimeType: 'audio/webm' });
      
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        this.audioChunks = [];

        // Convert to base64 and send via socket
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1];
          if (this.socket) {
            this.socket.emit('audio_chunk', {
              audio: base64Audio,
              room: 'matchmaking'
            });
          }
        };

        // Restart recording for continuous capture
        if (this.isRecording && this.mediaRecorder && this.mediaRecorder.state === 'inactive') {
          this.mediaRecorder.start();
          setTimeout(() => {
            if (this.isRecording && this.mediaRecorder && this.mediaRecorder.state === 'recording') {
              this.mediaRecorder.stop();
            }
          }, 3000); // Capture 3-second chunks
        }
      };

      this.isRecording = true;
      this.mediaRecorder.start();

      // Stop after 3 seconds to create chunks
      setTimeout(() => {
        if (this.isRecording && this.mediaRecorder && this.mediaRecorder.state === 'recording') {
          this.mediaRecorder.stop();
        }
      }, 3000);

      console.log('🎤 Audio capture started for STT');
    } catch (error) {
      console.error('❌ Error starting audio capture:', error);
    }
  }

  stopAudioCapture() {
    this.isRecording = false;
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    console.log('🛑 Audio capture stopped');
  }

  async toggleVideo() {
    if (!this.localStream) return;

    const videoTrack = this.localStream.getVideoTracks()[0];
    
    if (videoTrack) {
      // Has video track, toggle it
      this.isVideoEnabled = !videoTrack.enabled;
      videoTrack.enabled = this.isVideoEnabled;
      console.log('📹 Video toggled:', this.isVideoEnabled ? 'ON' : 'OFF');
      return this.isVideoEnabled;
    } else {
      // No video track, add one
      try {
        const videoStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        const newVideoTrack = videoStream.getVideoTracks()[0];
        this.localStream.addTrack(newVideoTrack);

        // Add to peer connection if active and trigger renegotiation
        if (this.peerConnection) {
          this.peerConnection.addTrack(newVideoTrack, this.localStream);

          // Renegotiate to send video to peer
          console.log('🔄 Renegotiating connection to add video...');
          const offer = await this.peerConnection.createOffer();
          await this.peerConnection.setLocalDescription(offer);

          // Send offer to peer via socket
          if (this.socket && this.targetId) {
            this.socket.emit('offer', {
              target: this.targetId,
              offer: offer
            });
            console.log('📤 Sent renegotiation offer to peer');
          }
        }

        this.isVideoEnabled = true;
        console.log('📹 Video enabled');

        if (this.onLocalStream) {
          this.onLocalStream(this.localStream);
        }

        return true;
      } catch (error) {
        console.error('❌ Error enabling video:', error);
        throw error;
      }
    }
  }

  createPeerConnection() {
    this.peerConnection = new RTCPeerConnection(configuration);

    // Handle ICE candidates
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate && this.socket) {
        this.socket.emit('ice_candidate', {
          candidate: event.candidate,
          target: this.remoteId
        });
      }
    };

    // Handle remote stream
    this.peerConnection.ontrack = (event) => {
      const track = event.track;
      console.log('🎥 Received remote track:', track.kind);
      console.log('   Track enabled:', track.enabled);
      console.log('   Track muted:', track.muted);
      console.log('   Track readyState:', track.readyState);
      
      // Listen for unmute event - track.muted is read-only and changes automatically
      track.addEventListener('unmute', () => {
        console.log('🔊 Remote track unmuted!');
      });
      
      track.addEventListener('mute', () => {
        console.warn('🔇 Remote track muted!');
      });
      
      this.remoteStream = event.streams[0];
      console.log('🎥 Remote stream tracks:', this.remoteStream.getTracks().map(t => `${t.kind}: enabled=${t.enabled}, muted=${t.muted}, readyState=${t.readyState}`));
      
      // Note: track.muted is READ-ONLY and reflects whether data is flowing
      // If it stays muted, the remote peer isn't sending audio data
      if (track.muted) {
        console.warn('⚠️ Remote track is muted - waiting for remote peer to send audio...');
      }
      
      if (this.onRemoteStream) {
        this.onRemoteStream(this.remoteStream);
      }
    };

    // Handle connection state changes
    this.peerConnection.onconnectionstatechange = () => {
      const state = this.peerConnection.connectionState;
      console.log('🔗 Connection state:', state);
      
      if (state === 'connected') {
        console.log('✅ WebRTC connection established!');
        console.log('   Remote stream:', this.remoteStream ? 'exists' : 'none');
        console.log('   Remote tracks:', this.remoteStream?.getTracks().map(t => `${t.kind}: ${t.enabled}`) || []);
      } else if (state === 'failed') {
        console.error('❌ Connection failed');
        this.hangUp();
      } else if (state === 'disconnected') {
        console.warn('⚠️ Connection disconnected');
      }
    };
  }

  async startCall() {
    if (!this.remoteId || !this.localStream) {
      console.error('❌ Cannot start call:');
      console.error('   Remote ID:', this.remoteId);
      console.error('   Local stream:', this.localStream ? 'exists' : 'missing');
      console.error('   Local tracks:', this.localStream?.getTracks().map(t => t.kind));
      return;
    }

    // Prevent duplicate calls
    if (this.isCallInitiated) {
      console.warn('⚠️ Call already initiated, skipping duplicate');
      return;
    }
    this.isCallInitiated = true;

    console.log('📞 Starting call...');
    console.log('   My socket ID:', this.socket.id);
    console.log('   Remote ID:', this.remoteId);
    console.log('   Local stream tracks:', this.localStream.getTracks().map(t => `${t.kind}: ${t.enabled}`));
    
    this.createPeerConnection();

    // Add local tracks to peer connection
    this.localStream.getTracks().forEach(track => {
      const sender = this.peerConnection.addTrack(track, this.localStream);
      console.log('   Added track to peer connection:', track.kind, 'enabled:', track.enabled);
    });

    try {
      const offer = await this.peerConnection.createOffer();
      await this.peerConnection.setLocalDescription(offer);
      console.log('   Created offer:', offer.type);
      this.socket.emit('offer', {
        offer: offer,
        target: this.remoteId
      });
      console.log('✅ Call initiated - offer sent to:', this.remoteId);
    } catch (error) {
      console.error('❌ Error creating offer:', error);
    }
  }

  async handleOffer(offer) {
    console.log('📞 Handling incoming call...');
    console.log('   My socket ID:', this.socket.id);
    console.log('   Remote ID (sender):', this.remoteId);
    console.log('   Offer type:', offer.type);
    
    this.createPeerConnection();

    // Add local tracks
    if (this.localStream) {
      console.log('   Adding local tracks to peer connection...');
      this.localStream.getTracks().forEach(track => {
        this.peerConnection.addTrack(track, this.localStream);
        console.log('   Added track:', track.kind, 'enabled:', track.enabled);
      });
    } else {
      console.warn('⚠️ No local stream available when handling offer!');
    }

    try {
      await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
      console.log('   Remote description set');
      
      const answer = await this.peerConnection.createAnswer();
      console.log('   Created answer:', answer.type);
      
      await this.peerConnection.setLocalDescription(answer);
      console.log('   Local description set');
      
      this.socket.emit('answer', {
        answer: answer,
        target: this.remoteId
      });
      console.log('✅ Call accepted - answer sent to:', this.remoteId);
    } catch (error) {
      console.error('❌ Error handling offer:', error);
    }
  }

  async handleAnswer(answer) {
    try {
      // Check if we already have a remote description
      if (this.peerConnection.currentRemoteDescription) {
        console.warn('⚠️ Remote description already set, skipping duplicate answer');
        return;
      }
      
      await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
      console.log('✅ Answer processed successfully');
    } catch (error) {
      console.error('❌ Error handling answer:', error);
    }
  }

  async handleIceCandidate(candidate) {
    try {
      await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
    } catch (error) {
      console.error('❌ Error adding ICE candidate:', error);
    }
  }

  hangUp() {
    if (this.peerConnection) {
      this.peerConnection.close();
      this.peerConnection = null;
    }
    this.remoteStream = null;
    this.isCallInitiated = false; // Reset flag
    console.log('📴 Call ended');
  }

  cleanup() {
    this.stopAudioCapture();
    this.hangUp();
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => track.stop());
      this.localStream = null;
    }
  }
}

// Singleton instance
const webrtcService = new WebRTCService();
export default webrtcService;

