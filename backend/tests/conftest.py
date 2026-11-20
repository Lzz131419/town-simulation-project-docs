import os
import sys
import tempfile
import asyncio
from pathlib import Path

os.environ["TOWN_DATABASE_URL"] = "sqlite:///" + str(Path(tempfile.mkdtemp()) / "test.db")
os.environ["TOWN_TICK_SECONDS"] = "3600"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pytest
from fastapi.testclient import TestClient
from app.main import app, runtime
from app.db import Base, engine
from sqlalchemy import text


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    with engine.begin() as db:
        db.execute(text("DROP TABLE IF EXISTS alembic_version"))
    runtime.clients.clear()
    runtime.calls.clear()
    runtime.lock = asyncio.Lock()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    assert (
        client.post(
            "/api/auth/login", json={"username": "wangjue", "password": "wangjue"}
        ).status_code
        == 200
    )
    return client
