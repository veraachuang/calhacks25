import React, { useState, useEffect, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import MediatorHoloSphere from "../components/MediatorHoloSphere";
import ProgressBar from "../components/ProgressBar";
import { useNavigate, useLocation } from "react-router-dom";
import * as THREE from "three";
import "../index.css";
import socketService from "../services/socketService";
import webrtcService from "../services/webrtcService";
import apiService from "../services/apiService";

export default function HeartLinkScene() {
  const [activeSpeaker, setActiveSpeaker] = useState("user1");
  const [matchReady, setMatchReady] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [peerConnected, setPeerConnected] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const [remoteUserName, setRemoteUserName] = useState("User 2");
  
  const flame1Ref = useRef(null);
  const flame2Ref = useRef(null);
  const scene1Ref = useRef(null);
  const scene2Ref = useRef(null);
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);

  const navigate = useNavigate();
  const location = useLocation();

  const {
    avatarName = "User 1",
    flameColor = "orange",
    spiceLevel = 2,
    personality = "",
    hobbies = "",
    lookingFor = "",
    sessionId = null,
    userRole = null,
  } = location.state || {};

  // Debug log
  console.log('🔍 HeartLinkScene initialized with:', {
    sessionId,
    userRole,
    avatarName,
  });

  const flameColors = {
    orange: 0xff4500,
    blue: 0x4169e1,
    purple: 0x8b00ff,
    green: 0x00ff41,
    pink: 0xff1493,
    white: 0xffffff,
  };

  const getCurrentColor = (colorId) => flameColors[colorId] || 0xff4500;

  // Initialize WebRTC and Socket.IO
  useEffect(() => {
    const initConnection = async () => {
      try {
        const socket = socketService.getSocket();
        if (!socket) {
          console.error('❌ No socket connection');
          return;
        }

        // Set up WebRTC service with socket
        webrtcService.setSocket(socket);

        // Get local media (audio only by default)
        await webrtcService.getLocalMedia(false);
        setIsConnected(true);

        // Set up stream callbacks
        webrtcService.onLocalStream = (stream) => {
          console.log('🎤 Local stream received:', stream.getTracks().map(t => `${t.kind}: ${t.enabled}`));
          if (localVideoRef.current) {
            localVideoRef.current.srcObject = stream;
            console.log('✅ Local video element updated');
          } else {
            console.log('⚠️ Local video ref not ready');
          }
        };

        webrtcService.onRemoteStream = (stream) => {
          console.log('🎥 Remote stream received:', stream.getTracks().map(t => `${t.kind}: ${t.enabled}`));
          if (remoteVideoRef.current) {
            const videoEl = remoteVideoRef.current;
            videoEl.srcObject = stream;
            
            // Ensure volume is up and not muted
            videoEl.volume = 1.0;
            videoEl.muted = false;
            
            console.log('🔊 Video element settings:', {
              volume: videoEl.volume,
              muted: videoEl.muted,
              paused: videoEl.paused
            });
            
            // Explicitly play the video element to ensure audio plays
            videoEl.play().then(() => {
              console.log('✅ Remote video element updated and playing');
              console.log('   Final state - volume:', videoEl.volume, 'muted:', videoEl.muted);
            }).catch(err => {
              console.warn('⚠️ Autoplay prevented, user interaction may be needed:', err);
            });
          } else {
            console.log('⚠️ Remote video ref not ready, will retry...');
            // Retry after a short delay if video element isn't ready
            setTimeout(() => {
              if (remoteVideoRef.current) {
                remoteVideoRef.current.srcObject = stream;
                remoteVideoRef.current.play().catch(err => {
                  console.warn('⚠️ Autoplay prevented (retry):', err);
                });
                console.log('✅ Remote video element updated (retry)');
              }
            }, 500);
          }
          setPeerConnected(true);
        };

        // Listen for user joined (peer available)
        socket.on('user_joined', (data) => {
          console.log('👤 Peer joined:', data.id);
          console.log('   My role:', userRole);
          console.log('   Should I call?', userRole === 'B' ? 'YES (I am User B)' : 'NO (I am User A, waiting)');
          setPeerConnected(true);
          
          // Only User B (joiner) initiates the call to avoid both peers calling
          if (userRole === 'B') {
            console.log('🔄 User B initiating call...');
            setTimeout(() => webrtcService.startCall(), 1000);
          } else {
            console.log('👤 User A waiting for call from User B...');
          }
        });

        // Re-join the matchmaking room to trigger user_joined events
        // This ensures we receive events for users already in the room
        console.log('🔄 Re-joining matchmaking room to sync with peers...');
        socketService.joinRoom('matchmaking');

        // If we're User B, request the session info to get User A's socket ID
        if (sessionId && userRole === 'B') {
          console.log('🔍 User B checking for User A in session...');
          // Ask backend to tell us about User A
          socket.emit('request_peer_info', { session_id: sessionId });
        }

        // Listen for transcript updates
        socket.on('transcript_update', (data) => {
          console.log('📝 Transcript:', data);
          setTranscripts(prev => [...prev, {
            speaker: data.user_id === socket.id ? avatarName : remoteUserName,
            text: data.text,
            type: 'user'
          }]);
        });

        // Listen for AI interjections
        socket.on('ai_interjection', (data) => {
          console.log('🤖 AI:', data.message);
          setTranscripts(prev => [...prev, {
            speaker: 'AI',
            text: data.message,
            type: 'ai'
          }]);
        });

        // Load both profiles to get remote user name
        if (sessionId) {
          try {
            const profiles = await apiService.getBothProfiles(sessionId);
            const remoteProfile = userRole === 'A' ? profiles.B : profiles.A;
            if (remoteProfile && remoteProfile.name) {
              setRemoteUserName(remoteProfile.name);
            }
          } catch (error) {
            console.error('Failed to load profiles:', error);
          }
        }

      } catch (error) {
        console.error('❌ Error initializing connection:', error);
      }
    };

    initConnection();

    return () => {
      // Cleanup on unmount
      webrtcService.cleanup();
    };
  }, [sessionId, userRole, avatarName, remoteUserName]);

  // 🔥 reusable flame builder
  const createFlame = (canvasRef, sceneRef, colorId) => {
    if (!canvasRef.current) return;

    if (sceneRef.current) {
      while (sceneRef.current.children.length > 0) {
        const obj = sceneRef.current.children[0];
        sceneRef.current.remove(obj);
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
      }
    }

    const color = getCurrentColor(colorId);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      alpha: true,
      antialias: true,
    });
    renderer.setSize(200, 200);
    camera.position.z = 5;
    sceneRef.current = scene;

    const flameParticles = [];
    const particleCount = 180;

    for (let i = 0; i < particleCount; i++) {
      const size = Math.random() * 0.25 + 0.1;
      const geometry = new THREE.SphereGeometry(size, 8, 8);
      const material = new THREE.MeshBasicMaterial({
        color,
        transparent: true,
        opacity: 0.8,
      });
      const particle = new THREE.Mesh(geometry, material);

      const heightRatio = Math.random();
      const angle = Math.random() * Math.PI * 2;
      let width;
      if (heightRatio < 0.3) width = 0.15 + (heightRatio / 0.3) * 0.25;
      else if (heightRatio < 0.6) width = 0.4 - ((heightRatio - 0.3) / 0.3) * 0.05;
      else width = 0.35 - ((heightRatio - 0.6) / 0.4) * 0.33;

      const radius = Math.random() * width;
      particle.position.x = Math.cos(angle) * radius;
      particle.position.z = Math.sin(angle) * radius;
      particle.position.y = heightRatio * 2.2 - 0.3;

      particle.userData = {
        speed: Math.random() * 0.015 + 0.008,
        wobble: Math.random() * 0.06,
        wobbleSpeed: Math.random() * 2 + 1,
        angle,
        baseRadius: radius,
      };

      scene.add(particle);
      flameParticles.push(particle);
    }

    const pointLight = new THREE.PointLight(color, 2, 10);
    pointLight.position.set(0, 0, 0);
    scene.add(pointLight);
    scene.add(new THREE.AmbientLight(0x404040));

    let time = 0;
    let animationId;
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      time += 0.016;

      flameParticles.forEach((p, i) => {
        p.position.y += p.userData.speed;

        const heightPos = (p.position.y + 0.3) / 2.2;
        let currentWidth;
        if (heightPos < 0.3) currentWidth = 0.15 + (heightPos / 0.3) * 0.25;
        else if (heightPos < 0.6) currentWidth = 0.4 - ((heightPos - 0.3) / 0.3) * 0.05;
        else currentWidth = 0.35 - ((heightPos - 0.6) / 0.4) * 0.33;

        const currentRadius = p.userData.baseRadius * (currentWidth / 0.4);
        const wobbleX = Math.sin(time * p.userData.wobbleSpeed + i) * p.userData.wobble;
        const wobbleZ = Math.cos(time * p.userData.wobbleSpeed + i) * p.userData.wobble;

        p.position.x = Math.cos(p.userData.angle) * currentRadius + wobbleX;
        p.position.z = Math.sin(p.userData.angle) * currentRadius + wobbleZ;

        // keep single color
        p.material.color.setHex(color);
        p.material.opacity = Math.max(0, 1 - (p.position.y + 0.3) / 2.5);
        if (p.position.y > 1.9) p.position.y = -0.3;
      });

      pointLight.intensity = 2 + Math.sin(time * 5) * 0.3;
      pointLight.color.setHex(color);

      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationId);
      flameParticles.forEach((p) => {
        p.geometry.dispose();
        p.material.dispose();
        scene.remove(p);
      });
      scene.clear();
      renderer.dispose();
    };
  };

  // mount both flames
  useEffect(() => {
    if (!isVideoEnabled) {
      const cleanup1 = createFlame(flame1Ref, scene1Ref, flameColor);
      const cleanup2 = createFlame(flame2Ref, scene2Ref, "pink");
      return () => {
        if (cleanup1) cleanup1();
        if (cleanup2) cleanup2();
      };
    }
  }, [flameColor, isVideoEnabled]);

  // Handle video toggle
  const handleToggleVideo = async () => {
    try {
      const enabled = await webrtcService.toggleVideo();
      setIsVideoEnabled(enabled);
    } catch (error) {
      console.error('Failed to toggle video:', error);
      alert('Failed to enable video. Please check camera permissions.');
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden text-white bg-[#050514]">
      {/* 3D Mediator */}
      <Canvas camera={{ position: [0, 0, 8], fov: 60 }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[0, 3, 5]} intensity={2} color="#ffffff" />
        <MediatorHoloSphere position={[0, 0, 0]} />
      </Canvas>

      {/* Progress */}
      <ProgressBar onMatchReady={(ready) => setMatchReady(ready)} />

      {/* Back */}
      <button
        onClick={() => navigate("/")}
        className="absolute top-6 left-6 px-4 py-2 rounded-lg bg-white/10 text-gray-300 hover:text-white border border-white/20 backdrop-blur-md z-20"
      >
        ← Back
      </button>

      {/* Connection Status */}
      <div className="absolute top-6 right-6 px-4 py-2 rounded-lg bg-white/10 border border-white/20 backdrop-blur-md z-20">
        <span className="text-sm">
          {!isConnected && "🔴 Connecting..."}
          {isConnected && !peerConnected && "🟡 Waiting for peer..."}
          {isConnected && peerConnected && "🟢 Connected"}
        </span>
      </div>

      {/* Video Toggle Button */}
      <button
        onClick={handleToggleVideo}
        disabled={!isConnected}
        className="absolute top-6 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg bg-white/10 text-gray-300 hover:text-white border border-white/20 backdrop-blur-md z-20 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isVideoEnabled ? "📹 Hide Video" : "📹 Show Video"}
      </button>

      {/* Match button */}
      <div className="absolute top-[60px] left-1/2 -translate-x-1/2 z-20">
        <button
          disabled={!matchReady}
          className={`px-6 py-2 rounded-full font-semibold border backdrop-blur-md transition-all ${
            matchReady
              ? "bg-gradient-to-r from-pink-500 to-purple-500 text-white border-pink-400 shadow-lg hover:scale-105"
              : "bg-white/10 text-gray-400 border-white/20 cursor-not-allowed"
          }`}
        >
          💞 Match
        </button>
      </div>

      {/* Flames or Video */}
      <div className="absolute inset-0 flex items-center justify-between px-24 pointer-events-none">
        <div className="flex flex-col items-center">
          {/* Canvas flame (shown when video disabled) */}
          {!isVideoEnabled && <canvas ref={flame1Ref} className="w-[200px] h-[200px]" />}
          
          {/* Video element (always in DOM for audio, but hidden when video disabled) */}
          <video 
            ref={localVideoRef} 
            autoPlay 
            muted 
            playsInline 
            className={`rounded-2xl border-2 border-white/20 shadow-xl pointer-events-auto ${
              isVideoEnabled 
                ? "w-[300px] h-[225px]" 
                : "hidden"
            }`}
          />
          <p className="text-white/80 font-semibold mt-3">{avatarName}</p>
        </div>
        <div className="flex flex-col items-center">
          {/* Canvas flame (shown when video disabled) */}
          {!isVideoEnabled && <canvas ref={flame2Ref} className="w-[200px] h-[200px]" />}
          
          {/* Video element (always in DOM for audio, but hidden when video disabled) */}
          <video 
            ref={remoteVideoRef} 
            autoPlay 
            playsInline 
            className={`rounded-2xl border-2 border-white/20 shadow-xl pointer-events-auto ${
              isVideoEnabled 
                ? "w-[300px] h-[225px]" 
                : "hidden"
            }`}
          />
          <p className="text-white/80 font-semibold mt-3">{remoteUserName}</p>
        </div>
      </div>

      {/* AI Chat */}
      <div
        className="glass-box absolute bottom-16 left-1/2 -translate-x-1/2 w-3/5 p-6 overflow-y-auto"
        style={{ maxWidth: "700px", maxHeight: "300px" }}
      >
        <h2 className="text-pink-400 font-semibold text-xl mb-3 text-center">HeartLink AI Mediator 🤍</h2>
        <div className="text-gray-200 text-base leading-relaxed space-y-2 text-left">
          {transcripts.length === 0 ? (
            <p className="text-center text-gray-400 italic">Start talking to see transcripts...</p>
          ) : (
            transcripts.slice(-5).map((t, idx) => (
              <p key={idx}>
                {t.type === 'ai' ? (
                  <span className="text-pink-300 font-bold">AI: </span>
                ) : (
                  <span className="font-bold">{t.speaker}: </span>
                )}
                <span>{t.text}</span>
              </p>
            ))
          )}
        </div>
      </div>
    </div>
  );
}