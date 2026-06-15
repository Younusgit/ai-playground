import os
import asyncpg
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None


async def init_db():
    global _pool
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    _pool = await asyncpg.create_pool(
        database_url,
        min_size=2,
        max_size=10,
        command_timeout=60
    )
    logger.info("Database pool created successfully")


async def get_db() -> asyncpg.Pool:
    if _pool is None:
        await init_db()
    return _pool


async def close_db():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
