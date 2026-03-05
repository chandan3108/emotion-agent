"use client";

import { useState, useRef, useEffect } from "react";
import { sendRealtimeEvent, sendRealtimeFeedback, requestAgentReply } from "../lib/api";
import { initFaceTracking, getFaceLandmarks, setDebugCanvas } from "../lib/face";
import { initAudio, getAudioFeatures, isAudioActive } from "../lib/audio";

export default function HomePage() {
  const [result, setResult] = useState<any>(null);
  const [smoothed, setSmoothed] = useState({
    emotion: null as string | null,
    valence: null as number | null,
    arousal: null as number | null,
    confidence: null as number | null,
  });
  const [agentReply, setAgentReply] = useState<string | null>(null);
  const [agentLoading, setAgentLoading] = useState(false);
  type ChatMessage = { role: "user" | "assistant"; content: string; auto?: boolean };
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const chatMessagesRef = useRef<ChatMessage[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatInitialized, setChatInitialized] = useState(false);
  const lastUserActivityRef = useRef<number | null>(null);
  const idleTimeoutRef = useRef<number | null>(null);
  const [running, setRunning] = useState(false);
  const [faceReady, setFaceReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [landmarkCount, setLandmarkCount] = useState<number | null>(null);
  const [facePresent, setFacePresent] = useState(false);
  const [faceCoverage, setFaceCoverage] = useState<number | null>(null); // 0–1 area of face in frame
  const [audioReady, setAudioReady] = useState(false);
  const loopRef = useRef<any>(null);
  const animationRef = useRef<number | null>(null);
  const lastSmoothedRef = useRef({
    emotion: null as string | null,
    valence: null as number | null,
    arousal: null as number | null,
    confidence: null as number | null,
  });
  const debugCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const faceBoxRef = useRef<{ minX: number; minY: number; maxX: number; maxY: number } | null>(
    null,
  );

  // Hook up debug canvas to face tracker
  useEffect(() => {
    setDebugCanvas(debugCanvasRef.current);
    return () => setDebugCanvas(null);
  }, []);

  // Start face tracking + capture loop
  useEffect(() => {
    let mounted = true;

    async function setup() {
      try {
        await initFaceTracking();
        if (mounted) {
          setFaceReady(true);
          animationRef.current = requestAnimationFrame(captureLoop);
        }
      } catch (err) {
        console.error("Face tracking init failed:", err);
        if (mounted) {
          setError("Failed to initialize face tracking. Please allow camera access.");
        }
      }
    }

    setup();

    // Cleanup on unmount
    return () => {
      mounted = false;
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (loopRef.current) {
        clearInterval(loopRef.current);
      }
    };
  }, []);

  const TOTAL_LANDMARKS = 478; // MediaPipe face_landmarker model output size

  function captureLoop() {
    const lm = getFaceLandmarks();

    if (lm) {
      setFacePresent(true);
      // Count only landmarks with good visibility so the number changes
      // as parts of the face are occluded.
      const visibleCount = lm.filter((pt: any) =>
        pt.visibility == null ? true : pt.visibility > 0.5
      ).length;
      setLandmarkCount(visibleCount);

      // Approximate how much of the frame the face occupies using the
      // bounding box of all landmarks. This will shrink as you move away
      // or occlude parts of the face.
      let minX = 1,
        maxX = 0,
        minY = 1,
        maxY = 0;
      for (const pt of lm as any[]) {
        if (pt.x < minX) minX = pt.x;
        if (pt.x > maxX) maxX = pt.x;
        if (pt.y < minY) minY = pt.y;
        if (pt.y > maxY) maxY = pt.y;
      }
      const width = Math.max(0, Math.min(1, maxX) - Math.max(0, minX));
      const height = Math.max(0, Math.min(1, maxY) - Math.max(0, minY));
      const area = Math.max(0, Math.min(1, width * height));
      setFaceCoverage(area);
      faceBoxRef.current = { minX, minY, maxX, maxY };
    } else {
      setFacePresent(false);
      setLandmarkCount(null);
      setFaceCoverage(null);
      faceBoxRef.current = null;
    }

    animationRef.current = requestAnimationFrame(captureLoop);
  }

  // Helper math utilities for feature extraction
  function dist(a: any, b: any) {
    if (!a || !b) return 0;
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.hypot(dx, dy);
  }

  function lerp(a: number, b: number, t: number) {
    return a + (b - a) * t;
  }

  function clamp01(x: number) {
    return Math.max(0, Math.min(1, x));
  }

  // Compute face-related features from landmarks (0-1-ish range)
  function computeFaceFeatures(lm: any[]) {
    const p = (i: number) => lm?.[i];

    // Canonical scales
    const leftEyeOuter = p(33);
    const rightEyeOuter = p(263);
    const faceWidth = dist(leftEyeOuter, rightEyeOuter) || 1;

    const chin = p(152);
    const forehead = p(10) || p(9) || p(151);
    const faceHeight = dist(chin, forehead) || faceWidth;

    // Eyes
    const leftEyeInner = p(133);
    const leftEyeUpper = p(159);
    const leftEyeLower = p(145);
    const rightEyeInner = p(362);
    const rightEyeUpper = p(386);
    const rightEyeLower = p(374);

    const leftEyeWidth = dist(leftEyeOuter, leftEyeInner) || faceWidth;
    const rightEyeWidth = dist(rightEyeOuter, rightEyeInner) || faceWidth;

    const leftEyeOpenRaw = dist(leftEyeUpper, leftEyeLower) / leftEyeWidth;
    const rightEyeOpenRaw = dist(rightEyeUpper, rightEyeLower) / rightEyeWidth;

    const eye_openness_left = clamp01(lerp(0, 1, (leftEyeOpenRaw - 0.1) / 0.25));
    const eye_openness_right = clamp01(lerp(0, 1, (rightEyeOpenRaw - 0.1) / 0.25));

    const eye_asymmetry = Math.abs(eye_openness_left - eye_openness_right);

    // Iris-based gaze (rough)
    const leftIrisCenter = p(468);
    const rightIrisCenter = p(473);

    const leftEyeCenter = leftEyeOuter && leftEyeInner
      ? { x: (leftEyeOuter.x + leftEyeInner.x) / 2, y: (leftEyeOuter.y + leftEyeInner.y) / 2 }
      : leftEyeOuter || leftEyeInner;
    const rightEyeCenter = rightEyeOuter && rightEyeInner
      ? { x: (rightEyeOuter.x + rightEyeInner.x) / 2, y: (rightEyeOuter.y + rightEyeInner.y) / 2 }
      : rightEyeOuter || rightEyeInner;

    let eye_gaze_x = 0;
    let eye_gaze_y = 0;
    if (leftIrisCenter && leftEyeCenter && rightIrisCenter && rightEyeCenter) {
      const lx = (leftIrisCenter.x - leftEyeCenter.x) / (leftEyeWidth || faceWidth);
      const ly = (leftIrisCenter.y - leftEyeCenter.y) / (leftEyeWidth || faceWidth);
      const rx = (rightIrisCenter.x - rightEyeCenter.x) / (rightEyeWidth || faceWidth);
      const ry = (rightIrisCenter.y - rightEyeCenter.y) / (rightEyeWidth || faceWidth);
      eye_gaze_x = clamp01(0.5 + 2 * ((lx + rx) / 2));
      eye_gaze_y = clamp01(0.5 + 2 * ((ly + ry) / 2));
    }

    // Brows
    const leftBrowInner = p(70);
    const leftBrowOuter = p(46);
    const rightBrowInner = p(300);
    const rightBrowOuter = p(336);

    const eyeLineY = leftEyeCenter && rightEyeCenter
      ? (leftEyeCenter.y + rightEyeCenter.y) / 2
      : (leftEyeCenter?.y ?? rightEyeCenter?.y ?? 0.5);

    function browRaise(brow: any) {
      if (!brow) return 0.5;
      const dy = eyeLineY - brow.y; // positive when brow is higher
      return clamp01((dy * 1.5) / (faceHeight || 1) + 0.5);
    }

    const browInnerLeftRaise = browRaise(leftBrowInner);
    const browInnerRightRaise = browRaise(rightBrowInner);
    const browOuterLeftRaise = browRaise(leftBrowOuter);
    const browOuterRightRaise = browRaise(rightBrowOuter);

    const brow_inner_raise = (browInnerLeftRaise + browInnerRightRaise) / 2;
    const brow_outer_raise = (browOuterLeftRaise + browOuterRightRaise) / 2;
    const brow_lower = 1 - brow_inner_raise;
    const brow_asymmetry =
      Math.abs(browInnerLeftRaise - browInnerRightRaise) +
      Math.abs(browOuterLeftRaise - browOuterRightRaise);

    // Mouth
    const mouthLeft = p(61);
    const mouthRight = p(291);
    const upperLip = p(13);
    const lowerLip = p(14);

    const mouthWidth = dist(mouthLeft, mouthRight) || faceWidth;
    const mouthOpenRaw = dist(upperLip, lowerLip) / (faceHeight || 1);
    const mouth_opening = clamp01((mouthOpenRaw - 0.02) / 0.12);

    const neutralMouthWidth = faceWidth * 0.35;
    const widthRatio = mouthWidth / neutralMouthWidth;
    const lip_corner_pull = clamp01((widthRatio - 1) / 0.4); // smile/stretch
    const lip_pucker = clamp01((1 - widthRatio) / 0.4);
    const lip_stretch = lip_corner_pull;

    const mouth_asymmetry = clamp01(
      Math.abs((mouthLeft?.y ?? 0) - (mouthRight?.y ?? 0)) / (faceHeight || 1) * 4,
    );

    const noseBase = p(2) || p(1);
    const lip_corner_depress = clamp01(
      noseBase && mouthLeft && mouthRight
        ? ((dist(noseBase, mouthLeft) + dist(noseBase, mouthRight)) / 2) /
            (faceHeight || 1)
        : 0.5,
    );

    // Cheeks & nose
    const cheekLeft = p(50);
    const cheekRight = p(280);
    const eyeCenterY = eyeLineY;

    const cheek_raise = clamp01(
      1 -
        ((cheekLeft && cheekRight
          ? (cheekLeft.y + cheekRight.y) / 2
          : eyeCenterY) - eyeCenterY) /
          (faceHeight || 1) * 3,
    );

    const noseLeft = p(94);
    const noseRight = p(331);
    const nostrilWidth = dist(noseLeft, noseRight) || faceWidth * 0.2;
    const nostril_flare = clamp01((nostrilWidth / (faceWidth * 0.3) - 1) / 0.5 + 0.5);

    const noseBridge = p(168) || p(6);
    const nose_wrinkle = clamp01(
      noseBridge && noseBase
        ? ((noseBridge.y - noseBase.y) / (faceHeight || 1) + 0.5) * 2
        : 0.5,
    );

    // Head pose (very rough)
    const noseTip = p(1) || noseBase;
    const faceCenterX = (leftEyeCenter?.x ?? 0.5 + rightEyeCenter?.x ?? 0.5) / 2;
    const faceCenterY = (eyeCenterY + (noseBase?.y ?? eyeCenterY)) / 2;

    let head_yaw = 0.5;
    let head_pitch = 0.5;
    let head_roll = 0.5;

    if (noseTip) {
      head_yaw = clamp01(0.5 + 3 * ((noseTip.x - faceCenterX) / (faceWidth || 1)));
      head_pitch = clamp01(0.5 + 3 * ((noseTip.y - faceCenterY) / (faceHeight || 1)));
    }

    if (leftEyeCenter && rightEyeCenter) {
      const dx = rightEyeCenter.x - leftEyeCenter.x;
      const dy = rightEyeCenter.y - leftEyeCenter.y;
      const angle = Math.atan2(dy, dx); // 0 is horizontal
      head_roll = clamp01(0.5 + (angle / (Math.PI / 4)) * 0.5);
    }

    // Blink approximations
    const blink_level_left = 1 - eye_openness_left;
    const blink_level_right = 1 - eye_openness_right;
    const blink_rate = (blink_level_left + blink_level_right) / 2;
    const blink_duration = blink_rate; // single-frame proxy

    return {
      brow_inner_raise,
      brow_outer_raise,
      brow_lower,
      brow_asymmetry,
      eye_openness_left,
      eye_openness_right,
      blink_rate,
      blink_duration,
      eye_asymmetry,
      eye_gaze_x,
      eye_gaze_y,
      mouth_opening,
      lip_corner_pull,
      lip_corner_depress,
      lip_pucker,
      lip_stretch,
      mouth_asymmetry,
      cheek_raise,
      nose_wrinkle,
      nostril_flare,
      head_pitch,
      head_yaw,
      head_roll,
    };
  }

  // Fallback audio features if the microphone is unavailable.
  function generateSyntheticAudioFeatures() {
    return {
      pitch: 0.5,
      pitch_stability: 0.5,
      volume: 0,
      spectral_centroid: 0.5,
      spectral_rolloff: 0.5,
      zcr: 0,
      jitter: 0.5,
      shimmer: 0.5,
      silence_duration: 1,
      speaking_rate: 0,
    };
  }

  // Aggregate raw face+audio features into higher-level emotional signals.
  // All outputs are in [0,1] where 0 = low/negative, 1 = high/positive.
  function computeSummarySignals(face: any, audio: any) {
    const f = face || {};
    const a = audio || {};
    const get = (o: any, k: string, d: number) =>
      typeof o?.[k] === "number" && !Number.isNaN(o[k]) ? o[k] : d;

    // Convenience values
    const smile = get(f, "lip_corner_pull", 0.5);
    const browLower = get(f, "brow_lower", 0.5);
    const browInnerRaise = get(f, "brow_inner_raise", 0.5);
    const browOuterRaise = get(f, "brow_outer_raise", 0.5);
    const cheekRaise = get(f, "cheek_raise", 0.5);
    const noseWrinkle = get(f, "nose_wrinkle", 0.5);
    const nostrilFlare = get(f, "nostril_flare", 0.5);
    const mouthOpen = get(f, "mouth_opening", 0);
    const mouthAsym = get(f, "mouth_asymmetry", 0);
    const eyeOpenL = get(f, "eye_openness_left", 0.5);
    const eyeOpenR = get(f, "eye_openness_right", 0.5);
    const eyeAsym = get(f, "eye_asymmetry", 0);
    const headPitch = get(f, "head_pitch", 0.5);
    const headYaw = get(f, "head_yaw", 0.5);
    const headRoll = get(f, "head_roll", 0.5);

    const volume = get(a, "volume", 0);
    const pitchStability = get(a, "pitch_stability", 0.5);
    const spectralCentroid = get(a, "spectral_centroid", 0.5);
    const silence = get(a, "silence_duration", 0.5);
    const speakingRate = get(a, "speaking_rate", 0.5);

    const eyeActivation = (eyeOpenL + eyeOpenR) / 2;
    const headMovement =
      (Math.abs(headPitch - 0.5) + Math.abs(headYaw - 0.5) + Math.abs(headRoll - 0.5)) /
      3;
    const browTension = (browLower + noseWrinkle + nostrilFlare) / 3;
    const facialSymmetry = clamp01(1 - (mouthAsym + eyeAsym) / 2);
    const speechActivity = clamp01(1 - silence);

    // 1) Overall arousal / activation (how energized or intense things are)
    const summary_arousal = clamp01(
      0.35 * volume +
        0.15 * spectralCentroid +
        0.2 * eyeActivation +
        0.2 * (mouthOpen + headMovement) / 2 +
        0.1 * speakingRate,
    );

    // 2) Facial valence (positive vs negative affect from the face itself)
    const rawValenceFace =
      0.7 * smile + // smiles
      0.3 * cheekRaise -
      0.5 * browTension -
      0.3 * noseWrinkle -
      0.2 * mouthAsym;
    const summary_valence_face = clamp01(0.5 + rawValenceFace); // shift to [0,1]

    // 3) Stress / tension (higher when brows are tight, nose is wrinkled, etc.)
    const pitchInstability = clamp01(1 - pitchStability);
    const summary_stress = clamp01(
      0.45 * browTension +
        0.2 * pitchInstability +
        0.15 * headMovement +
        0.2 * (1 - facialSymmetry),
    );

    // 4) Engagement (how much you seem actively engaged in the interaction)
    const summary_engagement = clamp01(
      0.35 * summary_arousal +
        0.25 * eyeActivation +
        0.2 * speechActivity +
        0.2 * (mouthOpen + headMovement) / 2,
    );

    // 5) Expressed confidence (rough heuristic from valence, stress, symmetry)
    const summary_confidence = clamp01(
      0.4 * summary_valence_face +
        0.25 * (1 - summary_stress) +
        0.2 * facialSymmetry +
        0.15 * (1 - Math.abs(headRoll - 0.5)),
    );

    // 6) Overall emotion score & label (for high-level use / prompting)
    // Score: positive when valence high, stress low, engagement & confidence high.
    const overall_score_raw =
      0.4 * summary_valence_face +
      0.25 * (1 - summary_stress) +
      0.2 * summary_engagement +
      0.15 * summary_confidence;
    const summary_overall_emotion_score = clamp01(overall_score_raw);

    let summary_overall_emotion_label: string;
    if (summary_overall_emotion_score > 0.75 && summary_arousal > 0.6) {
      summary_overall_emotion_label = "high_positive_excited";
    } else if (summary_overall_emotion_score > 0.6) {
      summary_overall_emotion_label = "positive_calm";
    } else if (summary_overall_emotion_score < 0.35 && summary_stress > 0.6) {
      summary_overall_emotion_label = "stressed_or_anxious";
    } else if (summary_overall_emotion_score < 0.35 && summary_arousal < 0.4) {
      summary_overall_emotion_label = "low_mood_or_tired";
    } else if (summary_arousal < 0.3 && summary_engagement < 0.4) {
      summary_overall_emotion_label = "disengaged_or_bored";
    } else {
      summary_overall_emotion_label = "neutral_or_mixed";
    }

    return {
      summary_arousal,
      summary_valence_face,
      summary_stress,
      summary_engagement,
      summary_confidence,
      summary_overall_emotion_score,
      summary_overall_emotion_label,
    };
  }

  // Helper: schedule an auto check-in after a period of user inactivity.
  function scheduleIdleCheckin() {
    const IDLE_MS = 40_000; // 40 seconds of user silence
    if (idleTimeoutRef.current) {
      clearTimeout(idleTimeoutRef.current);
    }
    if (!chatInitialized) return;
    idleTimeoutRef.current = window.setTimeout(() => {
      void runAutoCheckin();
    }, IDLE_MS);
  }

  async function runAutoCheckin() {
    if (!chatInitialized || !result || agentLoading) return;

    const pred = result.prediction ?? {};
    const summary = result.received ?? {};

    const autoUserMsg = "Can you check in with me again based on how I seem right now?";
    const baseHistory = chatMessagesRef.current;
    const historyWithAuto: ChatMessage[] = [
      ...baseHistory,
      { role: "user" as const, content: autoUserMsg, auto: true },
    ];
    chatMessagesRef.current = historyWithAuto;
    setChatMessages(historyWithAuto);

    lastUserActivityRef.current = Date.now();
    setAgentLoading(true);
    try {
      const resp = await requestAgentReply({
        emotion: typeof pred.emotion === "string" ? pred.emotion : null,
        valence: typeof pred.valence === "number" ? pred.valence : null,
        arousal: typeof pred.arousal === "number" ? pred.arousal : null,
        stress:
          typeof summary.summary_stress === "number" ? summary.summary_stress : null,
        engagement:
          typeof summary.summary_engagement === "number"
            ? summary.summary_engagement
            : null,
        messages: historyWithAuto,
      });
      setAgentReply(resp.reply);
      const nextMessages: ChatMessage[] = [
        ...chatMessagesRef.current,
        { role: "assistant", content: resp.reply },
      ];
      chatMessagesRef.current = nextMessages;
      setChatMessages(nextMessages);
      lastUserActivityRef.current = Date.now();
      scheduleIdleCheckin();
    } catch (e) {
      console.error("Agent auto-checkin error", e);
    } finally {
      setAgentLoading(false);
    }
  }

  // Initialize the chat, seeding tone with current emotion once.
  async function handleAgentCheckIn() {
    if (!result || chatInitialized) return;

    const pred = result.prediction ?? {};
    const summary = result.received ?? {};

    setAgentLoading(true);
    try {
      const resp = await requestAgentReply({
        emotion: typeof pred.emotion === "string" ? pred.emotion : null,
        valence: typeof pred.valence === "number" ? pred.valence : null,
        arousal: typeof pred.arousal === "number" ? pred.arousal : null,
        stress:
          typeof summary.summary_stress === "number" ? summary.summary_stress : null,
        engagement:
          typeof summary.summary_engagement === "number"
            ? summary.summary_engagement
            : null,
        messages: [
          {
            role: "user",
            content:
              "Please check in with me based on how I seem right now and start the conversation.",
          },
        ],
      });
      setAgentReply(resp.reply);
      const initialMessages: ChatMessage[] = [
        {
          role: "assistant",
          content: resp.reply,
        },
      ];
      chatMessagesRef.current = initialMessages;
      setChatMessages(initialMessages);
      setChatInitialized(true);
      lastUserActivityRef.current = Date.now();
      scheduleIdleCheckin();
    } catch (e) {
      console.error("Agent error", e);
      setAgentReply("Something went wrong talking to the companion.");
    } finally {
      setAgentLoading(false);
    }
  }

  // realtime loop
  async function startRealtimeLoop() {
    if (running) return;

    setRunning(true);
    setError(null);

    // Try to start audio capture once, but don't fail hard if it
    // isn't available or the user denies permission.
    try {
      await initAudio();
      if (isAudioActive()) {
        setAudioReady(true);
      }
    } catch (e) {
      console.warn("Audio capture not available:", e);
      setAudioReady(false);
    }

    loopRef.current = setInterval(async () => {
      const lm = getFaceLandmarks();

      let frame: any;
      if (lm) {
        const faceFeatures = computeFaceFeatures(lm as any[]);
        const audioFeatures = getAudioFeatures() || generateSyntheticAudioFeatures();
        const summary = computeSummarySignals(faceFeatures, audioFeatures);
        frame = {
          ...faceFeatures,
          ...audioFeatures,
          ...summary,
          // Map legacy fields onto our calibrated summary values so
          // downstream code continues to work but now reflects your face.
          emotional_valence: summary.summary_valence_face,
          emotional_arousal: summary.summary_arousal,
        };
      } else {
        // Fallback to audio-only frame if face not available
        const audioFeatures = getAudioFeatures() || generateSyntheticAudioFeatures();
        const summary = computeSummarySignals({}, audioFeatures);
        frame = {
          // zeroed face features
          brow_inner_raise: 0,
          brow_outer_raise: 0,
          brow_lower: 0,
          brow_asymmetry: 0,
          eye_openness_left: 0,
          eye_openness_right: 0,
          blink_rate: 0,
          blink_duration: 0,
          eye_asymmetry: 0,
          eye_gaze_x: 0.5,
          eye_gaze_y: 0.5,
          mouth_opening: 0,
          lip_corner_pull: 0,
          lip_corner_depress: 0,
          lip_pucker: 0,
          lip_stretch: 0,
          mouth_asymmetry: 0,
          cheek_raise: 0,
          nose_wrinkle: 0,
          nostril_flare: 0,
          head_pitch: 0.5,
          head_yaw: 0.5,
          head_roll: 0.5,
          ...audioFeatures,
          ...summary,
          // Neutral-ish valence/arousal when no face
          emotional_valence: 0.5,
          emotional_arousal: summary.summary_arousal,
        };
      }

      // Attach a face snapshot from the debug canvas if available so the
      // backend Hugging Face model can use it. This does not affect the
      // existing numeric feature pipeline.
      const canvas = debugCanvasRef.current;
      if (canvas) {
        try {
          const bbox = faceBoxRef.current;
          if (bbox && canvas.width && canvas.height) {
            const { minX, minY, maxX, maxY } = bbox;
            // Expand box a bit for context
            const pad = 0.15;
            const sx = Math.max(0, (minX - pad) * canvas.width);
            const sy = Math.max(0, (minY - pad) * canvas.height);
            const ex = Math.min(1, maxX + pad) * canvas.width;
            const ey = Math.min(1, maxY + pad) * canvas.height;
            const sw = Math.max(1, ex - sx);
            const sh = Math.max(1, ey - sy);

            const off = document.createElement("canvas");
            off.width = 224;
            off.height = 224;
            const octx = off.getContext("2d");
            if (octx) {
              octx.drawImage(canvas, sx, sy, sw, sh, 0, 0, off.width, off.height);
              frame.face_image = off.toDataURL("image/jpeg", 0.8);
            } else {
              frame.face_image = canvas.toDataURL("image/jpeg", 0.7);
            }
          } else {
            // Fallback: full frame
            frame.face_image = canvas.toDataURL("image/jpeg", 0.7);
          }
        } catch {
          // ignore encoding errors
        }
      }

      try {
        const res = await sendRealtimeEvent(frame);
        setResult(res);

        // Temporal smoothing for prediction fields so the UI feels
        // more continuous and less jittery frame-to-frame.
        const raw = res?.prediction ?? {};
        const prev = lastSmoothedRef.current;
        const alpha = 0.2; // 0 < alpha <= 1, lower = smoother/slower

        const blend = (prevVal: number | null, nextVal: unknown): number | null => {
          const n = typeof nextVal === "number" && !Number.isNaN(nextVal) ? nextVal : null;
          if (n == null) return prevVal;
          if (prevVal == null) return n;
          return prevVal * (1 - alpha) + n * alpha;
        };

        const next = {
          emotion: typeof raw.emotion === "string" ? raw.emotion : prev.emotion,
          valence: blend(prev.valence, raw.valence),
          arousal: blend(prev.arousal, raw.arousal),
          confidence: blend(prev.confidence, raw.confidence),
        };

        lastSmoothedRef.current = next;
        setSmoothed(next);
      } catch (e) {
        console.error("Realtime Error:", e);
        setError("Connection error. Retrying...");
      }
    }, 300);
  }

  function stopRealtimeLoop() {
    setRunning(false);
    clearInterval(loopRef.current);
    setError(null);
  }

  // Cleanup any pending idle timeout when component unmounts.
  useEffect(() => {
    return () => {
      if (idleTimeoutRef.current) {
        clearTimeout(idleTimeoutRef.current);
      }
    };
  }, []);

  return (
    <main style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}>
      <h1>Realtime Emotion Engine</h1>

      <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
        <p style={{ opacity: 0.7 }}>
          {faceReady ? "✅ Face tracking active" : "⏳ Initializing face tracking..."}
        </p>
        <p style={{ opacity: 0.7, marginTop: "0.25rem" }}>
          {audioReady ? "🎙️ Voice features active" : "(Optional) Enable microphone for voice features"}
        </p>
        {faceReady && (
          <div style={{ marginTop: "0.5rem" }}>
            <canvas
              ref={debugCanvasRef}
              style={{
                width: 200,
                height: 150,
                borderRadius: 8,
                background: "#000",
              }}
            />
          </div>
        )}
        {faceReady && (
          <p style={{ opacity: 0.8 }}>
            {facePresent
              ? `Visible landmarks: ${landmarkCount ?? 0} / ${TOTAL_LANDMARKS}` +
                (faceCoverage != null
                  ? ` • face size ~ ${Math.round(faceCoverage * 100)}% of frame`
                  : "")
              : "No face detected"}
          </p>
        )}
        {error && (
          <p style={{ color: "red", marginTop: "0.5rem" }}>{error}</p>
        )}
      </div>

      {!running ? (
        <button 
          onClick={startRealtimeLoop}
          disabled={!faceReady}
          style={{ 
            padding: "0.5rem 1rem",
            cursor: faceReady ? "pointer" : "not-allowed",
            opacity: faceReady ? 1 : 0.5
          }}
        >
          Start Realtime
        </button>
      ) : (
        <button 
          onClick={stopRealtimeLoop}
          style={{ padding: "0.5rem 1rem" }}
        >
          Stop Realtime
        </button>
      )}

      {result && (
        <div style={{ marginTop: "1.5rem" }}>
          <h2>Prediction</h2>
          <div style={{ 
            background: "#f5f5f5", 
            padding: "1rem", 
            borderRadius: "8px",
            marginBottom: "1rem"
          }}>
            <p>
              <strong>Emotion:</strong>{" "}
              {smoothed.emotion || result?.prediction?.emotion || "N/A"}
            </p>
            <p>
              <strong>Valence:</strong>{" "}
              {smoothed.valence != null
                ? smoothed.valence.toFixed(3)
                : result?.prediction?.valence?.toFixed(3) || "N/A"}
            </p>
            <p>
              <strong>Arousal:</strong>{" "}
              {smoothed.arousal != null
                ? smoothed.arousal.toFixed(3)
                : result?.prediction?.arousal?.toFixed(3) || "N/A"}
            </p>
            <p>
              <strong>Confidence:</strong>{" "}
              {smoothed.confidence != null
                ? smoothed.confidence.toFixed(3)
                : result?.prediction?.confidence?.toFixed(3) || "N/A"}
            </p>
          </div>

          <details>
            <summary style={{ cursor: "pointer", marginBottom: "0.5rem" }}>
              Show full response
            </summary>
            <pre style={{ 
              background: "#2d2d2d", 
              color: "#f8f8f2",
              padding: "1rem",
              borderRadius: "4px",
              overflow: "auto",
              fontSize: "0.85rem"
            }}>
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>

          {/* Simple feedback UI to label current prediction */}
          <div style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid #ddd" }}>
            <p style={{ marginBottom: "0.5rem" }}>Was this prediction accurate?</p>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              {['happy', 'excited', 'stressed', 'sad', 'calm', 'neutral'].map((label) => (
                <button
                  key={label}
                  type="button"
                  onClick={async () => {
                    try {
                      const features = result?.received ?? {};
                      await sendRealtimeFeedback({
                        features,
                        true_emotion: label,
                      });
                      // eslint-disable-next-line no-alert
                      alert(`Thanks! Logged feedback as "${label}".`);
                    } catch (err) {
                      console.error('Feedback error', err);
                      // eslint-disable-next-line no-alert
                      alert('Failed to send feedback.');
                    }
                  }}
                  style={{
                    padding: "0.25rem 0.75rem",
                    borderRadius: 999,
                    border: "1px solid #ccc",
                    background: "white",
                    cursor: "pointer",
                    fontSize: "0.85rem",
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Emotion-aware companion section */}
          <div style={{ marginTop: "2rem", paddingTop: "1rem", borderTop: "1px solid #ddd" }}>
            <h2>Companion</h2>
            <p style={{ marginBottom: "0.75rem", opacity: 0.8 }}>
              Click once to start a conversation tuned to your current emotion, then chat normally.
            </p>
            <button
              type="button"
              onClick={handleAgentCheckIn}
              style={{ padding: "0.5rem 1rem", borderRadius: 999, cursor: "pointer" }}
              disabled={agentLoading || chatInitialized}
            >
              {chatInitialized ? "Companion Ready" : agentLoading ? "Thinking..." : "Ask Companion"}
            </button>

            {/* Chat history */}
            {chatMessages.length > 0 && (
              <div
                style={{
                  marginTop: "1rem",
                  padding: "1rem",
                  borderRadius: 8,
                  background: "#eef5ff",
                  maxHeight: 260,
                  overflowY: "auto",
                }}
              >
                {chatMessages
                  // Keep user-typed messages and all assistant messages.
                  // Only hide synthetic auto user prompts.
                  .filter((m) => !(m.role === "user" && m.auto === true))
                  .map((m, idx) => (
                    <div
                      key={idx}
                      style={{
                        marginBottom: "0.5rem",
                        textAlign: m.role === "user" ? "right" : "left",
                      }}
                    >
                      <span
                        style={{
                          display: "inline-block",
                          padding: "0.35rem 0.7rem",
                          borderRadius: 12,
                          background: m.role === "user" ? "#d1eaff" : "#ffffff",
                        }}
                      >
                        {m.content}
                      </span>
                    </div>
                  ))}
              </div>
            )}

            {/* Input for continuing the conversation */}
            <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder={
                  chatInitialized
                    ? "Type a message to your companion..."
                    : "Click \"Ask Companion\" to start the conversation"
                }
                disabled={!chatInitialized}
                style={{
                  flex: 1,
                  padding: "0.5rem 0.75rem",
                  borderRadius: 999,
                  border: "1px solid #ccc",
                }}
              />
              <button
                type="button"
                disabled={!chatInitialized || !chatInput || agentLoading}
                onClick={async () => {
                  if (!chatInitialized || !chatInput) return;
                  const nextMessages: ChatMessage[] = [
                    ...chatMessagesRef.current,
                    { role: "user" as const, content: chatInput },
                  ];
                  chatMessagesRef.current = nextMessages;
                  setChatMessages(nextMessages);
                  lastUserActivityRef.current = Date.now();
                  scheduleIdleCheckin();
                  const toSend = nextMessages;
                  setChatInput("");
                  setAgentLoading(true);
                  try {
                    const resp = await requestAgentReply({
                      // After the first turn, we don't need to resend emotion; history carries context.
                      emotion: null,
                      valence: null,
                      arousal: null,
                      stress: null,
                      engagement: null,
                      messages: toSend,
                    });
                    setAgentReply(resp.reply);
                    const updated: ChatMessage[] = [
                      ...chatMessagesRef.current,
                      { role: "assistant", content: resp.reply },
                    ];
                    chatMessagesRef.current = updated;
                    setChatMessages(updated);
                    // Do not reset lastUserActivity here; we track *user* inactivity.
                  } catch (e) {
                    console.error("Agent error", e);
                    setAgentReply("Something went wrong talking to the companion.");
                  } finally {
                    setAgentLoading(false);
                  }
                }}
                style={{
                  padding: "0.5rem 0.9rem",
                  borderRadius: 999,
                  border: "none",
                  background: "#0070f3",
                  color: "white",
                  cursor: chatInitialized ? "pointer" : "not-allowed",
                }}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
