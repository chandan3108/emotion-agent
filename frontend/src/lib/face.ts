"use client";

let FaceLandmarker: any = null;
let FilesetResolver: any = null;
let faceLandmarker: any = null;
let videoEl: HTMLVideoElement | null = null;
let initialized = false;
let loading = false;

// Optional debug canvas for visualizing what MediaPipe sees.
let debugCanvas: HTMLCanvasElement | null = null;
let debugCtx: CanvasRenderingContext2D | null = null;

/**
 * Load MediaPipe from local ESM bundle in /public/mediapipe
 */
async function loadMediaPipe() {
  if (FaceLandmarker && FilesetResolver) {
    console.log("✅ Already loaded");
    return;
  }

  if (loading) {
    console.log("⏳ Already loading, waiting...");
    return new Promise((resolve) => {
      const check = setInterval(() => {
        if (FaceLandmarker && FilesetResolver) {
          clearInterval(check);
          resolve(true);
        }
      }, 100);
    });
  }

  loading = true;
  console.log("📦 Loading MediaPipe from local ESM bundle...");

  try {
    // vision_bundle.js is an ES module with named exports.
    // We import it directly instead of injecting a classic <script>,
    // which avoids the "Unexpected token 'export'" syntax error.
    const vision: any = await import(/* webpackIgnore: true */ "/mediapipe/vision_bundle.js");

    if (!vision) {
      throw new Error("MediaPipe ESM module not found");
    }

    FaceLandmarker = vision.FaceLandmarker;
    FilesetResolver = vision.FilesetResolver;

    if (!FaceLandmarker || !FilesetResolver) {
      console.error("❌ Missing required MediaPipe classes");
      throw new Error("FaceLandmarker or FilesetResolver not found in module");
    }

    console.log("✅ MediaPipe ESM module loaded successfully");
  } catch (err) {
    console.error("❌ Error while importing MediaPipe ESM bundle:", err);
    throw err;
  } finally {
    loading = false;
  }
}

export function setDebugCanvas(canvas: HTMLCanvasElement | null) {
  debugCanvas = canvas;
  debugCtx = canvas ? canvas.getContext("2d") : null;
}

function drawDebugFrame(landmarks: any[]) {
  if (!debugCanvas || !debugCtx || !videoEl) return;
  const vw = videoEl.videoWidth || 640;
  const vh = videoEl.videoHeight || 480;

  if (!vw || !vh) return;

  if (debugCanvas.width !== vw) debugCanvas.width = vw;
  if (debugCanvas.height !== vh) debugCanvas.height = vh;

  debugCtx.save();
  debugCtx.clearRect(0, 0, vw, vh);

  try {
    debugCtx.drawImage(videoEl, 0, 0, vw, vh);
  } catch {
    // drawImage can throw if video not ready yet; just skip this frame.
  }

  debugCtx.fillStyle = "rgba(0, 255, 0, 0.8)";
  for (const pt of landmarks as any[]) {
    const x = pt.x * vw;
    const y = pt.y * vh;
    debugCtx.beginPath();
    debugCtx.arc(x, y, 2, 0, Math.PI * 2);
    debugCtx.fill();
  }

  debugCtx.restore();
}

/**
 * Initialize Face Tracking
 */
export async function initFaceTracking() {
  if (initialized) {
    console.log("✅ Already initialized");
    return;
  }

  console.log("💫 Starting face tracking initialization...");

  try {
    console.log("Step 1: Loading MediaPipe...");
    await loadMediaPipe();
    console.log("✅ MediaPipe loaded");

    console.log("Step 2: Loading WASM files...");
    const vision = await FilesetResolver.forVisionTasks("/mediapipe/wasm");
    console.log("✅ WASM loaded");

    console.log("Step 3: Creating face landmarker...");
    faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
        delegate: "GPU",
      },
      runningMode: "VIDEO",
      numFaces: 1,
    });
    console.log("✅ Face landmarker created");

    console.log("Step 4: Setting up video element...");
    if (!videoEl) {
      videoEl = document.createElement("video");
      videoEl.autoplay = true;
      videoEl.playsInline = true;
      videoEl.muted = true;
      videoEl.style.display = "none";
      document.body.appendChild(videoEl);
    }

    console.log("Step 5: Requesting camera access...");
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: "user",
      },
      audio: false,
    });
    console.log("✅ Camera access granted");

    videoEl.srcObject = stream;

    console.log("Step 6: Waiting for video...");
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Video timeout"));
      }, 10000);

      videoEl!.onloadedmetadata = () => {
        clearTimeout(timeout);
        videoEl!.play()
          .then(() => {
            initialized = true;
            console.log("✅ Video playing");
            resolve();
          })
          .catch(reject);
      };
    });

    console.log("🎥✅ Face tracking ready!");
  } catch (error) {
    console.error("❌ Initialization failed:", error);
    initialized = false;
    throw error;
  }
}

export function getFaceLandmarks() {
  if (!faceLandmarker || !videoEl || videoEl.readyState < 2) return null;

  try {
    const now = performance.now();
    const result = faceLandmarker.detectForVideo(videoEl, now);
    const landmarks = result?.faceLandmarks?.[0] || null;

    if (landmarks) {
      drawDebugFrame(landmarks);
    }

    return landmarks;
  } catch (error) {
    console.error("Detection error:", error);
    return null;
  }
}

export function cleanupFaceTracking() {
  if (videoEl?.srcObject) {
    (videoEl.srcObject as MediaStream).getTracks().forEach((t) => t.stop());
  }
  videoEl?.parentNode?.removeChild(videoEl);
  videoEl = null;
  faceLandmarker = null;
  initialized = false;
}

