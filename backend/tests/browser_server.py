"""Opt-in, disposable browser-test server. Never imported by app.main.

TOWN_E2E_RESET_WORLD=1 TOWN_DATABASE_URL=sqlite:////.../e2e.db \
  python -m uvicorn tests.browser_server:app --port 8010
"""

# Application imports intentionally follow fail-closed checks to protect the live database.
# ruff: noqa: E402
import os
from pathlib import Path

# Fail closed: the fixture can never reset the regular application database.
if os.environ.get("TOWN_E2E_RESET_WORLD") != "1":
    raise RuntimeError("Browser reset server requires explicit TOWN_E2E_RESET_WORLD=1")
url = os.environ.get("TOWN_DATABASE_URL", "")
if not (url.startswith("sqlite:////") and Path(url.removeprefix("sqlite:///")).name == "e2e.db"):
    raise RuntimeError("Browser reset server requires an absolute disposable e2e.db path")

from app.main import app, runtime
from app.catalog import initial_world
from app.database import Session
from app.models import Departure, Event, World, WorldSample
from app.services.history import sample_world
from sqlalchemy import delete


@app.post("/__test/reset-world")
async def reset_world():
    async with runtime.lock:
        w = initial_world()
        # A fresh known climate draw; UI tests assert baseline recipe quantities.
        w["rng_seed"] = 0
        for a in w["agents"].values():
            a["mode"] = "manual"
        with Session.begin() as db:
            for model in (Departure, Event, WorldSample):
                db.execute(delete(model))
            row = db.get(World, 1)
            row.data = w
            row.revision += 1
            sample_world(db, w)
    return {"reset": True}
