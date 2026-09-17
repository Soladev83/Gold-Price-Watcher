"""
Gold Price Watcher Ethiopia — FastAPI application entry point (multi-user).
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.routes import router as main_router
from app.api.telegram_webhook import router as webhook_router
from app.core.config import settings
from app.db.database import init_db
from app.scheduler.jobs import create_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Gold Price Watcher Ethiopia",
    description=(
        "Multi-user Ethiopian gold price monitoring with Telegram alerts. "
        "Prices are reference rates — not dealer quotes."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(webhook_router, prefix="/api")


# ---------------------------------------------------------------------------
# Keep-alive endpoint
# Pinged by GitHub Actions every 14 minutes to prevent free-tier sleep.
# Also useful as an uptime-monitor target.
# ---------------------------------------------------------------------------

import time as _time

_start_time = _time.time()


@app.get("/ping", tags=["system"], include_in_schema=False)
def ping():
    """
    Lightweight keep-alive endpoint.
    Returns uptime so you can confirm the service is live.
    """
    uptime_seconds = int(_time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return {
        "status": "alive",
        "uptime": f"{hours}h {minutes}m {seconds}s",
    }


@app.on_event("startup")
async def on_startup():
    logger.info("Initialising database...")
    init_db()
    logger.info("Starting scheduler...")
    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Gold Price Watcher v2 is running.")


@app.on_event("shutdown")
async def on_shutdown():
    scheduler = getattr(app.state, "scheduler", None)
    if scheduler:
        scheduler.shutdown(wait=False)
