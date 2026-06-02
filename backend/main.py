from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load backend/.env relative to main.py
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from .db import SessionLocal
from .models import EmotionEvent
from .realtime import router as realtime_router
from .ml_model import reload_model
from .agent import router as agent_router
from .game_api import router as game_api_router

app = FastAPI()


# Database session generator

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "backend ok"}


@app.get("/health")
def health():
    """Health check for deployment monitoring."""
    return {"status": "healthy", "service": "emotion-agent"}


@app.on_event("startup")
async def startup_event():
    import os
    print("🚀 Emotion Agent API starting...")
    print(f"   GROQ_API_KEY: {'✅ set' if os.getenv('GROQ_API_KEY') else '❌ missing'}")
    print(f"   MODEL_ID: {os.getenv('MODEL_ID', 'default')}")


# Routers
app.include_router(realtime_router)
app.include_router(agent_router)
app.include_router(game_api_router)


@app.post("/admin/reload_model")
def admin_reload_model():
    """Hot-reload the emotion model from disk.

    Call this after running `python train_model.py` (from backend directory)
    to start using the newly trained model without restarting the server.
    """

    status = reload_model()
    return {"ok": True, **status}


@app.post("/ingest")
async def ingest(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    event = EmotionEvent(**data)
    db.add(event)
    db.commit()
    db.refresh(event)

    print("Received:", data)

    # Debug mode: print valid model columns
    print("Model columns:", EmotionEvent.__table__.columns.keys())

    return {"ok": True, "id": event.id}
