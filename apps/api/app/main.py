import json
import logging
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.config import settings
from app.db.session import engine
from app.redis import close_redis
from app.services.rate_limit import allow_request


class JsonFormatter(logging.Formatter):
    """Emit structured logs without request bodies or personally identifying data."""

    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            },
            ensure_ascii=True,
        )

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=settings.LOG_LEVEL, handlers=[handler], force=True)
logger = logging.getLogger("opportunityabroad.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting OpportunityAbroad API (%s)...", settings.ENVIRONMENT)
    if not settings.is_production:
        try:
            from sqlalchemy import func, select

            from app.db.session import AsyncSessionLocal
            from app.models.opportunity import Opportunity
            from app.scripts.seed_opportunities import seed_data

            async with AsyncSessionLocal() as session:
                opportunity_count = (
                    await session.execute(select(func.count(Opportunity.id)))
                ).scalar_one()
            if opportunity_count == 0:
                await seed_data()
                logger.info("Development database seeded with sample opportunities.")
        except Exception as exc:
            logger.warning("Development data seed skipped: %s", type(exc).__name__)
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


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = None
    auth_prefix = "/api/v1/auth/"
    if request.method == "POST" and request.url.path.startswith(auth_prefix):
        endpoint = request.url.path.removeprefix(auth_prefix)
        limits = {
            "login": (10, 60),
            "register": (5, 3600),
            "forgot-password": (5, 3600),
            "reset-password": (10, 3600),
            "refresh": (30, 60),
        }
        if endpoint in limits:
            limit, window = limits[endpoint]
            client_ip = request.client.host if request.client else "unknown"
            allowed, remaining = await allow_request(f"auth-rate:{endpoint}:{client_ip}", limit, window)
            if not allowed:
                response = JSONResponse(
                    status_code=429,
                    content={"detail": "Too many authentication requests. Please try again later."},
                    headers={"Retry-After": str(window)},
                )
            else:
                response = await call_next(request)
                response.headers["X-RateLimit-Remaining"] = str(remaining)
    if response is None:
        response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    )
    return response


if settings.is_production and "*" in settings.allowed_origins_list:
    raise RuntimeError("Wildcard CORS origins are not allowed in production.")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
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
