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
    } catch (error) {
        console.error('Error accessing media devices:', error);
        alert('Could not access camera/microphone. Please check permissions.');
    }
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

// Initialize on page load
window.addEventListener('load', () => {
    initializeSocket();
});
