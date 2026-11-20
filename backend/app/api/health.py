"""Process liveness is independent of database/world readiness."""

import asyncio
import time
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text
from ..config import settings
from ..database import engine
from ..services.container import runtime

router = APIRouter()


def database_ready():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@router.get("/api/health/live")
async def live():
    return {"ok": True, "version": "2.0.0"}


@router.get("/api/health")
@router.get("/api/health/ready")
async def ready(request: Request):
    task = getattr(request.app.state, "world_task", None)
    started = getattr(request.app.state, "started_at", 0)
    tick_age = time.monotonic() - (runtime.last_tick_at or started)
    clock_ok = bool(task and not task.done() and not runtime.last_cycle_failed)
    clock_ok = clock_ok and tick_age <= max(5, settings.tick_seconds * 3)
    db_ok = False
    if getattr(request.app.state, "ready", False):
        try:
            await asyncio.wait_for(asyncio.to_thread(database_ready), settings.health_timeout)
            db_ok = True
        except Exception:
            pass
    ok = db_ok and clock_ok
    return JSONResponse(
        {"ok": ok, "version": "2.0.0", "checks": {"database": db_ok, "world_clock": clock_ok}},
        status_code=200 if ok else 503,
    )
