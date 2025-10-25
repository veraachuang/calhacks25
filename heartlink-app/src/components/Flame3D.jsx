// components/Flame3D.jsx
import React, { useEffect, useRef } from "react";
import * as THREE from "three";

export default function Flame3D({ flameColor = "orange", size = 200 }) {
  const canvasRef = useRef(null);

  const flameColors = {
    orange: 0xff4500,
    blue: 0x4169e1,
    purple: 0x8b00ff,
    green: 0x00ff41,
    pink: 0xff1493,
    white: 0xffffff,
  };

  const getColor = () => flameColors[flameColor] || 0xff4500;

  useEffect(() => {
    if (!canvasRef.current) return;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      alpha: true,
      antialias: true,
    });

    renderer.setSize(size, size);
    camera.position.z = 5;

    // Particle system
    const particles = [];
    const count = 180;

    for (let i = 0; i < count; i++) {
      const s = Math.random() * 0.25 + 0.1;
      const geo = new THREE.SphereGeometry(s, 8, 8);
      const mat = new THREE.MeshBasicMaterial({
        color: getColor(),
        transparent: true,
        opacity: 0.8,
      });
      const mesh = new THREE.Mesh(geo, mat);

      const h = Math.random();
      const angle = Math.random() * Math.PI * 2;
      let width;
      if (h < 0.3) width = 0.15 + (h / 0.3) * 0.25;
      else if (h < 0.6) width = 0.4 - ((h - 0.3) / 0.3) * 0.05;
      else width = 0.35 - ((h - 0.6) / 0.4) * 0.33;

      const radius = Math.random() * width;
      mesh.position.set(Math.cos(angle) * radius, h * 2.2 - 0.3, Math.sin(angle) * radius);
      mesh.userData = {
        speed: Math.random() * 0.015 + 0.008,
        wobble: Math.random() * 0.06,
        wobbleSpeed: Math.random() * 2 + 1,
        angle,
        baseRadius: radius,
      };
      scene.add(mesh);
      particles.push(mesh);
    }

    const light = new THREE.PointLight(getColor(), 2, 10);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0x404040));

    let time = 0;
    let animationId;

    const animate = () => {
      animationId = requestAnimationFrame(animate);
      time += 0.016;

      particles.forEach((p, i) => {
        p.position.y += p.userData.speed;

        const yRatio = (p.position.y + 0.3) / 2.2;
        let currentWidth;
        if (yRatio < 0.3) currentWidth = 0.15 + (yRatio / 0.3) * 0.25;
        else if (yRatio < 0.6) currentWidth = 0.4 - ((yRatio - 0.3) / 0.3) * 0.05;
        else currentWidth = 0.35 - ((yRatio - 0.6) / 0.4) * 0.33;

        const wRatio = currentWidth / 0.4;
        const r = p.userData.baseRadius * wRatio;
        const wobbleX = Math.sin(time * p.userData.wobbleSpeed + i) * p.userData.wobble;
        const wobbleZ = Math.cos(time * p.userData.wobbleSpeed + i) * p.userData.wobble;
        p.position.x = Math.cos(p.userData.angle) * r + wobbleX;
        p.position.z = Math.sin(p.userData.angle) * r + wobbleZ;

        // color gradient by height
        if (yRatio < 0.2) p.material.color.setHex(0xff3300);
        else if (yRatio < 0.4) p.material.color.setHex(0xff6600);
        else if (yRatio < 0.6) p.material.color.setHex(getColor());
        else if (yRatio < 0.8) p.material.color.setHex(0xffaa00);
        else p.material.color.setHex(0xffff88);

        p.material.opacity = Math.max(0, 1 - (p.position.y + 0.3) / 2.5);
        if (p.position.y > 1.9) p.position.y = -0.3;
      });

      light.intensity = 2 + Math.sin(time * 5) * 0.3;
      light.color.setHex(getColor());
      renderer.render(scene, camera);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationId);
      renderer.dispose();
      particles.forEach((p) => {
        p.geometry.dispose();
        p.material.dispose();
      });
    };
  }, [flameColor, size]);

  return <canvas ref={canvasRef} style={{ width: size, height: size }} />;
}