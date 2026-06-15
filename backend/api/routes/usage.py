from fastapi import APIRouter, Depends
from api.routes.auth import get_current_user
from services.database import get_db

router = APIRouter()


@router.get("/my")
async def my_usage(current_user=Depends(get_current_user)):
    db = await get_db()
    today = await db.fetchval(
        "SELECT COUNT(*) FROM usage_logs WHERE user_id=$1 AND created_at > NOW() - INTERVAL '1 day'",
        current_user["sub"]
    )
    week = await db.fetchval(
        "SELECT COUNT(*) FROM usage_logs WHERE user_id=$1 AND created_at > NOW() - INTERVAL '7 days'",
        current_user["sub"]
    )
    total = await db.fetchval("SELECT COUNT(*) FROM usage_logs WHERE user_id=$1", current_user["sub"])
    limits = await db.fetchrow("SELECT daily_message_limit FROM user_limits WHERE user_id=$1", current_user["sub"])
    daily_limit = limits["daily_message_limit"] if limits else 50
    return {
        "today": today,
        "week": week,
        "total": total,
        "daily_limit": daily_limit,
        "remaining_today": max(0, daily_limit - today)
    }
