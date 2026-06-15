from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json

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
async def stream_chat(req: ChatRequest):
    db = await get_db()

    model = await db.fetchrow(
        """SELECT m.*, ak.key_value FROM models m 
           JOIN api_keys ak ON m.provider=ak.provider 
           WHERE m.id=$1 AND m.is_enabled=TRUE""",
        req.model_id
    )
    if not model:
        raise HTTPException(status_code=404, detail="Model not found or disabled")

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    async def generate():
        try:
            async for chunk in ai_service.stream_chat(
                provider=model["provider"],
                model=model["model_name"],
                messages=messages,
                api_key=model["key_value"],
                temperature=req.temperature,
                max_tokens=req.max_tokens,
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
