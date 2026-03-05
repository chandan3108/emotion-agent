from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.sql import func
from .db import Base

class EmotionEvent(Base):
    __tablename__ = "emotion_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)

    # ----- FACE FEATURES: BROWS -----
    brow_inner_raise = Column(Float)
    brow_outer_raise = Column(Float)
    brow_lower = Column(Float)
    brow_asymmetry = Column(Float)

    # ----- FACE FEATURES: EYES -----
    eye_openness_left = Column(Float)
    eye_openness_right = Column(Float)
    blink_rate = Column(Float)
    blink_duration = Column(Float)
    eye_asymmetry = Column(Float)
    eye_gaze_x = Column(Float)
    eye_gaze_y = Column(Float)

    # ----- FACE FEATURES: MOUTH -----
    mouth_opening = Column(Float)
    lip_corner_pull = Column(Float)
    lip_corner_depress = Column(Float)
    lip_pucker = Column(Float)
    lip_stretch = Column(Float)
    mouth_asymmetry = Column(Float)

    # ----- FACE FEATURES: CHEEKS / NOSE -----
    cheek_raise = Column(Float)
    nose_wrinkle = Column(Float)
    nostril_flare = Column(Float)

    # ----- HEAD POSE -----
    head_pitch = Column(Float)
    head_yaw = Column(Float)
    head_roll = Column(Float)

    # ----- VOICE FEATURES: ACOUSTIC -----
    pitch = Column(Float)
    pitch_stability = Column(Float)
    volume = Column(Float)
    spectral_centroid = Column(Float)
    spectral_rolloff = Column(Float)
    zcr = Column(Float)
    jitter = Column(Float)
    shimmer = Column(Float)

    # ----- VOICE FEATURES: BEHAVIORAL -----
    silence_duration = Column(Float)
    speaking_rate = Column(Float)

    # ----- HIGH-LEVEL EMOTIONAL OUTPUT -----
    emotional_valence = Column(Float)
    emotional_arousal = Column(Float)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

