import React, { useState, useEffect, useRef } from "react";
import { Zap, Palette } from "lucide-react";
import * as THREE from "three";
import { useNavigate } from "react-router-dom";

export default function ProfilePage() {
  const [avatarName, setAvatarName] = useState("");
  const [spiceLevel, setSpiceLevel] = useState(2);
  const [flameColor, setFlameColor] = useState("orange");
  const [personality, setPersonality] = useState("");
  const [hobbies, setHobbies] = useState("");
  const [lookingFor, setLookingFor] = useState("");

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
  const handleStartMatching = () => {
    if (avatarName && personality && hobbies && lookingFor) {
      navigate("/heartlink", {
        state: { avatarName, flameColor, spiceLevel, personality, hobbies, lookingFor },
      });
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-gray-800 p-4 overflow-y-auto">
      <div className="w-full max-w-4xl mx-auto py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1
            className="text-5xl font-bold text-white mb-4"
            style={{
              fontFamily: '"Roboto Mono", monospace',
              textShadow: "0 0 10px #ff6600, 0 0 20px #ff4400, 0 0 40px #ff0000",
            }}
          >
            Flames
          </h1>
          <p className="text-gray-300">Connect through conversation, reveal when ready</p>
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
              <label className="text-white text-lg font-semibold mb-3 block">Personality Type</label>
              <div className="grid grid-cols-2 gap-3 mb-6">
                {["introvert", "extrovert"].map((type) => (
                  <button
                    key={type}
                    onClick={() => setPersonality(type)}
                    className={`py-3 px-4 rounded-xl font-medium transition-all ${
                      personality === type
                        ? "bg-gradient-to-r from-pink-500 to-orange-500 text-white shadow-lg"
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
          {/* Personality Type */}
              <div className="mb-6">
                <label className="text-white text-lg font-semibold mb-3 block">
                  Personality Type
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setPersonality('introvert')}
                    className={`py-3 px-4 rounded-xl font-medium transition-all ${
                      personality === 'introvert'
                        ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white shadow-lg'
                        : 'bg-gray-700/30 text-gray-300 hover:bg-gray-700/50'
                    }`}
                  >
                    Introvert
                  </button>
                  <button
                    onClick={() => setPersonality('extrovert')}
                    className={`py-3 px-4 rounded-xl font-medium transition-all ${
                      personality === 'extrovert'
                        ? 'bg-gradient-to-r from-pink-500 to-orange-500 text-white shadow-lg'
                        : 'bg-gray-700/30 text-gray-300 hover:bg-gray-700/50'
                    }`}
                  >
                    Extrovert
                  </button>
                </div>
              </div>

              {/* Hobbies */}
              <div className="mb-6">
                <label className="text-white text-lg font-semibold mb-3 block">
                  What are your hobbies?
                </label>
                <textarea
                  value={hobbies}
                  onChange={(e) => setHobbies(e.target.value)}
                  placeholder="e.g., Gaming, reading, hiking..."
                  className="w-full bg-gray-700/50 border border-gray-600 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all resize-none"
                  rows={3}
                  maxLength={150}
                />
                <p className="text-gray-500 text-xs mt-1">{hobbies.length}/150</p>
              </div>

              {/* Looking For */}
              <div className="mb-6">
                <label className="text-white text-lg font-semibold mb-3 block">
                  What are you looking for?
                </label>
                <textarea
                  value={lookingFor}
                  onChange={(e) => setLookingFor(e.target.value)}
                  placeholder="e.g., Deep conversations, new friends, casual chat..."
                  className="w-full bg-gray-700/50 border border-gray-600 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-orange-500 transition-all resize-none"
                  rows={3}
                  maxLength={150}
                />
                <p className="text-gray-500 text-xs mt-1">{lookingFor.length}/150</p>
              </div>

          {/* CTA */}
          <button
            onClick={handleStartMatching}
            disabled={!avatarName || !personality || !hobbies || !lookingFor}
            className={`w-full py-4 rounded-xl font-bold text-lg mt-8 transition-all ${
              avatarName && personality && hobbies && lookingFor
                ? "bg-gradient-to-r from-orange-500 to-red-500 text-white hover:scale-105 hover:shadow-xl"
                : "bg-gray-700 text-gray-500 cursor-not-allowed"
            }`}
          >
            {avatarName && personality && hobbies && lookingFor
              ? "Find Your Match"
              : "Complete Your Profile"}
          </button>
        </div>
      </div>
    </div>
  );
}