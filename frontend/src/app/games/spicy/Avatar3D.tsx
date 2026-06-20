"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMUtils, VRM } from "@pixiv/three-vrm";

interface Avatar3DProps {
  mood: string;
  isSpeaking: boolean;
}

export default function Avatar3D({ mood, isSpeaking }: Avatar3DProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loadingProgress, setLoadingProgress] = useState<number>(0);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  // Keep track of current properties using refs to avoid recreating the Three.js context on prop changes
  const moodRef = useRef<string>(mood);
  const isSpeakingRef = useRef<boolean>(isSpeaking);

  useEffect(() => {
    moodRef.current = mood;
  }, [mood]);

  useEffect(() => {
    isSpeakingRef.current = isSpeaking;
  }, [isSpeaking]);

  useEffect(() => {
    if (!canvasRef.current) return;

    let mounted = true;
    let vrmModel: VRM | null = null;
    let animationFrameId: number;

    const clock = new THREE.Clock();

    // 1. Mouse coordinates tracking
    const mouse = { x: 0, y: 0 };
    const handleMouseMove = (event: MouseEvent) => {
      // Normalize mouse coordinates to [-1, 1] relative to the window
      mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener("mousemove", handleMouseMove);

    // 2. Setup Three.js Scene, Camera, Renderer
    const scene = new THREE.Scene();

    const canvasWidth = canvasRef.current.clientWidth;
    const canvasHeight = canvasRef.current.clientHeight;
    const camera = new THREE.PerspectiveCamera(35, canvasWidth / canvasHeight, 0.1, 20.0);
    // Position camera at eye level (approx. 1.45m high) and close to the avatar
    camera.position.set(0, 1.45, 1.0);

    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      antialias: true,
      alpha: true, // Transparent background to blend into Next.js styles
      powerPreference: "high-performance",
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(canvasWidth, canvasHeight, false);
    renderer.shadowMap.enabled = true;

    // 3. Lighting Setup for Premium Depth & Rim Light
    // Soft cool ambient light
    const ambientLight = new THREE.AmbientLight(0xd5dbff, 0.6);
    scene.add(ambientLight);

    // Warm key light
    const keyLight = new THREE.DirectionalLight(0xfffaed, 1.0);
    keyLight.position.set(2.0, 4.0, 3.0);
    keyLight.castShadow = true;
    scene.add(keyLight);

    // Cyberpunk purple/violet rim light from behind for premium neon aesthetics
    const rimLight = new THREE.PointLight(0xa855f7, 2.5, 10.0);
    rimLight.position.set(-1.5, 2.0, -2.0);
    scene.add(rimLight);

    // Soft cyan fill light
    const fillLight = new THREE.DirectionalLight(0x06b6d4, 0.4);
    fillLight.position.set(-2.0, 1.0, 1.0);
    scene.add(fillLight);

    // Look at dummy target for VRM eyes to track
    const lookAtTarget = new THREE.Object3D();
    scene.add(lookAtTarget);

    // 4. VRM Loader Config
    const loader = new GLTFLoader();
    loader.register((parser) => {
      return new VRMLoaderPlugin(parser, {
        // We can specify option mappings here if needed
      });
    });

    // Load the model from public folder
    loader.load(
      "/models/rem.vrm",
      (gltf) => {
        if (!mounted) return;
        const vrm = gltf.userData.vrm as VRM;
        vrmModel = vrm;

        // Enable automatic normalized-to-raw copying to allow VRM humanoid solver to pose the mesh
        if (vrm.humanoid) {
          vrm.humanoid.autoUpdateHumanBones = true;
        }

        // Add model to scene
        scene.add(vrm.scene);

        // Turn the model to face the camera (if needed, default VRM points forward -Z)
        vrm.scene.rotation.y = Math.PI;

        // Disable frustum culling to prevent avatar from glitching/disappearing at edges
        vrm.scene.traverse((obj) => {
          obj.frustumCulled = false;
        });

        // Set eye target object
        if (vrm.lookAt) {
          vrm.lookAt.target = lookAtTarget;
        }

        // Apply helper setup to prepare expressions
        VRMUtils.rotateVRM0(vrm); // Support legacy VRM 0.0 rotation fixes automatically
        console.log("[AVATAR 3D] Model loaded successfully:", vrm);
        
        // Diagnostic bone logging
        try {
          const testBones = ["leftUpperArm", "leftLowerArm", "leftHand", "rightUpperArm", "rightLowerArm", "rightHand", "head", "neck", "spine", "chest"];
          const normalizedNodes: any = {};
          const rawNodes: any = {};
          testBones.forEach(b => {
            normalizedNodes[b] = vrm.humanoid?.getNormalizedBoneNode(b as any) ? "FOUND" : "NULL";
            rawNodes[b] = vrm.humanoid?.getRawBoneNode(b as any) ? "FOUND" : "NULL";
          });
          
          const leftUpperArmNode = vrm.humanoid?.getRawBoneNode("leftUpperArm");
          const skinnedMeshesCheck: any[] = [];
          
          vrm.scene.traverse((obj) => {
            if ((obj as any).isSkinnedMesh) {
              const mesh = obj as THREE.SkinnedMesh;
              skinnedMeshesCheck.push({
                name: mesh.name,
                bonesCount: mesh.skeleton?.bones?.length || 0,
                containsLeftUpperArm: mesh.skeleton?.bones?.includes(leftUpperArmNode as any) || false,
              });
            }
          });

          const logPayload = {
            timestamp: new Date().toISOString(),
            vrmVersion: (vrm.meta as any)?.version || "unknown",
            vrmMetaName: (vrm.meta as any)?.name || (vrm.meta as any)?.title || "unknown",
            normalizedBones: normalizedNodes,
            rawBones: rawNodes,
            humanoidExists: !!vrm.humanoid,
            autoUpdateBonesValue: vrm.humanoid?.autoUpdateHumanBones,
            skinnedMeshes: skinnedMeshesCheck,
            leftUpperArmDebug: leftUpperArmNode ? {
              name: leftUpperArmNode.name,
              type: leftUpperArmNode.type,
              parentName: leftUpperArmNode.parent?.name || "none",
              matrixAutoUpdate: leftUpperArmNode.matrixAutoUpdate,
              matrix: leftUpperArmNode.matrix.elements,
              matrixWorld: leftUpperArmNode.matrixWorld.elements,
              visible: leftUpperArmNode.visible,
            } : null
          };
          
          const logStr = JSON.stringify(logPayload, null, 2);
          console.log("[AVATAR 3D] Bone Diagnostic Payload:", logStr);
          
          fetch("http://localhost:8000/api/debug/logs", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ logs: logStr }),
          }).catch(err => console.error("Failed to post debug logs:", err));
        } catch (e: any) {
          console.error("[AVATAR 3D] Error checking bones:", e);
          fetch("http://localhost:8000/api/debug/logs", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ logs: `Error checking bones: ${e.message}\nStack: ${e.stack}` }),
          }).catch(() => {});
        }
        setLoadingProgress(100);
      },
      (xhr) => {
        if (xhr.total > 0) {
          const pct = Math.round((xhr.loaded / xhr.total) * 100);
          setLoadingProgress(pct);
        }
      },
      (err) => {
        console.error("[AVATAR 3D] Error loading VRM model:", err);
        setLoadingError("Failed to render 3D model. Make sure rem.vrm is fully loaded.");
      }
    );

    // 5. Animation Constants & State Variables
    let blinkTimer = 2.0;
    let isBlinking = false;
    let blinkVal = 0;
    const blinkDuration = 0.12; // fast natural blink

    // Keep track of current expression levels for smooth interpolation
    const currentExpressions: Record<string, number> = {
      happy: 0,
      sad: 0,
      angry: 0,
      relaxed: 0,
      surprised: 0,
      neutral: 1.0,
      blush: 0,
    };

    // Mapping moods to VRM expression blend shapes
    const moodToExpressions: Record<string, Record<string, number>> = {
      neutral: { neutral: 1.0, happy: 0.0, sad: 0.0, angry: 0.0, relaxed: 0.0 },
      happy: { neutral: 0.0, happy: 0.35, sad: 0.0, angry: 0.0, relaxed: 0.0 },
      sad: { neutral: 0.0, happy: 0.0, sad: 0.3, angry: 0.0, relaxed: 0.0 },
      angry: { neutral: 0.0, happy: 0.0, sad: 0.0, angry: 0.3, relaxed: 0.0 },
      relaxed: { neutral: 0.0, happy: 0.0, sad: 0.0, angry: 0.0, relaxed: 0.3 },
      surprised: { neutral: 0.0, happy: 0.0, sad: 0.0, angry: 0.0, surprised: 0.4 },
      // Spicy Chat Starting Mood Titles (mapped to expressions)
      "flirty & affectionate": { happy: 0.35, relaxed: 0.15 },
      "teasing & playful": { happy: 0.3, relaxed: 0.2 },
      "shy & hesitant": { sad: 0.3, relaxed: 0.1 },
      "cold & hard to get": { neutral: 0.8, sad: 0.15 },
      "sassy & sarcastic": { relaxed: 0.35, happy: 0.15 },
      "guarded & conservative": { neutral: 0.9, sad: 0.1 },
      "super dominant": { neutral: 0.8, angry: 0.2 },
      "submissive & vulnerable": { sad: 0.4, relaxed: 0.1 },
      "unyielding & detached": { neutral: 0.8, sad: 0.15 },
      "flirty": { happy: 0.35, relaxed: 0.15 },
      "playful": { happy: 0.3, relaxed: 0.2 },
    };

    // 6. Main Render/Animation Loop
    let lastMood = "";
    let lastLoggedMood = "";

    const eulerToQuaternionArray = (x: number, y: number, z: number): [number, number, number, number] => {
      const q = new THREE.Quaternion().setFromEuler(new THREE.Euler(x, y, z, 'ZXY'));
      return [q.x, q.y, q.z, q.w];
    };
    const headState = { x: 0, y: 0 };

    const tick = () => {
      if (!mounted) return;

      const delta = clock.getDelta();
      const time = clock.getElapsedTime();

      if (vrmModel) {
        // --- 6a. Main VRM Update ---
        // Updates expressionManager, lookAt, and springBoneManager constraint system.
        // This is now called at the end of the tick block to sync normalized bones to raw bones.

        const currentMood = moodRef.current.toLowerCase();
        if (currentMood !== lastMood) {
          console.log("[AVATAR 3D] Mood changed in tick loop from:", lastMood, "to:", currentMood);
          lastMood = currentMood;
        }

        // --- 6c. Mouse cursor head & eye tracking ---
        // LookAtTarget follows mouse projected coordinates
        lookAtTarget.position.set(mouse.x * 3.0, mouse.y * 3.0 + 1.45, 2.0);

        // Turn head and neck slightly towards the cursor direction
        const targetHeadY = mouse.x * 0.28; // head turning limits
        const targetHeadX = -mouse.y * 0.18; // head nodding limits

        // Lerp for smooth head movement
        headState.y += (targetHeadY - headState.y) * 0.05;
        headState.x += (targetHeadX - headState.x) * 0.05;

        // Build normalized pose dictionary (includes static A-pose for arms with breathing/sway)
        const breathSway = Math.sin(time * 1.4);
        const breathAmp = 0.03; // arm expansion amp
        const microSwayX = Math.sin(time * 0.5) * 0.015;
        const microSwayY = Math.cos(time * 0.4) * 0.015;
        const microSwayZ = Math.sin(time * 0.6) * 0.015;

        const normalizedPose: any = {
          leftUpperArm: {
            rotation: eulerToQuaternionArray(
              microSwayX,
              microSwayY,
              1.25 + (breathSway * breathAmp) + microSwayZ
            )
          },
          rightUpperArm: {
            rotation: eulerToQuaternionArray(
              -microSwayX,
              -microSwayY,
              -1.25 - (breathSway * breathAmp) - microSwayZ
            )
          },
          leftLowerArm: {
            rotation: eulerToQuaternionArray(0.0, Math.sin(time * 0.7) * 0.02, -0.2)
          },
          rightLowerArm: {
            rotation: eulerToQuaternionArray(0.0, -Math.cos(time * 0.7) * 0.02, 0.2)
          },
          leftHand: {
            rotation: eulerToQuaternionArray(0.0, 0.0, Math.sin(time * 0.9) * 0.02)
          },
          rightHand: {
            rotation: eulerToQuaternionArray(0.0, 0.0, -Math.cos(time * 0.9) * 0.02)
          },
          chest: {
            rotation: eulerToQuaternionArray(
              Math.sin(time * 1.4) * 0.035, // Breathing rise & fall
              0.0,
              Math.cos(time * 0.7) * 0.015 // Gentle chest roll
            )
          },
          spine: {
            rotation: eulerToQuaternionArray(
              Math.sin(time * 1.4) * 0.01,
              Math.sin(time * 0.6) * 0.025, // Side-to-side hip sway
              Math.cos(time * 0.6) * 0.015
            )
          },
          head: {
            rotation: eulerToQuaternionArray(
              headState.x + Math.sin(time * 0.8) * 0.015,
              headState.y + Math.cos(time * 0.5) * 0.015,
              Math.sin(time * 0.4) * 0.01 // Soft head tilt
            )
          },
          neck: {
            rotation: eulerToQuaternionArray(
              (headState.x * 0.25) + Math.sin(time * 0.8) * 0.005,
              (headState.y * 0.25) + Math.cos(time * 0.5) * 0.005,
              Math.sin(time * 0.4) * 0.003
            )
          }
        };

        // Apply normalized pose using three-vrm official API
        vrmModel.humanoid.setNormalizedPose(normalizedPose);

        // --- 6d. Random Blink Logic ---
        blinkTimer -= delta;
        if (blinkTimer <= 0) {
          isBlinking = true;
          blinkTimer = 2.5 + Math.random() * 4.5; // Random blink cycle (2.5s - 7s)
        }

        if (isBlinking) {
          blinkVal += delta / (blinkDuration / 2);
          if (blinkVal >= 1.0) {
            blinkVal = 1.0;
            isBlinking = false; // Start opening eyes
          }
        } else if (blinkVal > 0.0) {
          blinkVal -= delta / (blinkDuration / 2);
          if (blinkVal <= 0.0) {
            blinkVal = 0.0;
          }
        }
        
        // Write both VRM 1.0 (lowercase) and VRM 0.0 (capitalized) blink names
        vrmModel.expressionManager?.setValue("blink", blinkVal);
        vrmModel.expressionManager?.setValue("Blink" as any, blinkVal);

        // --- 6e. Smooth Expression Interpolation ---
        const targetMood = moodRef.current.toLowerCase();
        const targetExprs = moodToExpressions[targetMood] || moodToExpressions.neutral;

        if (targetMood !== lastLoggedMood) {
          console.log(`[AVATAR 3D] Active expression mood changed to: "${targetMood}". Preset:`, targetExprs);
          lastLoggedMood = targetMood;
        }

        // Reset/smooth change expressions
        for (const key of ["happy", "sad", "angry", "relaxed", "surprised", "neutral"]) {
          const targetVal = targetExprs[key] ?? 0.0;
          const currentVal = currentExpressions[key] ?? 0.0;

          // Blend shape value interpolation (lerp)
          currentExpressions[key] = currentVal + (targetVal - currentVal) * 0.06;
          const val = currentExpressions[key];

          // Set VRM 1.0 lowercase expressions
          vrmModel.expressionManager?.setValue(key, val);

          // Map VRM 0.0 legacy equivalents (case-sensitive presets)
          if (key === "happy") {
            vrmModel.expressionManager?.setValue("joy" as any, val);
            vrmModel.expressionManager?.setValue("Joy" as any, val);
          } else if (key === "sad") {
            vrmModel.expressionManager?.setValue("sorrow" as any, val);
            vrmModel.expressionManager?.setValue("Sorrow" as any, val);
          } else if (key === "relaxed") {
            vrmModel.expressionManager?.setValue("fun" as any, val);
            vrmModel.expressionManager?.setValue("Fun" as any, val);
          } else if (key === "angry") {
            vrmModel.expressionManager?.setValue("Angry" as any, val);
          } else if (key === "neutral") {
            vrmModel.expressionManager?.setValue("Neutral" as any, val);
          } else if (key === "surprised") {
            vrmModel.expressionManager?.setValue("Surprised" as any, val);
          }
        }

        // --- 6e-2. Smooth Blush / Cheek Flushing Interpolation ---
        let targetBlush = 0.0;
        if (targetMood.includes("flirty") || targetMood.includes("affectionate") || targetMood.includes("playful") || targetMood.includes("vulnerable") || targetMood.includes("shy") || targetMood.includes("hesitant")) {
          targetBlush = 0.85; // Heavy blush for flirty/shy/vulnerable moods
        }

        const currentBlush = currentExpressions.blush ?? 0.0;
        currentExpressions.blush = currentBlush + (targetBlush - currentBlush) * 0.05;
        const bVal = currentExpressions.blush;

        // Apply to standard blush keys for VRM 1.0 and VRM 0.0 case variants
        vrmModel.expressionManager?.setValue("blush", bVal);
        vrmModel.expressionManager?.setValue("Blush" as any, bVal);
        vrmModel.expressionManager?.setValue("shame" as any, bVal);
        vrmModel.expressionManager?.setValue("Shame" as any, bVal);
        vrmModel.expressionManager?.setValue("cheek" as any, bVal);
        vrmModel.expressionManager?.setValue("Cheek" as any, bVal);

        // --- 6f. Mouth Lip-Sync Visemes (Speeches & Dialogues) ---
        if (isSpeakingRef.current) {
          // Speak viseme cycles
          const mouthOpenSpeed = 12.0;
          const aaVal = 0.4 + Math.sin(time * mouthOpenSpeed) * 0.4;
          const ohVal = 0.1 + Math.sin(time * mouthOpenSpeed * 0.7) * 0.2;

          // Write both VRM 1.0 (aa, oh) and VRM 0.0 (a, o, A, O)
          vrmModel.expressionManager?.setValue("aa", aaVal);
          vrmModel.expressionManager?.setValue("a" as any, aaVal);
          vrmModel.expressionManager?.setValue("A" as any, aaVal);

          vrmModel.expressionManager?.setValue("oh", ohVal);
          vrmModel.expressionManager?.setValue("o" as any, ohVal);
          vrmModel.expressionManager?.setValue("O" as any, ohVal);
          
          vrmModel.expressionManager?.setValue("ih", 0.0);
          vrmModel.expressionManager?.setValue("i" as any, 0.0);
          vrmModel.expressionManager?.setValue("I" as any, 0.0);
        } else {
          // Clear mouth visemes
          vrmModel.expressionManager?.setValue("aa", 0.0);
          vrmModel.expressionManager?.setValue("a" as any, 0.0);
          vrmModel.expressionManager?.setValue("A" as any, 0.0);
          
          vrmModel.expressionManager?.setValue("oh", 0.0);
          vrmModel.expressionManager?.setValue("o" as any, 0.0);
          vrmModel.expressionManager?.setValue("O" as any, 0.0);
          
          vrmModel.expressionManager?.setValue("ih", 0.0);
          vrmModel.expressionManager?.setValue("i" as any, 0.0);
          vrmModel.expressionManager?.setValue("I" as any, 0.0);
        }

        // --- 6g. Apply bone and expression updates ---
        vrmModel.update(delta);
      }


      // Render scene
      renderer.render(scene, camera);
      animationFrameId = requestAnimationFrame(tick);
    };

    tick();

    // 7. Handle Resize
    const handleResize = () => {
      if (!canvasRef.current) return;
      const width = canvasRef.current.clientWidth;
      const height = canvasRef.current.clientHeight;

      camera.aspect = width / height;
      camera.updateProjectionMatrix();

      renderer.setSize(width, height, false);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    };

    const resizeObserver = new ResizeObserver(() => handleResize());
    if (canvasRef.current.parentElement) {
      resizeObserver.observe(canvasRef.current.parentElement);
    }

    // Cleanup logic
    return () => {
      mounted = false;
      window.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(animationFrameId);
      resizeObserver.disconnect();

      // Dispose Three.js objects
      if (vrmModel) {
        VRMUtils.deepDispose(vrmModel.scene);
      }
      renderer.dispose();
      keyLight.dispose();
      ambientLight.dispose();
      rimLight.dispose();
      fillLight.dispose();
    };
  }, []);

  return (
    <div className="relative w-full h-full min-h-[400px] flex items-center justify-center bg-radial from-slate-950/20 to-slate-950/90 rounded-2xl overflow-hidden border border-purple-500/10 shadow-2xl">
      {/* 3D Canvas */}
      <canvas ref={canvasRef} className="w-full h-full block z-10" />

      {/* Loading Overlay */}
      {loadingProgress < 100 && !loadingError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/80 z-20 transition-all duration-300">
          <div className="w-16 h-16 border-4 border-purple-500/20 border-t-purple-500 rounded-full animate-spin mb-4" />
          <div className="text-purple-400 font-medium tracking-wide">Initializing Virtual Body...</div>
          <div className="text-purple-300/60 text-xs mt-1">{loadingProgress}% Loaded</div>
        </div>
      )}

      {/* Error Overlay */}
      {loadingError && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950/90 z-20 px-6 text-center">
          <span className="text-3xl mb-3">⚠️</span>
          <div className="text-red-400 font-medium">{loadingError}</div>
          <div className="text-slate-500 text-xs mt-2 max-w-[280px]">
            Please verify that the model file exists at `frontend/public/models/rem.vrm`.
          </div>
        </div>
      )}

      {/* Futuristic scanning overlay grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_bottom,rgba(168,85,247,0.02)_1px,transparent_1px)] bg-[size:100%_4px] pointer-events-none z-15" />
    </div>
  );
}
