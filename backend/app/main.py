from .bootstrap import initialize
from .infrastructure.async_io import run_blocking
from .infrastructure.http import configure_http
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
import time
from sqlalchemy import select, func
from .telemetry import metrics
from .models import ModelCall
from fastapi.staticfiles import StaticFiles
from .config import ROOT, settings
from .database import Session
from .services.container import runtime
from .api import auth, profile, world, orders, messages, ai, archives, realtime, health


@asynccontextmanager
async def lifespan(app):
    app.state.ready = False
    await asyncio.wait_for(run_blocking(initialize), timeout=settings.startup_timeout)
    runtime.last_tick_at = None
    runtime.last_cycle_failed = False
    app.state.started_at = time.monotonic()
    world_task = asyncio.create_task(runtime.run(settings.tick_seconds), name="town-world-clock")
    app.state.world_task = world_task
    app.state.ready = True
    try:
        yield
    finally:
        app.state.ready = False
        world_task.cancel()
        calls = list(runtime.calls.values())
        for call in calls:
            call.cancel()
        await asyncio.gather(world_task, *calls, return_exceptions=True)
        await runtime.shutdown()


app = FastAPI(title="雾河镇 · 共享世界", version="2.0.0", lifespan=lifespan)


@app.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics():
    with Session() as db:
        records = db.execute(
            select(ModelCall.status, func.count()).group_by(ModelCall.status)
        ).all()
    text = metrics.render()
    for status, count in records:
        if status in {"running", "received", "failed", "cancelled"}:
            text += f'town_llm_calls{{status="{status}"}} {count}\n'
    return PlainTextResponse(text, media_type="text/plain; version=0.0.4")


configure_http(app)


for module in [auth, profile, world, orders, messages, ai, archives, realtime, health]:
    app.include_router(module.router)

# One backend worker owns the world clock. Serve production assets from the same origin.
DIST = ROOT / "frontend/dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    def index():
        return FileResponse(DIST / "index.html")
