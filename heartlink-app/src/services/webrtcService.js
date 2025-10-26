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
  }

  setSocket(socket) {
    this.socket = socket;
    this.setupSocketListeners();
  }

  setupSocketListeners() {
    if (!this.socket) return;

    this.socket.on('user_joined', (data) => {
      console.log('👤 User joined:', data.id);
      this.remoteId = data.id;
    });

    this.socket.on('user_left', (data) => {
      console.log('👋 User left:', data.id);
      this.hangUp();
    });

    this.socket.on('offer', async (data) => {
      console.log('📞 Received offer from:', data.sender);
      this.remoteId = data.sender;
      await this.handleOffer(data.offer);
    });

    this.socket.on('answer', async (data) => {
      console.log('✅ Received answer from:', data.sender);
      await this.handleAnswer(data.answer);
    });

    this.socket.on('ice_candidate', async (data) => {
      console.log('🧊 Received ICE candidate');
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
      this.mediaRecorder = new MediaRecorder(this.localStream, { mimeType: 'audio/webm' });
      
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
        
        // Add to peer connection if active
        if (this.peerConnection) {
          this.peerConnection.addTrack(newVideoTrack, this.localStream);
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
      console.log('🎥 Received remote track');
      this.remoteStream = event.streams[0];
      if (this.onRemoteStream) {
        this.onRemoteStream(this.remoteStream);
      }
    };

    // Handle connection state changes
    this.peerConnection.onconnectionstatechange = () => {
      console.log('🔗 Connection state:', this.peerConnection.connectionState);
      if (this.peerConnection.connectionState === 'failed') {
        this.hangUp();
      }
    };
  }

  async startCall() {
    if (!this.remoteId || !this.localStream) {
      console.error('❌ Cannot start call: missing remote ID or local stream');
      return;
    }

    console.log('📞 Starting call...');
    this.createPeerConnection();

    // Add local tracks to peer connection
    this.localStream.getTracks().forEach(track => {
      this.peerConnection.addTrack(track, this.localStream);
    });

    try {
      const offer = await this.peerConnection.createOffer();
      await this.peerConnection.setLocalDescription(offer);
      this.socket.emit('offer', {
        offer: offer,
        target: this.remoteId
      });
      console.log('✅ Call initiated');
    } catch (error) {
      console.error('❌ Error creating offer:', error);
    }
  }

  async handleOffer(offer) {
    console.log('📞 Handling incoming call...');
    this.createPeerConnection();

    // Add local tracks
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => {
        this.peerConnection.addTrack(track, this.localStream);
      });
    }

    try {
      await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
      const answer = await this.peerConnection.createAnswer();
      await this.peerConnection.setLocalDescription(answer);
      this.socket.emit('answer', {
        answer: answer,
        target: this.remoteId
      });
      console.log('✅ Call accepted');
    } catch (error) {
      console.error('❌ Error handling offer:', error);
    }
  }

  async handleAnswer(answer) {
    try {
      await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
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

