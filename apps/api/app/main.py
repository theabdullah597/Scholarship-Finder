import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.config import settings
from app.db.session import engine
from app.redis import close_redis

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("opportunityabroad.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting OpportunityAbroad API (%s)...", settings.ENVIRONMENT)
    yield
    logger.info("Shutting down OpportunityAbroad API...")
    await close_redis()
    await engine.dispose()
    logger.info("Resources cleaned up successfully.")


app = FastAPI(
    title="OpportunityAbroad API",
    description="Backend API for OpportunityAbroad scholarship & internship platform.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Welcome to OpportunityAbroad API",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
