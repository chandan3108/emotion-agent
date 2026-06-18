import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import jwt
import bcrypt

from .db import SessionLocal
from .models import User

# Configuration parameters
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-rem-security-key-1234567")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

security_agent = HTTPBearer()

router = APIRouter(prefix="/api/auth", tags=["authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic schemas
class AuthRegister(BaseModel):
    email: EmailStr
    password: str

class AuthLogin(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    email: Optional[str] = None
    user_id: Optional[str] = None
    error: Optional[str] = None

# Utility functions
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security_agent)) -> str:
    """Dependency to extract user ID from JWT token."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Auth endpoints
@router.post("/register", response_model=AuthResponse)
def register(payload: AuthRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        return AuthResponse(success=False, error="Email is already registered")

    if len(payload.password) < 6:
        return AuthResponse(success=False, error="Password must be at least 6 characters long")

    # Create user
    user_id = "user_" + secrets.token_hex(8)
    hashed = hash_password(payload.password)
    user = User(id=user_id, email=payload.email, hashed_password=hashed)
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        
        token = create_access_token(user_id)
        return AuthResponse(success=True, token=token, email=user.email, user_id=user_id)
    except Exception as e:
        db.rollback()
        return AuthResponse(success=False, error=str(e))

@router.post("/login", response_model=AuthResponse)
def login(payload: AuthLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        return AuthResponse(success=False, error="Invalid email or password")

    token = create_access_token(user.id)
    return AuthResponse(success=True, token=token, email=user.email, user_id=user.id)
