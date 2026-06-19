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

class OAuthCallbackPayload(BaseModel):
    code: str
    redirect_uri: str

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


# OAuth Configurations
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "")


@router.get("/oauth/{provider}/url")
def get_oauth_url(provider: str, redirect_uri: str):
    import urllib.parse
    
    if provider == "google":
        if not GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Google OAuth not configured on server")
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "prompt": "select_account"
        }
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
        return {"url": url}
        
    elif provider == "discord":
        if not DISCORD_CLIENT_ID:
            raise HTTPException(status_code=400, detail="Discord OAuth not configured on server")
        params = {
            "client_id": DISCORD_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "identify email"
        }
        url = "https://discord.com/api/oauth2/authorize?" + urllib.parse.urlencode(params)
        return {"url": url}
        
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported OAuth provider: {provider}")


@router.post("/oauth/{provider}/callback", response_model=AuthResponse)
async def oauth_callback(provider: str, payload: OAuthCallbackPayload, db: Session = Depends(get_db)):
    import httpx
    
    email = None
    provider_user_id = None
    
    try:
        if provider == "google":
            if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
                return AuthResponse(success=False, error="Google OAuth credentials not configured")
                
            # 1. Exchange code for tokens
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": payload.code,
                        "client_id": GOOGLE_CLIENT_ID,
                        "client_secret": GOOGLE_CLIENT_SECRET,
                        "redirect_uri": payload.redirect_uri,
                        "grant_type": "authorization_code"
                    }
                )
                if token_resp.status_code >= 400:
                    return AuthResponse(success=False, error=f"Google token exchange failed: {token_resp.text}")
                
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                
                # 2. Get user info
                info_resp = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if info_resp.status_code >= 400:
                    return AuthResponse(success=False, error="Google user info fetch failed")
                
                info_data = info_resp.json()
                email = info_data.get("email")
                provider_user_id = info_data.get("sub")
                
        elif provider == "discord":
            if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
                return AuthResponse(success=False, error="Discord OAuth credentials not configured")
                
            # 1. Exchange code for access token
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://discord.com/api/oauth2/token",
                    data={
                        "client_id": DISCORD_CLIENT_ID,
                        "client_secret": DISCORD_CLIENT_SECRET,
                        "grant_type": "authorization_code",
                        "code": payload.code,
                        "redirect_uri": payload.redirect_uri
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                if token_resp.status_code >= 400:
                    return AuthResponse(success=False, error=f"Discord token exchange failed: {token_resp.text}")
                
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                
                # 2. Get user info
                info_resp = await client.get(
                    "https://discord.com/api/users/@me",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if info_resp.status_code >= 400:
                    return AuthResponse(success=False, error="Discord user info fetch failed")
                
                info_data = info_resp.json()
                email = info_data.get("email")
                provider_user_id = info_data.get("id")
                
        else:
            return AuthResponse(success=False, error=f"Unsupported OAuth provider: {provider}")
            
    except Exception as e:
        return AuthResponse(success=False, error=f"OAuth communication error: {str(e)}")
        
    if not email or not provider_user_id:
        return AuthResponse(success=False, error="Failed to retrieve profile details from provider")
        
    # 3. Handle user lookup and registration/merging
    user = None
    if provider == "google":
        user = db.query(User).filter(User.google_id == provider_user_id).first()
    elif provider == "discord":
        user = db.query(User).filter(User.discord_id == provider_user_id).first()
        
    # If not found by OAuth ID, check email to link/merge
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            if provider == "google":
                user.google_id = provider_user_id
            elif provider == "discord":
                user.discord_id = provider_user_id
            db.commit()
            db.refresh(user)
            
    # If still not found, register a brand new user
    if not user:
        user_id = "user_" + secrets.token_hex(8)
        user = User(
            id=user_id,
            email=email,
            hashed_password=None,
            google_id=provider_user_id if provider == "google" else None,
            discord_id=provider_user_id if provider == "discord" else None
        )
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            return AuthResponse(success=False, error=f"Failed to create user account: {str(e)}")
            
    # Automatically update mappings in UserLink for Discord logins
    if provider == "discord":
        try:
            from .models import UserLink
            link = db.query(UserLink).filter(UserLink.web_user_id == user.id).first()
            if not link:
                link = UserLink(web_user_id=user.id, discord_id=provider_user_id)
                db.add(link)
                db.commit()
        except Exception as le:
            print(f"Failed to link Discord user mappings (non-blocking): {le}")
            
    # Generate token
    token_str = create_access_token(user.id)
    return AuthResponse(success=True, token=token_str, email=user.email, user_id=user.id)


@router.post("/oauth/discord/link")
async def link_discord_oauth(
    payload: OAuthCallbackPayload,
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    import httpx
    from .models import UserLink
    
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Discord OAuth credentials not configured")
        
    try:
        # 1. Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://discord.com/api/oauth2/token",
                data={
                    "client_id": DISCORD_CLIENT_ID,
                    "client_secret": DISCORD_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "code": payload.code,
                    "redirect_uri": payload.redirect_uri
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            if token_resp.status_code >= 400:
                raise HTTPException(status_code=400, detail=f"Discord token exchange failed: {token_resp.text}")
            
            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            
            # 2. Get user info
            info_resp = await client.get(
                "https://discord.com/api/users/@me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if info_resp.status_code >= 400:
                raise HTTPException(status_code=400, detail="Discord user info fetch failed")
            
            info_data = info_resp.json()
            discord_user_id = info_data.get("id")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OAuth connection error: {str(e)}")
        
    if not discord_user_id:
        raise HTTPException(status_code=400, detail="Could not retrieve Discord User ID")
        
    # Check if this Discord account is already linked to another user
    existing_link = db.query(UserLink).filter(UserLink.discord_id == discord_user_id).first()
    if existing_link and existing_link.web_user_id != current_user_id:
        raise HTTPException(status_code=400, detail="This Discord account is already linked to another profile")
        
    # Update User model's discord_id
    user = db.query(User).filter(User.id == current_user_id).first()
    if user:
        user.discord_id = discord_user_id
        
    # Update UserLink table
    link = db.query(UserLink).filter(UserLink.web_user_id == current_user_id).first()
    if link:
        link.discord_id = discord_user_id
    else:
        link = UserLink(web_user_id=current_user_id, discord_id=discord_user_id)
        db.add(link)
        
    try:
        db.commit()
        return {"success": True, "discord_id": discord_user_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save linking: {str(e)}")

