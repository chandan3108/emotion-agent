# backend/ml_model.py
"""Emotion prediction powered by a locally trained ML model with
a safe heuristic fallback.

The flow is:
* Try to load a scikit-learn model from `models/emotion_model.joblib`
  (trained by `backend/train_model.py`).
* If loading succeeds, use the classifier to predict an emotion label
  (and probability-derived confidence) from the incoming feature dict.
* Always compute valence/arousal using the existing heuristic for now
  so the numbers stay stable, unless we later add regressors.
* If loading fails or no model exists yet, fall back to the heuristic
  only so the app keeps working out of the box.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import joblib

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "emotion_model.joblib")


def _get(x: Dict[str, Any], k: str, default: float = 0.0) -> float:
    v = x.get(k)
    if v is None:
        return default
    try:
        return float(v)
    except Exception:
        return default


def _heuristic_valence_arousal(payload: Dict[str, Any]) -> Dict[str, float]:
    """The original heuristic for valence & arousal.

    We keep this as a fallback and as a supplemental signal even
    when a trained model is available, so behaviour isn't brittle
    while you iterate on datasets.
    """

    mouth_opening = _get(payload, "mouth_opening", 0.0)
    lip_corner_pull = _get(payload, "lip_corner_pull", 0.0)
    brow_inner = _get(payload, "brow_inner_raise", 0.0)
    pitch = _get(payload, "pitch", 0.0)
    volume = _get(payload, "volume", 0.0)
    jitter = _get(payload, "jitter", 0.0)
    shimmer = _get(payload, "shimmer", 0.0)
    silence_duration = _get(payload, "silence_duration", 0.0)
    speaking_rate = _get(payload, "speaking_rate", 0.0)

    # simple heuristics for valence/arousal
    valence = (lip_corner_pull * 1.0) - (brow_inner * 0.2)
    arousal = (mouth_opening * 0.6) + (abs(pitch - 150) / 300.0) + (volume * 0.2)

    # small weighting for jitter/shimmer -> stress indicator
    arousal += (jitter + shimmer) * 0.5

    # speaking rate / silence influence arousal
    arousal += (max(0.0, speaking_rate - 3.0) * 0.05) - (silence_duration * 0.02)

    # clamp
    valence = max(-1.0, min(1.0, valence))
    arousal = max(-1.0, min(1.0, arousal))

    return {"valence": valence, "arousal": arousal}


class EmotionModel:
    """Wrapper around a trained sklearn model stored on disk.

    The joblib file is expected to contain at least:
        {
            "feature_cols": [...],
            "classifier": sklearn classifier,
        }
    """

    def __init__(self, model_path: str = MODEL_PATH) -> None:
        self.model_path = model_path
        self.feature_cols: Optional[list[str]] = None
        self.classifier: Any = None
        self.loaded: bool = False

        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.model_path):
            self.loaded = False
            return

        try:
            obj = joblib.load(self.model_path)
        except Exception:
            # If loading fails for any reason, stay in heuristic-only mode.
            self.loaded = False
            return

        self.feature_cols = obj.get("feature_cols")
        self.classifier = obj.get("classifier")

        self.loaded = bool(self.feature_cols and self.classifier)

    def reload(self) -> Dict[str, Any]:
        """Reload the joblib model from disk.

        Returns a small status dict for use in admin endpoints.
        """
        prev = self.loaded
        self._load()
        return {"previously_loaded": prev, "loaded": self.loaded}

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Predict emotion using ML model when available.

        Always returns the schema:
            {emotion, valence, arousal, confidence}
        """

        # Always compute heuristic valence/arousal as a baseline.
        ha = _heuristic_valence_arousal(payload)
        valence = ha["valence"]
        arousal = ha["arousal"]

        # If we don't have a trained model, just return the heuristic.
        if not self.loaded or not self.feature_cols or not self.classifier:
            emotion = _map_valence_arousal_to_label(valence, arousal)
            return {
                "emotion": emotion,
                "valence": round(valence, 3),
                "arousal": round(arousal, 3),
                # conservative but not random: mid-high confidence
                "confidence": 0.7,
            }

        # Build feature vector in fixed column order, robust to missing keys.
        row = []
        for col in self.feature_cols:
            v = payload.get(col)
            try:
                row.append(float(0.0 if v is None else v))
            except Exception:
                row.append(0.0)

        X = [row]

        # Class label
        try:
            pred_label = self.classifier.predict(X)[0]
        except Exception:
            # Fall back entirely to heuristics if anything goes wrong.
            emotion = _map_valence_arousal_to_label(valence, arousal)
            return {
                "emotion": emotion,
                "valence": round(valence, 3),
                "arousal": round(arousal, 3),
                "confidence": 0.7,
            }

        # Confidence from predict_proba if available.
        confidence = 0.75
        try:
            if hasattr(self.classifier, "predict_proba"):
                proba = self.classifier.predict_proba(X)[0]
                confidence = float(max(proba))
        except Exception:
            pass

        emotion = str(pred_label)

        # Small post-processing nudge: if the model calls something
        # neutral/calm/stressed but our heuristic valence+arousal say
        # "very low and negative", gently bias toward "sad". This
        # helps catch low-mood states without destroying the learned
        # classifier behaviour.
        if emotion in {"neutral", "calm", "stressed"} and valence < -0.4 and arousal < 0.4:
            emotion = "sad"
            confidence = max(confidence, 0.7)

        return {
            "emotion": emotion,
            "valence": round(valence, 3),
            "arousal": round(arousal, 3),
            "confidence": round(confidence, 3),
        }


def _map_valence_arousal_to_label(valence: float, arousal: float) -> str:
    """Original heuristic mapping from valence/arousal -> discrete label."""
    if arousal > 0.5 and valence > 0.2:
        return "excited"
    if arousal > 0.5 and valence <= 0.2:
        return "stressed"
    if valence > 0.3:
        return "happy"
    if valence < -0.3:
        return "sad"
    if arousal < -0.2:
        return "calm"
    return "neutral"


_MODEL = EmotionModel()


def reload_model() -> Dict[str, Any]:
    """Public function used by admin endpoints to refresh the model."""

    return _MODEL.reload()


def predict_emotion(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Module-level entrypoint used by the FastAPI router.

    Delegates to the loaded ML model; if no model is present, it
    automatically falls back to the heuristic behaviour.
    """

    return _MODEL.predict(payload)
