from fastapi import APIRouter
from services.database import get_db

router = APIRouter()


@router.get("/")
async def list_models():
    db = await get_db()
    models = await db.fetch(
        """SELECT id, display_name, provider, model_name, description 
           FROM models WHERE is_enabled=TRUE 
           ORDER BY provider, display_name"""
    )
    return [dict(m) for m in models]
