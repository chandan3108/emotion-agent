from pydantic import BaseModel
from typing import Optional

class RealtimeFeatures(BaseModel):
    # FACE: BROWS
    brow_inner_raise: Optional[float] = None
    brow_outer_raise: Optional[float] = None
    brow_lower: Optional[float] = None
    brow_asymmetry: Optional[float] = None

    # FACE: EYES
    eye_openness_left: Optional[float] = None
    eye_openness_right: Optional[float] = None
    blink_rate: Optional[float] = None
    blink_duration: Optional[float] = None
    eye_asymmetry: Optional[float] = None
    eye_gaze_x: Optional[float] = None
    eye_gaze_y: Optional[float] = None

    # FACE: MOUTH
    mouth_opening: Optional[float] = None
    lip_corner_pull: Optional[float] = None
    lip_corner_depress: Optional[float] = None
    lip_pucker: Optional[float] = None
    lip_stretch: Optional[float] = None
    mouth_asymmetry: Optional[float] = None

    # FACE: CHEEKS & NOSE
    cheek_raise: Optional[float] = None
    nose_wrinkle: Optional[float] = None
    nostril_flare: Optional[float] = None

    # HEAD POSE
    head_pitch: Optional[float] = None
    head_yaw: Optional[float] = None
    head_roll: Optional[float] = None

    # VOICE ACOUSTIC FEATURES
    pitch: Optional[float] = None
    pitch_stability: Optional[float] = None
    volume: Optional[float] = None
    spectral_centroid: Optional[float] = None
    spectral_rolloff: Optional[float] = None
    zcr: Optional[float] = None
    jitter: Optional[float] = None
    shimmer: Optional[float] = None

    # VOICE BEHAVIORAL
    silence_duration: Optional[float] = None
    speaking_rate: Optional[float] = None

    # HIGH-LEVEL EMOTION TARGETS
    emotional_valence: Optional[float] = None
    emotional_arousal: Optional[float] = None

    # DERIVED SUMMARY SIGNALS (optional; frontend may include these)
    summary_arousal: Optional[float] = None
    summary_valence_face: Optional[float] = None
    summary_stress: Optional[float] = None
    summary_engagement: Optional[float] = None
    summary_confidence: Optional[float] = None
    summary_overall_emotion_score: Optional[float] = None
    summary_overall_emotion_label: Optional[str] = None

    # Optional base64-encoded face image for direct vision models
    face_image: Optional[str] = None
