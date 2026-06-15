from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

from services.database import get_db

router = APIRouter()
security = HTTPBearer()

SECRET_KEY = os.getenv("JWT_SECRET", "change-this-secret")
ALGORITHM = "HS256"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register")
async def register(req: RegisterRequest):
    db = await get_db()
    existing = await db.fetchrow("SELECT id FROM users WHERE email=$1", req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
    user = await db.fetchrow(
        "INSERT INTO users (email, password_hash, username) VALUES ($1,$2,$3) RETURNING id, email, username",
        req.email, hashed, req.username
    )
    token = create_token(str(user["id"]), user["email"])
    return {"token": token, "user": {"id": str(user["id"]), "email": user["email"], "username": user["username"]}}


@router.post("/login")
async def login(req: LoginRequest):
    db = await get_db()
    user = await db.fetchrow("SELECT * FROM users WHERE email=$1 AND is_banned=FALSE", req.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    await db.execute("UPDATE users SET last_login=NOW() WHERE id=$1", user["id"])
    token = create_token(str(user["id"]), user["email"])
    return {"token": token, "user": {"id": str(user["id"]), "email": user["email"], "username": user["username"]}}


@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    db = await get_db()
    user = await db.fetchrow("SELECT id, email, username, credits, created_at FROM users WHERE id=$1", current_user["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)
