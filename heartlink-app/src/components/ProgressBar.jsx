import React, { useEffect, useState } from "react";

export default function ProgressBar({ onMatchReady }) {
  const totalSegments = 20; // per side
  const [user1Progress, setUser1Progress] = useState(0);
  const [user2Progress, setUser2Progress] = useState(0);

  // Simulate progress filling over time (for now)
  useEffect(() => {
    const interval = setInterval(() => {
      setUser1Progress((p) => Math.min(totalSegments, p + 1));
      setUser2Progress((p) => Math.min(totalSegments, p + 1));
    }, 300);
    return () => clearInterval(interval);
  }, []);

  // Notify parent when both reach full
  const isMatched = user1Progress === totalSegments && user2Progress === totalSegments;
  useEffect(() => {
    if (onMatchReady) onMatchReady(isMatched);
  }, [isMatched, onMatchReady]);

  // Color transition (red → yellow → green)
  const getColor = (i, progress) => {
    const ratio = i / totalSegments;
    if (ratio < 0.4) return "bg-rose-500";
    if (ratio < 0.7) return "bg-yellow-400";
    return "bg-emerald-400";
  };

  return (
    <div className="absolute top-6 left-1/2 -translate-x-1/2 flex items-center justify-center w-full z-10">
      <div className="flex items-center gap-1 justify-center">
        {/* Left side (User 1, fills rightward) */}
        {Array.from({ length: totalSegments }).map((_, i) => (
          <div
            key={`u1-${i}`}
            className={`h-3 w-3 rounded-sm transition-all duration-300 ${
              i < user1Progress ? getColor(i, user1Progress) : "bg-gray-700/60"
            }`}
          />
        ))}

        {/* Center space for Match button */}
        <div className="w-12" />

        {/* Right side (User 2, fills leftward) */}
        {Array.from({ length: totalSegments })
          .map((_, i) => totalSegments - 1 - i) // reverse order for symmetry
          .map((revI) => (
            <div
              key={`u2-${revI}`}
              className={`h-3 w-3 rounded-sm transition-all duration-300 ${
                revI < user2Progress ? getColor(revI, user2Progress) : "bg-gray-700/60"
              }`}
            />
          ))}
      </div>
    </div>
  );
}