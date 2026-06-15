from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from api.routes import chat, models, admin
from middleware.rate_limiter import RateLimitMiddleware
from services.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Playground API...")
    await init_db()
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="AI Playground API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(models.router, prefix="/api/models", tags=["Models"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/")
async def root():
    return {"message": "AI Playground API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
