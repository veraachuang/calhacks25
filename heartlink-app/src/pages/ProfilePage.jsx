import React, { useState, useEffect, useRef } from "react";
import { Zap, Palette } from "lucide-react";
import * as THREE from "three";
import { useNavigate } from "react-router-dom";
import logo from "./logo2.png";
import socketService from "../services/socketService";
import apiService from "../services/apiService";

export default function ProfilePage() {
  const [avatarName, setAvatarName] = useState("");
  const [spiceLevel, setSpiceLevel] = useState(2);
  const [flameColor, setFlameColor] = useState("orange");
  const [personality, setPersonality] = useState("");
  const [hobbies, setHobbies] = useState("");
  const [lookingFor, setLookingFor] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);

  const canvasRef = useRef(null);
  const sceneRef = useRef(null);
  const navigate = useNavigate();

  // Define available colors
  const flameColors = [
    { id: "orange", name: "Classic", color: 0xff4500 },
    { id: "blue", name: "Cool Blue", color: 0x4169e1 },
    { id: "purple", name: "Mystic", color: 0x8b00ff },
    { id: "green", name: "Emerald", color: 0x00ff41 },
    { id: "pink", name: "Hot Pink", color: 0xff1493 },
    { id: "white", name: "Pure", color: 0xffffff },
  ];

  const spiceLevels = [
    { level: 1, label: "Spark", desc: "Light & casual vibes", color: "from-blue-400 to-cyan-400" },
    { level: 2, label: "Warm", desc: "Friendly & engaging", color: "from-green-400 to-emerald-400" },
    { level: 3, label: "Hot", desc: "Deep & meaningful", color: "from-orange-400 to-amber-400" },
    { level: 4, label: "Inferno", desc: "Bold & unfiltered", color: "from-red-400 to-rose-400" },
  ];

  const getCurrentColor = () => {
    return flameColors.find((f) => f.id === flameColor)?.color || 0xff4500;
  };

  // === 🔥 Flame Renderer ===
  useEffect(() => {
    if (!canvasRef.current) return;

    // Clean up old scene
    if (sceneRef.current) {
      while (sceneRef.current.children.length > 0) {
        const obj = sceneRef.current.children[0];
        sceneRef.current.remove(obj);
        if (obj.geometry) obj.geometry.dispose();
        if (obj.material) obj.material.dispose();
      }
    }

    // Scene + Camera + Renderer
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

    // Create flame particles
    const flameParticles = [];
    const particleCount = 180;
    const color = getCurrentColor();

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

    // Lights
    const pointLight = new THREE.PointLight(color, 2, 10);
    pointLight.position.set(0, 0, 0);
    scene.add(pointLight);
    scene.add(new THREE.AmbientLight(0x404040));

    // Animation loop
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

        // 🔥 Entire flame = one color
        p.material.color.setHex(color);

        // Fade out & loop
        p.material.opacity = Math.max(0, 1 - (p.position.y + 0.3) / 2.5);
        if (p.position.y > 1.9) p.position.y = -0.3;
      });

      // Flicker effect
      pointLight.intensity = 2 + Math.sin(time * 5) * 0.3;
      pointLight.color.setHex(color);

      renderer.render(scene, camera);
    };
    animate();

    // Cleanup
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
  }, [flameColor]);

  // Navigation
  const handleStartMatching = async () => {
    if (avatarName && personality && hobbies && lookingFor) {
      setIsConnecting(true);
      try {
        // Connect to backend
        console.log('🔌 Connecting to backend...');
        const socket = socketService.connect();
        
        // Wait for socket to actually connect
        await new Promise((resolve, reject) => {
          if (socket.connected) {
            resolve();
          } else {
            const timeout = setTimeout(() => reject(new Error('Connection timeout')), 10000);
            socket.once('connect', () => {
              clearTimeout(timeout);
              resolve();
            });
            socket.once('connect_error', (err) => {
              clearTimeout(timeout);
              reject(err);
            });
          }
        });
        
        console.log('✅ Socket connected');
        
        // Join room (using a default room for matchmaking)
        const roomName = 'matchmaking';
        socketService.joinRoom(roomName);
        
        // Wait for session_info event with timeout
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => {
            reject(new Error('Timeout waiting for session. Check your connection.'));
          }, 10000); // 10 second timeout
          
          socket.once('session_info', async (data) => {
            clearTimeout(timeout);
            console.log('📋 Got session info:', data);
            
            // Prepare profile data matching backend schema
            const profileData = {
              name: avatarName,
              personality_type: personality,
              hobbies: hobbies.split(',').map(h => h.trim()).filter(h => h),
              goal: lookingFor,
              spiceLevel: spiceLevel,
              flameColor: flameColor,
              interests: hobbies.split(',').map(h => h.trim()).filter(h => h)
            };
            
            // Save profile to backend
            try {
              await apiService.updateProfile(data.session_id, socket.id, profileData);
              console.log('✅ Profile saved successfully');
            } catch (error) {
              console.error('Failed to save profile:', error);
              // Continue anyway
            }
            
            resolve(data);
          });
          
          // Handle session full error (MVP: 2 users max)
          socket.once('session_error', (data) => {
            clearTimeout(timeout);
            console.error('❌ Session error:', data);
            reject(new Error(data.message || 'Session error'));
          });
        });
        
        // Navigate to HeartLink scene
        navigate("/heartlink", {
          state: { 
            avatarName, 
            flameColor, 
            spiceLevel, 
            personality, 
            hobbies, 
            lookingFor,
            sessionId: socketService.getSessionId(),
            userRole: socketService.getUserRole()
          },
        });
      } catch (error) {
        console.error('❌ Error connecting to backend:', error);
        setIsConnecting(false);
        
        // More specific error messages
        if (error.message.includes('full') || error.message.includes('2 users')) {
          alert('⚠️ Matchmaking room is full!\n\nThe MVP currently supports 2 users max.\n\nPlease wait for the current session to end or try again later.');
        } else if (error.message.includes('timeout') || error.message.includes('Timeout')) {
          alert('Connection timeout! Check:\n1. Backend server is running\n2. You accepted the HTTPS certificate at https://' + window.location.hostname + ':8765\n3. Your WiFi connection');
        } else if (error.message.includes('ECONNREFUSED') || error.message.includes('refused')) {
          alert('Backend server is not running! Start it with: python app.py');
        } else {
          alert('Failed to connect to backend:\n' + error.message);
        }
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-gray-800 p-4 overflow-y-auto">
      <div className="w-full max-w-4xl mx-auto py-8">
        {/* Header */}
        {/* Logo Header */}
        <div className="text-center mb-4 flex flex-col items-center">
        <img
            src={logo}
            alt="Flames Logo"
            className="w-40 md:w-52 lg:w-60 drop-shadow-[0_0_25px_rgba(255,100,0,0.5)] transition-transform duration-300 hover:scale-105"
        />
        <p className="text-gray-300 text-sm mt-2 tracking-wide">
            Connect through conversation, reveal when ready
        </p>
        </div>

        {/* Main Card */}
        <div className="bg-gray-800/50 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-gray-700">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Left: Flame customization */}
            <div>
              <label className="flex items-center gap-2 text-white text-lg font-semibold mb-4">
                <Palette className="w-5 h-5" /> Customize Your Flame
              </label>

              <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 mb-6 flex items-center justify-center border border-gray-700">
                <canvas ref={canvasRef} className="relative z-10" />
              </div>

              <label className="text-white text-sm font-medium mb-3 block">Flame Color</label>
              <div className="grid grid-cols-3 gap-2">
                {flameColors.map((flame) => (
                  <button
                    key={flame.id}
                    onClick={() => setFlameColor(flame.id)}
                    className={`relative p-3 rounded-lg transition-all ${
                      flameColor === flame.id ? "ring-2 ring-white scale-105" : "hover:scale-105"
                    }`}
                    style={{
                      background: `#${flame.color.toString(16).padStart(6, "0")}`,
                    }}
                  >
                    <span className="text-white text-xs font-medium drop-shadow-lg">
                      {flame.name}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Right: Info form */}
            <div className="flex flex-col">
              <label className="text-white text-lg font-semibold mb-3 block">Avatar Name</label>
              <input
                type="text"
                value={avatarName}
                onChange={(e) => setAvatarName(e.target.value)}
                placeholder="Enter your alias..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all mb-6"
              />

              {/* Personality */}
              <label className="text-white text-lg font-semibold mb-3 block">
            Personality Type
            </label>

            <div className="grid grid-cols-3 gap-2 mb-6">
            {["introvert", "ambivert", "extrovert"].map((type) => (
                <button
                key={type}
                onClick={() => setPersonality(type)}
                className={`py-2 px-3 text-sm rounded-lg font-medium transition-all ${
                    personality === type
                    ? "bg-gradient-to-r from-pink-500 to-orange-500 text-white shadow-md scale-105"
                    : "bg-gray-700/30 text-gray-300 hover:bg-gray-700/50"
                }`}
                >
                {type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
            ))}
            </div>

              {/* Hobbies */}
              <label className="text-white text-lg font-semibold mb-3 block">What are your hobbies?</label>
              <textarea
                value={hobbies}
                onChange={(e) => setHobbies(e.target.value)}
                placeholder="e.g., Gaming, hiking..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-orange-500 mb-6"
                rows={3}
                maxLength={150}
              />

              {/* Looking For */}
              <label className="text-white text-lg font-semibold mb-3 block">What are you looking for?</label>
              <textarea
                value={lookingFor}
                onChange={(e) => setLookingFor(e.target.value)}
                placeholder="e.g., Deep conversations, new friends..."
                className="w-full bg-gray-700/50 border border-gray-600 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:ring-2 focus:ring-orange-500"
                rows={3}
                maxLength={150}
              />
            </div>
          </div>
          <div className="flex-1">
                <label className="flex items-center gap-2 text-white text-lg font-semibold mb-4">
                  <Zap className="w-5 h-5" />
                  Conversation Intensity
                </label>
                
                <div className="space-y-3">
                  {spiceLevels.map((level) => (
                    <button
                      key={level.level}
                      onClick={() => setSpiceLevel(level.level)}
                      className={`w-full p-4 rounded-xl transition-all transform hover:scale-102 ${
                        spiceLevel === level.level
                          ? `bg-gradient-to-r ${level.color} text-white shadow-lg`
                          : 'bg-gray-700/30 text-gray-300 hover:bg-gray-700/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="text-left">
                          <div className="font-bold text-lg">{level.label}</div>
                          <div className={`text-sm ${spiceLevel === level.level ? 'text-white/90' : 'text-gray-400'}`}>
                            {level.desc}
                          </div>
                        </div>
                        <div className="flex gap-1">
                          {[...Array(level.level)].map((_, i) => (
                            <div
                              key={i}
                              className={`w-2 h-8 rounded-full ${
                                spiceLevel === level.level ? 'bg-white/80' : 'bg-gray-500'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
                </div>

          {/* Certificate Help */}
          <div className="mt-4 p-3 bg-blue-900/30 border border-blue-500/50 rounded-lg">
            <p className="text-blue-300 text-sm mb-2">
              ⚠️ First time? Accept the backend certificate:
            </p>
            <button
              onClick={() => window.open(`https://${window.location.hostname}`, '_blank')}
              className="text-blue-400 hover:text-blue-300 underline text-sm"
            >
              Click here to accept certificate →
            </button>
            <p className="text-gray-400 text-xs mt-1">
              (Opens in new tab, click "Advanced" → "Proceed")
            </p>
          </div>

          {/* CTA */}
          <button
            onClick={handleStartMatching}
            disabled={!avatarName || !personality || !hobbies || !lookingFor || isConnecting}
            className={`w-full py-4 rounded-xl font-bold text-lg mt-4 transition-all ${
              avatarName && personality && hobbies && lookingFor && !isConnecting
                ? "bg-gradient-to-r from-orange-500 to-red-500 text-white hover:scale-105 hover:shadow-xl"
                : "bg-gray-700 text-gray-500 cursor-not-allowed"
            }`}
          >
            {isConnecting
              ? "🔄 Connecting..."
              : avatarName && personality && hobbies && lookingFor
              ? "🔥 Find Your Match"
              : "Fill out all fields"}
          </button>
        </div>
      </div>
    </div>
  );
}