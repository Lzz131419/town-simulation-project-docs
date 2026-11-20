import asyncio
from copy import deepcopy
import threading
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import create_engine, inspect, text, select
from sqlalchemy.exc import OperationalError
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.database import Base, Session
from app.models import World, ModelCall, ModelConfig, Event, Message
from app.catalog import initial_world
from app.domain.actions import validate_action
from app.domain.orders import post_order
from app.infrastructure.async_io import run_blocking
from app.infrastructure.migrations import migrate, configuration
from app.main import app, runtime
from app.runtime import TownRuntime
from app.config import encryption


def test_migrations_fresh_legacy_and_index_rollback_preserve_data(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    Base.metadata.create_all(engine)
    with engine.begin() as db:
        for table in inspect(db).get_table_names():
            for index in inspect(db).get_indexes(table):
                db.execute(text(f'DROP INDEX "{index["name"]}"'))
        db.execute(World.__table__.insert().values(id=1, revision=99, data=initial_world()))
        before = db.execute(text("SELECT revision, data FROM worlds")).fetchone()
    migrate(engine)
    migrate(engine)
    with engine.begin() as db:
        assert db.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0002"
        assert db.execute(text("SELECT revision, data FROM worlds")).fetchone() == before
        assert compare_metadata(MigrationContext.configure(db), Base.metadata) == []
        query_plan = str(
            db.execute(
                text(
                    "EXPLAIN QUERY PLAN SELECT * FROM events WHERE actor_id='wangjue' ORDER BY id DESC LIMIT 50"
                )
            ).fetchall()
        )
        assert "ix_events_actor_id_id" in query_plan
        config = configuration()
        config.attributes["connection"] = db
        command.downgrade(config, "0001")
        assert not inspect(db).get_indexes("events")
        command.upgrade(config, "head")
        assert db.execute(text("SELECT revision, data FROM worlds")).fetchone() == before
    engine.dispose()
    fresh = create_engine(f"sqlite:///{tmp_path / 'fresh.db'}")
    migrate(fresh)
    with fresh.connect() as db:
        assert compare_metadata(MigrationContext.configure(db), Base.metadata) == []
    fresh.dispose()


def test_migration_rejects_incompatible_legacy_schema(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'bad.db'}")
    with engine.begin() as db:
        db.execute(text("CREATE TABLE users (id TEXT PRIMARY KEY, name TEXT)"))
        db.execute(text("INSERT INTO users VALUES ('member', 'preserved')"))
    with pytest.raises(RuntimeError, match="Legacy schema mismatch"):
        migrate(engine)
    with engine.connect() as db:
        assert db.execute(text("SELECT name FROM users")).scalar() == "preserved"
    engine.dispose()


@pytest.mark.parametrize(
    "payload",
    [
        {"type": []},
        {"type": {}},
        {"type": "buy", "item": []},
        {"type": "delivery", "item": {}},
        {"type": "move", "place": []},
        {"type": "farm", "quantity": True},
        {"type": "farm", "quantity": 2},
        {"type": "farm", "item": "wood"},
        {"type": "farm", "place": "mine"},
        {"type": "social", "target_id": " "},
    ],
)
def test_malformed_model_actions_are_business_errors(payload):
    with pytest.raises(ValueError):
        validate_action(payload)


@pytest.mark.parametrize("quantity", [True, 1.5, "2"])
def test_quantities_are_integers_at_api_and_domain_boundaries(auth, quantity):
    before = auth.get("/api/world").json()["world"]
    for path, data in [
        ("/api/me/action", {"type": "farm", "quantity": quantity}),
        ("/api/orders", {"item": "wood", "quantity": quantity, "unit_price": 2}),
    ]:
        response = auth.post(path, json=data)
        assert response.status_code == 422 and response.json()["code"] == "invalid_input"
        assert response.headers["x-request-id"] == response.json()["request_id"]
    assert auth.get("/api/world").json()["world"] == before
    w = initial_world()
    old = deepcopy(w)
    with pytest.raises(ValueError):
        post_order(w, w["agents"]["wangjue"], "wood", quantity, 2, [])
    assert w == old


def test_readiness_reports_clock_and_storage_failures(auth, monkeypatch):
    import app.api.health as health

    assert auth.get("/api/health/ready").status_code == 200
    with monkeypatch.context() as patch:
        patch.setattr(runtime, "last_cycle_failed", True)
        response = auth.get("/api/health")
        assert response.status_code == 503 and not response.json()["checks"]["world_clock"]
        assert auth.get("/api/health/live").status_code == 200
    with monkeypatch.context() as patch:

        def broken():
            raise OperationalError("private SQL", {}, Exception("private database password"))

        patch.setattr(health, "database_ready", broken)
        response = auth.get("/api/health/ready")
        assert response.status_code == 503 and not response.json()["checks"]["database"]
        assert "private" not in response.text
    with monkeypatch.context() as patch:
        patch.setitem(
            app.state._state, "world_task", type("Ended", (), {"done": lambda self: True})()
        )
        assert auth.get("/api/health/ready").status_code == 503
    assert auth.get("/api/health/ready").status_code == 200


def test_error_envelope_does_not_echo_secrets(auth, monkeypatch):
    response = auth.put(
        "/api/model", json={"base_url": "secret" * 100, "model": "x", "api_key": "private-key"}
    )
    assert (
        response.status_code == 422
        and "private-key" not in response.text
        and "secret" not in response.text
    )

    def unavailable(uid):
        raise OperationalError("sensitive SQL", {}, Exception("password"))

    with monkeypatch.context() as patch:
        patch.setattr(runtime, "snapshot", unavailable)
        response = auth.get("/api/world")
        assert response.status_code == 503 and response.json()["code"] == "storage_unavailable"
        assert response.headers["x-request-id"] == response.json()["request_id"]
        assert "password" not in response.text and "sensitive" not in response.text
    assert auth.get("/api/world").status_code == 200


@pytest.mark.asyncio
async def test_cancelled_blocking_transaction_drains_before_unlock():
    lock = asyncio.Lock()
    entered, release, committed = threading.Event(), threading.Event(), threading.Event()

    def transaction():
        entered.set()
        assert release.wait(2)
        committed.set()

    async def operation():
        async with lock:
            await run_blocking(transaction)

    task = asyncio.create_task(operation())
    try:
        assert await asyncio.to_thread(entered.wait, 1)
        task.cancel()
        await asyncio.sleep(0.02)
        assert lock.locked() and not task.done() and not committed.is_set()
        task.cancel()  # Repeated cancellation cannot release the lock early either.
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert committed.is_set() and not lock.locked()


@pytest.mark.asyncio
async def test_login_hashing_does_not_block_liveness(client, monkeypatch):
    from app.api import auth

    original = auth.passwords.verify
    entered, release = threading.Event(), threading.Event()

    def slow(password, hashed):
        entered.set()
        assert release.wait(2)
        return original(password, hashed)

    monkeypatch.setattr(auth.passwords, "verify", slow)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        pending = asyncio.create_task(
            c.post("/api/auth/login", json={"username": "wangjue", "password": "wangjue"})
        )
        try:
            assert await asyncio.to_thread(entered.wait, 1)
            response = await asyncio.wait_for(c.get("/api/health/live"), 0.5)
            assert response.status_code == 200 and not pending.done()
        finally:
            release.set()
        assert (await pending).status_code == 200


@pytest.mark.asyncio
async def test_clock_survives_connection_validation_failure(monkeypatch):
    rt, progressed = TownRuntime(), asyncio.Event()
    ws = type("Socket", (), {"close": AsyncMock()})()
    rt.connect(ws, "wangjue", "test")
    count = 0

    def validate(_):
        nonlocal count
        count += 1
        if count == 1:
            raise OperationalError("test failure", {}, Exception())
        return True

    async def mutate(_):
        progressed.set()

    monkeypatch.setattr(rt, "valid_connection", validate)
    monkeypatch.setattr(rt, "mutate", mutate)
    task = asyncio.create_task(rt.run(0.01))
    try:
        await asyncio.wait_for(progressed.wait(), 1)
        assert count >= 2 and not task.done() and rt.last_tick_at is not None
        assert not rt.last_cycle_failed
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        await rt.shutdown()


@pytest.mark.asyncio
async def test_cancel_during_model_record_creation_leaves_no_running_call(auth, monkeypatch):
    import app.ai.provider as provider

    with Session.begin() as db:
        db.add(
            ModelConfig(
                user_id="wangjue",
                base_url="https://example.com/v1",
                model="test",
                encrypted_key=encryption().encrypt(b"test").decode(),
            )
        )
    original = provider.prepare_call
    entered, release = threading.Event(), threading.Event()

    def slow(*args):
        result = original(*args)
        entered.set()
        assert release.wait(2)
        return result

    monkeypatch.setattr(provider, "prepare_call", slow)
    monkeypatch.setattr(runtime, "online", lambda _: True)
    network = AsyncMock()
    monkeypatch.setattr(provider, "validate_base_url", network)
    task = asyncio.create_task(provider.ModelProvider(runtime).call("wangjue", "test", "", {}))
    try:
        assert await asyncio.to_thread(entered.wait, 1)
        task.cancel()
    finally:
        release.set()
    with pytest.raises(asyncio.CancelledError):
        await task
    network.assert_not_called()
    with Session() as db:
        assert db.scalar(select(ModelCall)).status == "cancelled"


def test_history_cursor_pagination_is_bounded_and_private(auth):
    with Session.begin() as db:
        for i in range(6):
            db.add(Event(tick=i, actor_id="wangjue", type="test", text=str(i), details={}))
            db.add(Message(sender_id="zhangguo", recipient_id="wangjue", text=str(i)))
        db.add(Message(sender_id="zhangguo", recipient_id="lizhanbo", text="not this inbox"))
    for endpoint in ["events?kind=test&", "messages?"]:
        first = auth.get("/api/" + endpoint + "limit=3").json()
        second = auth.get("/api/" + endpoint + f"limit=3&before={first[-1]['id']}").json()
        assert len(first) == len(second) == 3
        assert not {r["id"] for r in first} & {r["id"] for r in second}
        assert all(r["text"] != "not this inbox" for r in first + second)
        assert auth.get("/api/" + endpoint + "limit=1000").status_code == 422
        assert auth.get("/api/" + endpoint + "before=-1").status_code == 422
        assert auth.get("/api/" + endpoint + f"before={2**64}").status_code == 422


@pytest.mark.parametrize("conflicting", [False, True])
def test_migration_adopts_partial_indexes_and_rejects_wrong_definition(tmp_path, conflicting):
    engine = create_engine(f"sqlite:///{tmp_path / 'partial.db'}")
    with engine.begin() as db:
        config = configuration()
        config.attributes["connection"] = db
        command.upgrade(config, "0001")
        columns = "id" if conflicting else "actor_id, id"
        db.execute(text(f"CREATE INDEX ix_events_actor_id_id ON events ({columns})"))
    if conflicting:
        with pytest.raises(RuntimeError, match="Index definition mismatch"):
            migrate(engine)
        with engine.connect() as db:
            assert db.execute(text("SELECT version_num FROM alembic_version")).scalar() == "0001"
    else:
        migrate(engine)
        migrate(engine)
        with engine.connect() as db:
            assert compare_metadata(MigrationContext.configure(db), Base.metadata) == []
    engine.dispose()
