"use client";

// Very lightweight audio feature extractor using the Web Audio API.
// It runs entirely in the browser and produces the same fields the
// backend expects: pitch, volume, jitter, shimmer, etc. These are
// approximations, but they are stable and bounded to [0,1].

export type AudioFeatures = {
  pitch: number; // 0–1 (mapped from ~60–400 Hz)
  pitch_stability: number; // 0–1 (1 = very stable pitch)
  volume: number; // 0–1 (RMS level)
  spectral_centroid: number; // 0–1 (low → dark, high → bright)
  spectral_rolloff: number; // 0–1 (how much energy in high freqs)
  zcr: number; // 0–1 zero-crossing rate
  jitter: number; // 0–1 (1 = very unstable pitch)
  shimmer: number; // 0–1 (1 = very unstable loudness)
  silence_duration: number; // 0–1 (0 = speaking, 1 = long silence)
  speaking_rate: number; // 0–1 (rough proxy, higher = more speech activity)
};

let audioCtx: AudioContext | null = null;
let analyser: AnalyserNode | null = null;
let source: MediaStreamAudioSourceNode | null = null;
let initialized = false;
let initializing = false;
let denied = false;

let timeData: Float32Array | null = null;
let freqData: Float32Array | null = null;
let lastFeatures: AudioFeatures | null = null;

let lastFrameTime = 0;
let silenceMs = 0;
const volumeHistory: number[] = [];
const pitchHistory: number[] = [];
const HISTORY = 30;

function clamp01(x: number): number {
  return Math.max(0, Math.min(1, x));
}

function ensureAudioContext(): AudioContext {
  if (audioCtx) return audioCtx;
  const Ctx = (window as any).AudioContext || (window as any).webkitAudioContext;
  if (!Ctx) {
    throw new Error("Web Audio API not supported in this browser");
  }
  audioCtx = new Ctx();
  return audioCtx;
}

export async function initAudio(): Promise<void> {
  if (initialized || initializing || denied) return;
  initializing = true;
  try {
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("getUserMedia not available");
    }

    const ctx = ensureAudioContext();
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      video: false,
    });

    source = ctx.createMediaStreamSource(stream);
    analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0.5;
    source.connect(analyser);

    timeData = new Float32Array(analyser.fftSize);
    freqData = new Float32Array(analyser.frequencyBinCount);

    lastFeatures = {
      pitch: 0,
      pitch_stability: 0.5,
      volume: 0,
      spectral_centroid: 0.5,
      spectral_rolloff: 0.5,
      zcr: 0,
      jitter: 0.5,
      shimmer: 0.5,
      silence_duration: 0,
      speaking_rate: 0,
    };

    lastFrameTime = performance.now();
    silenceMs = 0;

    const loop = () => {
      if (!analyser || !timeData || !freqData || !audioCtx) return;

      analyser.getFloatTimeDomainData(timeData);
      const now = performance.now();
      const dt = now - lastFrameTime;
      lastFrameTime = now;

      // --- Level & ZCR ---
      let sumSq = 0;
      let zeroCrossings = 0;
      let prev = timeData[0];
      for (let i = 0; i < timeData.length; i++) {
        const v = timeData[i];
        sumSq += v * v;
        if ((v >= 0 && prev < 0) || (v < 0 && prev >= 0)) zeroCrossings++;
        prev = v;
      }
      const rms = Math.sqrt(sumSq / timeData.length);
      const volume = clamp01(rms * 5); // simple scaling
      const zcr = clamp01(zeroCrossings / timeData.length * 5);

      // --- Spectral features ---
      analyser.getFloatFrequencyData(freqData);
      // Convert dB to linear magnitude
      const mags = new Float32Array(freqData.length);
      for (let i = 0; i < freqData.length; i++) {
        mags[i] = Math.pow(10, freqData[i] / 20);
      }

      const binHz = audioCtx.sampleRate / (2 * mags.length);
      let magSum = 0;
      let weightedFreqSum = 0;
      for (let i = 0; i < mags.length; i++) {
        const f = i * binHz;
        const m = mags[i];
        magSum += m;
        weightedFreqSum += f * m;
      }
      const centroidHz = magSum > 0 ? weightedFreqSum / magSum : 0;
      const spectral_centroid = clamp01(centroidHz / 4000); // 0–4 kHz

      let cumulative = 0;
      let rolloffHz = 0;
      const target = magSum * 0.85;
      for (let i = 0; i < mags.length; i++) {
        cumulative += mags[i];
        if (cumulative >= target) {
          rolloffHz = i * binHz;
          break;
        }
      }
      const spectral_rolloff = clamp01(rolloffHz / 4000);

      // --- Pitch estimate: highest peak in 60–400 Hz band ---
      let bestIdx = -1;
      let bestMag = -Infinity;
      const lowBin = Math.max(1, Math.floor(60 / binHz));
      const highBin = Math.min(mags.length - 1, Math.floor(400 / binHz));
      for (let i = lowBin; i <= highBin; i++) {
        if (mags[i] > bestMag) {
          bestMag = mags[i];
          bestIdx = i;
        }
      }
      const pitchHz = bestIdx > 0 ? bestIdx * binHz : 0;
      const pitchNorm = clamp01((pitchHz - 60) / (400 - 60));

      // --- Histories for jitter/shimmer & pitch stability ---
      volumeHistory.push(volume);
      if (volumeHistory.length > HISTORY) volumeHistory.shift();

      if (pitchHz > 50 && pitchHz < 500) {
        pitchHistory.push(pitchHz);
        if (pitchHistory.length > HISTORY) pitchHistory.shift();
      }

      function stability(values: number[]): number {
        if (values.length < 3) return 0.5;
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        if (mean === 0) return 0.5;
        const varSum = values.reduce((a, b) => a + (b - mean) * (b - mean), 0);
        const std = Math.sqrt(varSum / values.length);
        const rel = std / mean;
        // rel=0 -> 1.0, rel>=1 -> 0
        return clamp01(1 - Math.min(1, rel));
      }

      const pitch_stability = stability(pitchHistory);
      const shimmer = 1 - stability(volumeHistory);
      const jitter = 1 - pitch_stability;

      // --- Silence / speaking rate ---
      const SILENCE_THRESHOLD = 0.03;
      if (volume < SILENCE_THRESHOLD) {
        silenceMs += dt;
      } else {
        silenceMs = 0;
      }
      const silence_duration = clamp01(silenceMs / 3000); // 3s -> 1.0
      const speaking_rate = clamp01(1 - silence_duration); // inverse of silence

      lastFeatures = {
        pitch: pitchNorm,
        pitch_stability,
        volume,
        spectral_centroid,
        spectral_rolloff,
        zcr,
        jitter,
        shimmer: clamp01(shimmer),
        silence_duration,
        speaking_rate,
      };

      requestAnimationFrame(loop);
    };

    requestAnimationFrame(loop);
    initialized = true;
  } catch (err) {
    console.error("Audio init failed:", err);
    denied = true;
  } finally {
    initializing = false;
  }
}

export function getAudioFeatures(): AudioFeatures | null {
  return lastFeatures;
}

export function isAudioActive(): boolean {
  return initialized && !denied;
}
