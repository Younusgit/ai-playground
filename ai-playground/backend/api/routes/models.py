from fastapi import APIRouter, HTTPException, Depends
from api.routes.auth import get_current_user
from services.database import get_db

router = APIRouter()


@router.get("/")
async def list_models(current_user=Depends(get_current_user)):
    db = await get_db()
    models = await db.fetch(
        "SELECT id, display_name, provider, model_name, description, is_enabled FROM models WHERE is_enabled=TRUE ORDER BY provider, display_name"
    )
    return [dict(m) for m in models]


@router.get("/all")
async def list_all_models(current_user=Depends(get_current_user)):
    db = await get_db()
    models = await db.fetch(
        "SELECT id, display_name, provider, model_name, description, is_enabled FROM models ORDER BY provider, display_name"
    )
    return [dict(m) for m in models]
