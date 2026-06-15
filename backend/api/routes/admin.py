from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import os

from api.routes.auth import get_current_user
from services.database import get_db

router = APIRouter()

ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")


async def require_admin(current_user=Depends(get_current_user)):
    if current_user["email"] not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


class ApiKeyRequest(BaseModel):
    provider: str
    key_value: str
    label: Optional[str] = None


class ModelToggleRequest(BaseModel):
    model_id: str
    enabled: bool


class BanRequest(BaseModel):
    user_id: str
    reason: Optional[str] = None


class LimitRequest(BaseModel):
    user_id: str
    daily_message_limit: int


class BroadcastRequest(BaseModel):
    message: str


@router.get("/stats")
async def get_stats(admin=Depends(require_admin)):
    db = await get_db()
    total_users = await db.fetchval("SELECT COUNT(*) FROM users")
    total_messages = await db.fetchval("SELECT COUNT(*) FROM usage_logs")
    today_messages = await db.fetchval("SELECT COUNT(*) FROM usage_logs WHERE created_at > NOW() - INTERVAL '1 day'")
    active_models = await db.fetchval("SELECT COUNT(*) FROM models WHERE is_enabled=TRUE")
    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "today_messages": today_messages,
        "active_models": active_models
    }


@router.get("/users")
async def list_users(admin=Depends(require_admin), limit: int = 100):
    db = await get_db()
    users = await db.fetch(
        "SELECT id, email, username, credits, is_banned, created_at, last_login FROM users ORDER BY created_at DESC LIMIT $1",
        limit
    )
    return [dict(u) for u in users]


@router.post("/api-keys")
async def add_api_key(req: ApiKeyRequest, admin=Depends(require_admin)):
    db = await get_db()
    existing = await db.fetchrow("SELECT id FROM api_keys WHERE provider=$1", req.provider)
    if existing:
        await db.execute("UPDATE api_keys SET key_value=$1, label=$2, updated_at=NOW() WHERE provider=$3",
                         req.key_value, req.label, req.provider)
        return {"message": f"API key for {req.provider} updated"}
    
    await db.execute(
        "INSERT INTO api_keys (provider, key_value, label) VALUES ($1,$2,$3)",
        req.provider, req.key_value, req.label
    )
    return {"message": f"API key for {req.provider} added"}


@router.delete("/api-keys/{provider}")
async def delete_api_key(provider: str, admin=Depends(require_admin)):
    db = await get_db()
    await db.execute("DELETE FROM api_keys WHERE provider=$1", provider)
    return {"message": f"API key for {provider} deleted"}


@router.get("/api-keys")
async def list_api_keys(admin=Depends(require_admin)):
    db = await get_db()
    keys = await db.fetch("SELECT provider, label, created_at, updated_at FROM api_keys")
    return [dict(k) for k in keys]


@router.post("/models/toggle")
async def toggle_model(req: ModelToggleRequest, admin=Depends(require_admin)):
    db = await get_db()
    await db.execute("UPDATE models SET is_enabled=$1 WHERE id=$2", req.enabled, req.model_id)
    return {"message": f"Model {'enabled' if req.enabled else 'disabled'}"}


@router.post("/users/ban")
async def ban_user(req: BanRequest, admin=Depends(require_admin)):
    db = await get_db()
    await db.execute("UPDATE users SET is_banned=TRUE WHERE id=$1", req.user_id)
    return {"message": "User banned"}


@router.post("/users/unban")
async def unban_user(req: BanRequest, admin=Depends(require_admin)):
    db = await get_db()
    await db.execute("UPDATE users SET is_banned=FALSE WHERE id=$1", req.user_id)
    return {"message": "User unbanned"}


@router.post("/limits")
async def set_limit(req: LimitRequest, admin=Depends(require_admin)):
    db = await get_db()
    existing = await db.fetchrow("SELECT id FROM user_limits WHERE user_id=$1", req.user_id)
    if existing:
        await db.execute("UPDATE user_limits SET daily_message_limit=$1 WHERE user_id=$2",
                         req.daily_message_limit, req.user_id)
    else:
        await db.execute("INSERT INTO user_limits (user_id, daily_message_limit) VALUES ($1,$2)",
                         req.user_id, req.daily_message_limit)
    return {"message": "Limit updated"}


@router.get("/models")
async def admin_list_models(admin=Depends(require_admin)):
    db = await get_db()
    models = await db.fetch("SELECT * FROM models ORDER BY provider, display_name")
    return [dict(m) for m in models]
