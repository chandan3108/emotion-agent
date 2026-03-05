# backend/realtime.py
from datetime import datetime
import csv
import os
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .realtime_schema import RealtimeFeatures
from .ml_model import predict_emotion


router = APIRouter()

LOG_PATH = os.path.join(os.path.dirname(__file__), "realtime_log.csv")
LABELED_LOG_PATH = os.path.join(os.path.dirname(__file__), "realtime_labeled.csv")


def _append_log_row(features: dict, prediction: dict) -> None:
    """Append a single training row to CSV for future ML."""
    row = {"timestamp": datetime.utcnow().isoformat()}
    # flatten prediction under prefixed keys
    for k, v in prediction.items():
        row[f"pred_{k}"] = v
    for k, v in features.items():
        row[k] = v

    file_exists = os.path.exists(LOG_PATH)
    with open(LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def _append_labeled_row(
    features: dict,
    true_emotion: str,
    true_valence: Optional[float] = None,
    true_arousal: Optional[float] = None,
) -> None:
    """Append a labeled row for supervised training (feedback loop)."""
    base_fields = ["timestamp"]
    feature_fields = sorted(features.keys())
    label_fields = ["true_emotion", "true_valence", "true_arousal"]
    fieldnames = base_fields + feature_fields + label_fields

    row = {name: None for name in fieldnames}
    row["timestamp"] = datetime.utcnow().isoformat()
    for k, v in features.items():
        row[k] = v
    row["true_emotion"] = true_emotion
    row["true_valence"] = true_valence
    row["true_arousal"] = true_arousal

    file_exists = os.path.exists(LABELED_LOG_PATH)
    with open(LABELED_LOG_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


@router.post("/realtime")
async def realtime_predict(payload: RealtimeFeatures):
    """Main realtime prediction endpoint.

    Accepts the full set of features (any subset allowed), forwards
    to the ML model and returns a prediction.
    """

    data = payload.dict()  # dict with all fields (values may be None)

    # ML model expects a dict; it will handle missing/None values
    prediction = predict_emotion(data)

    # Fire-and-forget logging for future ML training
    try:
        _append_log_row(data, prediction)
    except Exception:
        # Never break the API on logging errors
        pass

    return {
        "ok": True,
        "prediction": prediction,
        "received": data,
    }


class FeedbackPayload(BaseModel):
    """Payload for explicit user feedback on predictions."""

    features: RealtimeFeatures
    true_emotion: str
    true_valence: Optional[float] = None
    true_arousal: Optional[float] = None


@router.post("/realtime/feedback")
async def realtime_feedback(payload: FeedbackPayload):
    """Collect ground-truth labels for a given feature frame.

    Frontend can hit this after a prediction to say what the
    *actual* emotion was. These rows are then used by the
    offline training script to refine the model.
    """

    features = payload.features.dict()
    try:
        _append_labeled_row(
            features,
            true_emotion=payload.true_emotion,
            true_valence=payload.true_valence,
            true_arousal=payload.true_arousal,
        )
    except Exception:
        # Feedback should never break the app either.
        return {"ok": False}

    return {"ok": True}
