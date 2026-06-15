from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import time

from api.routes.auth import get_current_user
from services.ai_service import ai_service
from services.database import get_db

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model_id: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048


@router.post("/stream")
async def stream_chat(req: ChatRequest, current_user=Depends(get_current_user)):
    db = await get_db()
    
    # Check user ban status
    user = await db.fetchrow("SELECT is_banned, credits FROM users WHERE id=$1", current_user["sub"])
    if not user or user["is_banned"]:
        raise HTTPException(status_code=403, detail="Account banned")
    
    # Get model info
    model = await db.fetchrow(
        "SELECT m.*, ak.key_value FROM models m JOIN api_keys ak ON m.provider=ak.provider WHERE m.id=$1 AND m.is_enabled=TRUE",
        req.model_id
    )
    if not model:
        raise HTTPException(status_code=404, detail="Model not found or disabled")
    
    # Check daily limit
    today_usage = await db.fetchval(
        "SELECT COUNT(*) FROM usage_logs WHERE user_id=$1 AND created_at > NOW() - INTERVAL '1 day'",
        current_user["sub"]
    )
    
    limits = await db.fetchrow("SELECT daily_message_limit FROM user_limits WHERE user_id=$1", current_user["sub"])
    daily_limit = limits["daily_message_limit"] if limits else 50
    
    if today_usage >= daily_limit:
        raise HTTPException(status_code=429, detail="Daily message limit reached")
    
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    start_time = time.time()
    full_response = []

    async def generate():
        nonlocal full_response
        try:
            async for chunk in ai_service.stream_chat(
                provider=model["provider"],
                model=model["model_name"],
                messages=messages,
                api_key=model["key_value"],
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            ):
                full_response.append(chunk)
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            
            # Log usage
            response_text = "".join(full_response)
            duration_ms = int((time.time() - start_time) * 1000)
            input_tokens = sum(len(m["content"].split()) for m in messages)
            output_tokens = len(response_text.split())
            
            await db.execute(
                """INSERT INTO usage_logs (user_id, model_id, input_tokens, output_tokens, duration_ms)
                   VALUES ($1, $2, $3, $4, $5)""",
                current_user["sub"], req.model_id, input_tokens, output_tokens, duration_ms
            )
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history")
async def chat_history(current_user=Depends(get_current_user), limit: int = 50):
    db = await get_db()
    logs = await db.fetch(
        """SELECT ul.*, m.display_name as model_name FROM usage_logs ul 
           JOIN models m ON ul.model_id=m.id 
           WHERE ul.user_id=$1 ORDER BY ul.created_at DESC LIMIT $2""",
        current_user["sub"], limit
    )
    return [dict(r) for r in logs]
