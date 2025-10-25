import React, { useState, useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import MediatorHoloSphere from "../components/MediatorHoloSphere";
import ProgressBar from "../components/ProgressBar";
import { useNavigate, useLocation } from "react-router-dom";
import FlameAvatar from "../components/FlameAvatar";
import "../index.css";

export default function HeartLinkScene() {
  const [activeSpeaker, setActiveSpeaker] = useState("user1");
  const navigate = useNavigate();
  const location = useLocation();

  // Get user selections from ProfilePage
  const { avatarName = "User 1", flameColor = "orange" } = location.state || {};

  // Alternate "speaking" animation between users
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveSpeaker((prev) => (prev === "user1" ? "user2" : "user1"));
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-screen h-screen overflow-hidden text-white">
      {/* 3D Canvas Scene */}
      <Canvas
        className="absolute inset-0"
        camera={{ position: [0, 0, 8], fov: 60 }}
      >
        <color attach="background" args={["#050514"]} />
        <ambientLight intensity={0.6} />
        <pointLight position={[0, 2, 6]} intensity={2.5} color="#ffffff" />

        {/* Mediator Sphere — holographic center */}
        <MediatorHoloSphere position={[0, 0, 0]} activeSpeaker={activeSpeaker} />
      </Canvas>

      {/* 2D overlay (Flames + UI) */}
      <div className="absolute inset-0 z-10 flex items-center justify-between px-12 md:px-24 lg:px-32 pointer-events-none">
        {/* Left user */}
        <div className="flex flex-col items-center pointer-events-auto">
          <FlameAvatar flameColor={flameColor} size={200} />
          <p className="text-white/80 font-semibold mt-3">{avatarName}</p>
        </div>

        {/* Right user */}
        <div className="flex flex-col items-center pointer-events-auto">
          <FlameAvatar flameColor="pink" size={200} />
          <p className="text-white/80 font-semibold mt-3">User 2</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="z-20">
        <ProgressBar />
      </div>

      {/* Back button */}
      <button
        onClick={() => navigate("/")}
        className="absolute top-6 left-6 z-20 px-4 py-2 rounded-lg bg-white/10 text-gray-300 hover:text-white border border-white/20 backdrop-blur-md pointer-events-auto"
      >
        ← Back
      </button>

      {/* Disabled Match button */}
      <div className="absolute top-[60px] left-1/2 -translate-x-1/2 z-20 pointer-events-auto">
        <button
          disabled
          className="px-6 py-2 rounded-full bg-white/10 text-gray-400 font-semibold cursor-not-allowed border border-white/20 backdrop-blur-md"
        >
          💞 Match
        </button>
      </div>

      {/* Chat / dialogue overlay */}
      <div
        className="glass-box absolute bottom-16 left-1/2 -translate-x-1/2 w-3/5 p-6 text-center z-20 pointer-events-auto"
        style={{ maxWidth: "700px" }}
      >
        <h2 className="text-pink-400 font-semibold text-xl mb-2">
          HeartLink AI Mediator 🤍
        </h2>
        <p className="text-gray-200 text-base leading-relaxed">
          <b>{avatarName}:</b> “Hey, what kind of music do you like?” <br />
          <b>User 2:</b> “I’m really into ambient techno.” <br />
          <b className="text-pink-300">AI:</b> “Interesting — both of you seem
          drawn to rhythm and flow.” 🎵
        </p>
      </div>
    </div>
  );
}