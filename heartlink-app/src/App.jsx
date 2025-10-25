import React, { useState, useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import MediatorHoloSphere from "./components/MediatorHoloSphere";
import UserFlame from "./components/UserFlame";
import ProgressBar from "./components/ProgressBar";
import "./index.css";

export default function App() {
  const [activeSpeaker, setActiveSpeaker] = useState("user1");

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveSpeaker((p) => (p === "user1" ? "user2" : "user1"));
    }, 3500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative w-screen h-screen overflow-hidden text-white">
      <Canvas camera={{ position: [0, 0, 8], fov: 60 }}>
        <color attach="background" args={["#050514"]} />
        <ambientLight intensity={0.6} />
        <pointLight position={[0, 3, 5]} intensity={2} color="#ffffff" />

        <UserFlame
          position={[-3.8, -0.3, 0]}
          color="#00ffff"
          speaking={activeSpeaker === "user1"}
        />

        <MediatorHoloSphere position={[0, 0, 0]} />

        <UserFlame
          position={[3.8, -0.3, 0]}
          color="#ff66ff"
          speaking={activeSpeaker === "user2"}
        />

      </Canvas>

      <ProgressBar />

      <div className="absolute top-[60px] left-1/2 -translate-x-1/2">
        <button
          disabled
          className="px-6 py-2 rounded-full bg-white/10 text-gray-400 font-semibold cursor-not-allowed border border-white/20 backdrop-blur-md"
        >
          💞 Match
        </button>
      </div>

      <div
        className="glass-box absolute bottom-16 left-1/2 -translate-x-1/2 w-3/5 p-6 text-center"
        style={{ maxWidth: "700px" }}
      >
        <h2 className="text-pink-400 font-semibold text-xl mb-2">
          HeartLink AI Mediator 🤍
        </h2>
        <p className="text-gray-200 text-base leading-relaxed">
          <b>User 1:</b> “Hey, what kind of music do you like?” <br />
          <b>User 2:</b> “I’m really into ambient techno.” <br />
          <b className="text-pink-300">AI:</b> “Interesting — both of you seem
          drawn to rhythm and flow.” 🎵
        </p>
      </div>
    </div>
  );
}