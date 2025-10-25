import React, { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

export default function MediatorHoloSphere({ position = [0, 0, 0] }) {
  const meshRef = useRef();

  const uniforms = {
    u_time: { value: 0 },
    u_color1: { value: new THREE.Color("#00f5ff") }, // teal blue
    u_color2: { value: new THREE.Color("#ff6bff") }, // pink/magenta
    u_color3: { value: new THREE.Color("#8b80ff") }, // violet
  };

  const material = new THREE.ShaderMaterial({
    uniforms,
    transparent: true,
    blending: THREE.AdditiveBlending,
    side: THREE.DoubleSide,
    depthWrite: false,
    vertexShader: `
      varying vec3 vNormal;
      varying vec3 vPos;
      uniform float u_time;

      void main() {
        vNormal = normalize(normalMatrix * normal);
        vPos = position;

        // subtle wave motion to mimic fluidity
        vec3 displaced = position + normal * (
          sin(position.x * 3.5 + u_time * 2.0) * 0.07 +
          sin(position.y * 4.0 - u_time * 1.8) * 0.07 +
          sin(length(position.xy) * 5.0 - u_time * 2.5) * 0.05
        );

        gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
      }
    `,
    fragmentShader: `
      varying vec3 vNormal;
      varying vec3 vPos;
      uniform float u_time;
      uniform vec3 u_color1;
      uniform vec3 u_color2;
      uniform vec3 u_color3;

      void main() {
        // normal-based color shift
        float angle = dot(normalize(vNormal), normalize(vec3(0.0, 0.0, 1.0)));
        float pulse = 0.5 + 0.5 * sin(u_time * 3.0 + length(vPos.xy) * 4.0);

        // holographic gradient blending
        vec3 base = mix(u_color1, u_color2, 0.5 + 0.5 * sin(u_time + angle * 3.0));
        vec3 glow = mix(base, u_color3, pulse);

        // radial intensity for soft glow edges
        float intensity = pow(1.0 - abs(angle), 3.0);
        vec3 color = glow + intensity * vec3(0.4, 0.6, 1.0);

        // soft transparency and light emission
        gl_FragColor = vec4(color, 0.8 - intensity * 0.3);
      }
    `,
  });

  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    material.uniforms.u_time.value = t;
    meshRef.current.rotation.y += 0.003;
    meshRef.current.rotation.x += 0.001;
    const scale = 1.05 + Math.sin(t * 1.5) * 0.03;
    meshRef.current.scale.set(scale, scale, scale);
  });

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[1.35, 128, 128]} />
      <primitive attach="material" object={material} />
    </mesh>
  );
}