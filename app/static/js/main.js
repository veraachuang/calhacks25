// WebRTC Configuration
const configuration = {
    iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
    ]
};

// Global variables
let socket;
let localStream;
let peerConnection;
let myId;
let remoteId;
let currentRoom;
let isVideoEnabled = false; // Start with voice-only mode

// STT variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let sttInterval;

// DOM elements
const localVideo = document.getElementById('localVideo');
const remoteVideo = document.getElementById('remoteVideo');
const myIdElement = document.getElementById('myId');
const statusElement = document.getElementById('connectionStatus');
const joinBtn = document.getElementById('joinBtn');
const callBtn = document.getElementById('callBtn');
const hangupBtn = document.getElementById('hangupBtn');
const toggleVideoBtn = document.getElementById('toggleVideoBtn');
const roomInput = document.getElementById('roomInput');

// Initialize Socket.IO connection
function initializeSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
        updateStatus('Connected to server');
    });

    socket.on('user_id', (data) => {
        myId = data.id;
        myIdElement.textContent = myId;
        console.log('My ID:', myId);
    });

    socket.on('user_joined', async (data) => {
        console.log('User joined:', data.id);
        remoteId = data.id;
        updateStatus(`User ${data.id} joined the room`);
        callBtn.disabled = false;
    });

    socket.on('user_left', (data) => {
        console.log('User left:', data.id);
        updateStatus('Remote user left');
        if (peerConnection) {
            hangUp();
        }
    });

    socket.on('offer', async (data) => {
        console.log('Received offer from:', data.sender);
        remoteId = data.sender;
        await handleOffer(data.offer);
    });

    socket.on('answer', async (data) => {
        console.log('Received answer from:', data.sender);
        await handleAnswer(data.answer);
    });

    socket.on('ice_candidate', async (data) => {
        console.log('Received ICE candidate');
        await handleIceCandidate(data.candidate);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updateStatus('Disconnected from server');
    });

    socket.on('transcript_update', (data) => {
        console.log('Transcript:', data.text);
        displayTranscript(data);
    });

    socket.on('ai_interjection', (data) => {
        console.log('AI interjected:', data.message);
        displayAIInterjection(data.message);
        // Optionally speak the AI response using TTS
        speakAIResponse(data.message);
    });

    socket.on('stt_error', (data) => {
        console.error('STT Error:', data.error);
    });
}

// Join a room
async function joinRoom() {
    const room = roomInput.value.trim();
    if (!room) {
        alert('Please enter a room name');
        return;
    }

    currentRoom = room;
    socket.emit('join', { room: room });
    updateStatus(`Joined room: ${room}`);
    joinBtn.disabled = true;
    roomInput.disabled = true;

    // Get local media
    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: isVideoEnabled,
            audio: true
        });
        localVideo.srcObject = localStream;
        toggleVideoBtn.disabled = false;
        updateStatus(isVideoEnabled ? 'Camera and microphone ready' : 'Microphone ready (voice only)');

        // Start automatic STT
        startAutomaticSTT();
    } catch (error) {
        console.error('Error accessing media devices:', error);
        alert('Could not access camera/microphone. Please check permissions.');
    }
}

// Start automatic speech-to-text capture
function startAutomaticSTT() {
    if (!localStream) {
        console.error('No local stream available');
        return;
    }

    // Create MediaRecorder to capture audio
    const options = { mimeType: 'audio/webm' };
    mediaRecorder = new MediaRecorder(localStream, options);

    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            audioChunks.push(event.data);
        }
    };

    mediaRecorder.onstop = () => {
        // Convert audio chunks to blob and send to server
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        audioChunks = [];

        // Convert to base64 and send via socket
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            socket.emit('audio_chunk', {
                audio: base64Audio,
                room: currentRoom
            });
        };

        // Restart recording for continuous capture
        if (isRecording) {
            mediaRecorder.start();
            setTimeout(() => {
                if (isRecording && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                }
            }, 3000); // Capture 3-second chunks
        }
    };

    // Start recording
    isRecording = true;
    mediaRecorder.start();

    // Stop after 3 seconds to create chunks
    setTimeout(() => {
        if (isRecording && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
    }, 3000);

    console.log('Automatic STT started');
    updateStatus('Speech-to-text active');
}

// Stop automatic STT
function stopAutomaticSTT() {
    isRecording = false;
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
    console.log('Automatic STT stopped');
}

// Start a call
async function startCall() {
    if (!remoteId) {
        alert('No remote user available');
        return;
    }

    updateStatus('Starting call...');
    callBtn.disabled = true;
    hangupBtn.disabled = false;

    // Create peer connection
    createPeerConnection();

    // Add local tracks to peer connection
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
    });

    // Create and send offer
    try {
        const offer = await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        socket.emit('offer', {
            offer: offer,
            target: remoteId
        });
        updateStatus('Call initiated');
    } catch (error) {
        console.error('Error creating offer:', error);
        updateStatus('Failed to start call');
    }
}

// Create peer connection
function createPeerConnection() {
    peerConnection = new RTCPeerConnection(configuration);

    // Handle ICE candidates
    peerConnection.onicecandidate = (event) => {
        if (event.candidate) {
            socket.emit('ice_candidate', {
                candidate: event.candidate,
                target: remoteId
            });
        }
    };

    // Handle remote stream
    peerConnection.ontrack = (event) => {
        console.log('Received remote track');
        remoteVideo.srcObject = event.streams[0];
        updateStatus('Call connected');
    };

    // Handle connection state changes
    peerConnection.onconnectionstatechange = () => {
        console.log('Connection state:', peerConnection.connectionState);
        if (peerConnection.connectionState === 'connected') {
            updateStatus('Call connected');
        } else if (peerConnection.connectionState === 'disconnected') {
            updateStatus('Call disconnected');
        } else if (peerConnection.connectionState === 'failed') {
            updateStatus('Connection failed');
            hangUp();
        }
    };
}

// Handle incoming offer
async function handleOffer(offer) {
    updateStatus('Incoming call...');
    callBtn.disabled = true;
    hangupBtn.disabled = false;

    // Create peer connection
    createPeerConnection();

    // Add local tracks
    localStream.getTracks().forEach(track => {
        peerConnection.addTrack(track, localStream);
    });

    try {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        socket.emit('answer', {
            answer: answer,
            target: remoteId
        });
        updateStatus('Call accepted');
    } catch (error) {
        console.error('Error handling offer:', error);
        updateStatus('Failed to accept call');
    }
}

// Handle incoming answer
async function handleAnswer(answer) {
    try {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (error) {
        console.error('Error handling answer:', error);
    }
}

// Handle ICE candidate
async function handleIceCandidate(candidate) {
    try {
        await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
    } catch (error) {
        console.error('Error adding ICE candidate:', error);
    }
}

// Hang up
function hangUp() {
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }

    stopAutomaticSTT();
    remoteVideo.srcObject = null;
    callBtn.disabled = false;
    hangupBtn.disabled = true;
    updateStatus('Call ended');
}

// Toggle video on/off
function toggleVideo() {
    const videoTrack = localStream.getVideoTracks()[0];
    
    if (videoTrack) {
        isVideoEnabled = !videoTrack.enabled;
        videoTrack.enabled = isVideoEnabled;
        toggleVideoBtn.textContent = isVideoEnabled ? '📹 Video Off' : '📹 Video On';
        updateStatus(isVideoEnabled ? 'Video enabled' : 'Video disabled (voice only)');
    } else {
        // No video track, need to add one
        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(stream => {
                const videoTrack = stream.getVideoTracks()[0];
                localStream.addTrack(videoTrack);
                localVideo.srcObject = localStream;
                
                // Add to peer connection if active
                if (peerConnection) {
                    peerConnection.addTrack(videoTrack, localStream);
                }
                
                isVideoEnabled = true;
                toggleVideoBtn.textContent = '📹 Video Off';
                updateStatus('Video enabled');
            })
            .catch(error => {
                console.error('Error enabling video:', error);
                alert('Could not enable video');
            });
    }
}

// Update status display
function updateStatus(message) {
    statusElement.textContent = message;
    console.log('Status:', message);
}

// Display transcript in console (can be extended to UI)
function displayTranscript(data) {
    console.log(`[Transcript] User ${data.user_id}: ${data.text}`);
    // Could add UI element to show transcripts in real-time
}

// Display AI interjection
function displayAIInterjection(message) {
    console.log(`[AI Agent] ${message}`);
    updateStatus(`AI: ${message.substring(0, 50)}...`);

    // Show notification or UI popup
    if (Notification.permission === 'granted') {
        new Notification('AI Assistant', {
            body: message,
            icon: '/static/images/ai-icon.png'
        });
    }
}

// Speak AI response using Fish Audio TTS
async function speakAIResponse(text) {
    try {
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        if (data.audio) {
            // Decode base64 audio and play it
            const audioData = atob(data.audio);
            const arrayBuffer = new ArrayBuffer(audioData.length);
            const view = new Uint8Array(arrayBuffer);
            for (let i = 0; i < audioData.length; i++) {
                view[i] = audioData.charCodeAt(i);
            }

            const audioBlob = new Blob([arrayBuffer], { type: 'audio/wav' });
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);

            audio.play();
            console.log('Playing AI response audio');
        }
    } catch (error) {
        console.error('Error playing AI response:', error);
    }
}

// Initialize on page load
window.addEventListener('load', () => {
    initializeSocket();

    // Request notification permission
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
});
