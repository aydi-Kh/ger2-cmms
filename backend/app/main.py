"""
GER2 CMMS — FastAPI Application Entry Point
Registers routers, middleware, health check, Prometheus metrics, CORS, and startup hooks.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.api.v1.routers import assets, workorders, ai_agents, compliance, costs, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("GER2 CMMS API starting", version=settings.APP_VERSION)
    # Start Kafka consumers in background
    from app.integrations.kafka.consumer import start_consumers
    await start_consumers()
    yield
    logger.info("GER2 CMMS API shutting down")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="GER2 Medical Centers — Advanced CMMS REST API",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
PREFIX = settings.API_V1_PREFIX
app.include_router(auth.router,       prefix=PREFIX)
app.include_router(assets.router,     prefix=PREFIX)
app.include_router(workorders.router, prefix=PREFIX)
app.include_router(ai_agents.router,  prefix=PREFIX)
app.include_router(compliance.router, prefix=PREFIX)
app.include_router(costs.router,      prefix=PREFIX)

# ── Prometheus metrics endpoint ───────────────────────────────────────────────
if settings.PROMETHEUS_ENABLED:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.get("/readiness", tags=["Health"])
async def readiness():
    from app.core.database import engine
    from app.core.cache import get_redis
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy", fromlist=["text"]).text("SELECT 1"))
        r = await get_redis()
        await r.ping()
        return {"status": "ready", "db": "ok", "redis": "ok"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503
