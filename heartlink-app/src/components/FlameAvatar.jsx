import React, { useState, useEffect } from "react";

export default function FlameAvatar({ flameColor = "orange", size = 200 }) {
  const [animationOffset, setAnimationOffset] = useState(0);

  useEffect(() => {
    let offset = 0;
    const interval = setInterval(() => {
      offset += 0.1;
      setAnimationOffset(offset);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  const flameColors = {
    orange: ['#ff4500', '#ff6b35', '#ffa500', '#ffcc00'],
    blue: ['#1e90ff', '#4169e1', '#00bfff', '#87ceeb'],
    purple: ['#8b00ff', '#9d4edd', '#c77dff', '#e0aaff'],
    green: ['#00ff41', '#39ff14', '#7fff00', '#adff2f'],
    pink: ['#ff1493', '#ff69b4', '#ff91af', '#ffb3d9'],
    white: ['#ffffff', '#f0f0f0', '#e0e0e0', '#d0d0d0']
  };

  const colors = flameColors[flameColor] || flameColors.orange;
  const time = animationOffset;

  const generateFlamePath = (layer) => {
    const baseSize = 1 - (layer * 0.12);
    const leftWobble = Math.sin(time + layer) * 3;
    const rightWobble = Math.sin(time + layer + 1) * 3;
    const tipWobble = Math.sin(time * 1.5 + layer) * 2;
    const sideWave = Math.sin(time * 0.8) * 2;

    const leftCurve = 30 + leftWobble;
    const rightCurve = 70 + rightWobble;
    const tipHeight = 20 - (layer * 3) + tipWobble;
    const baseWidth = (25 + (layer * 3)) * baseSize;
    const midLeftX = 35 + sideWave;
    const midRightX = 65 - sideWave;

    return `
      M 50,${tipHeight}
      Q ${leftCurve},${35 + leftWobble} ${midLeftX},${55}
      Q ${30},${70} ${50 - baseWidth},${85}
      L ${50 + baseWidth},${85}
      Q ${70},${70} ${midRightX},${55}
      Q ${rightCurve},${35 + rightWobble} 50,${tipHeight}
      Z
    `;
  };

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className="drop-shadow-2xl"
    >
      <defs>
        <filter id="glow">
          <feGaussianBlur stdDeviation="4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        {colors.map((color, i) => (
          <linearGradient key={i} id={`flameGradient${i}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity={i === 0 ? "0.9" : "0.3"} />
            <stop offset="30%" stopColor={color} stopOpacity="1" />
            <stop offset="100%" stopColor={color} stopOpacity="0.6" />
          </linearGradient>
        ))}
      </defs>

      <ellipse cx="50" cy="88" rx="30" ry="10" fill={colors[0]} opacity="0.4" filter="url(#glow)" />

      <g filter="url(#glow)">
        <path d={generateFlamePath(3)} fill={`url(#flameGradient3)`} opacity="0.5" />
        <path d={generateFlamePath(2)} fill={`url(#flameGradient2)`} opacity="0.7" />
        <path d={generateFlamePath(1)} fill={`url(#flameGradient1)`} opacity="0.85" />
        <path d={generateFlamePath(0)} fill={`url(#flameGradient0)`} opacity="1" />
      </g>
    </svg>
  );
}