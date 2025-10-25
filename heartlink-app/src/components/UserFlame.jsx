import React, { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

export default function UserFlame({
  position = [0, 0, 0],
  color = "#00ffff",
  speaking = false,
}) {
  const meshRef = useRef();

  const uniforms = {
    u_time: { value: 0 },
    u_color: { value: new THREE.Color(color) },
  };

  const material = new THREE.ShaderMaterial({
    uniforms,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    side: THREE.DoubleSide,
    vertexShader: `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      varying vec2 vUv;
      uniform float u_time;
      uniform vec3 u_color;

      float flameShape(vec2 uv) {
        uv = uv * 2.0 - 1.0;
        uv.y += 0.4;
        float r = length(uv);
        float base = smoothstep(0.8, 0.4, r);
        base *= uv.y + 0.4;
        return clamp(base, 0.0, 1.0);
      }

      void main() {
        vec2 uv = vUv;
        float t = u_time * 1.2;

        // Gentle shimmer — not chaotic
        float flicker = sin(uv.y * 8.0 - t * 2.0) * 0.015 +
                        cos(uv.x * 5.0 + t * 1.5) * 0.015;

        float shape = flameShape(uv + vec2(0.0, flicker));

        vec3 col = u_color;
        col = mix(col * 0.7, vec3(1.0), uv.y * 1.2);
        col += vec3(0.2, 0.3, 0.7) * sin(t + uv.y * 2.0) * 0.2;

        gl_FragColor = vec4(col, shape * 1.1);
      }
    `,
  });

  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    uniforms.u_time.value = t;

    // More subtle pulse & smaller scale
    const baseScale = 1.6; // slightly smaller
    const pulse = speaking
      ? 1.05 + Math.sin(t * 2.5) * 0.05
      : 1.0 + Math.sin(t * 1.2) * 0.02;

    meshRef.current.scale.set(baseScale * pulse, baseScale * pulse, baseScale * pulse);
  });

  return (
    <mesh ref={meshRef} position={position}>
      <planeGeometry args={[1.2, 1.8, 64, 64]} />
      <primitive attach="material" object={material} />
    </mesh>
  );
}