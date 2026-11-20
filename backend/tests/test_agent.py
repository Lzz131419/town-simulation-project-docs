import asyncio
import json
from unittest.mock import AsyncMock
import pytest
import httpx
from app.ai.planner import Planner
from app.ai.provider import validate_base_url
from app.main import runtime
from app.db import Session, ModelConfig, World
from app.config import encryption
from app.catalog import initial_world
from app.runtime import TownRuntime


@pytest.mark.asyncio
async def test_offline_gate_before_provider(monkeypatch):
    rt = TownRuntime()
    p = Planner(rt)
    spy = AsyncMock()
    monkeypatch.setattr(p, "call", spy)
    with pytest.raises(ValueError, match="离线"):
        await p.run("wangjue", "计划")
    spy.assert_not_called()


@pytest.mark.asyncio
async def test_disconnect_cancels_pending_call():
    rt = TownRuntime()
    ws = object()
    rt.connect(ws, "wangjue", "test-session")
    cancelled = asyncio.Event()

    async def wait():
        try:
            await asyncio.sleep(60)
        finally:
            cancelled.set()

    task = asyncio.create_task(wait())
    rt.calls["wangjue"] = task
    await asyncio.sleep(0)
    rt.disconnect(ws)
    with pytest.raises(asyncio.CancelledError):
        await task
    assert cancelled.is_set() and not rt.online("wangjue")


@pytest.mark.asyncio
async def test_model_plan_schema_blocks_unavailable_tools():
    p = Planner(TownRuntime())
    with pytest.raises(ValueError):
        await p.validate(
            {"result": {"summary": "x", "actions": [{"type": "transfer", "target": "other"}]}}
        )
    with pytest.raises(ValueError):
        await p.validate(
            {
                "result": {
                    "summary": "x",
                    "actions": [{"type": "buy", "item": "bread", "quantity": 500}],
                }
            }
        )
    r = await p.validate(
        {"result": {"summary": "先收获再烘焙", "actions": [{"type": "farm"}, {"type": "bake"}]}}
    )
    assert len(r["plan"]) == 2


@pytest.mark.asyncio
async def test_private_and_invalid_provider_urls():
    for url in [
        "http://127.0.0.1/v1",
        "https://127.0.0.1/v1",
        "https://[::1]/v1",
        "https://example.com:8443/v1",
        "https://u:p@example.com/v1",
    ]:
        with pytest.raises(ValueError):
            await validate_base_url(url)


def test_no_model_calls_in_offline_rules(auth, monkeypatch):
    from app.engine import tick_world

    w = initial_world()
    w["agents"]["wangjue"]["mode"] = "rules"
    w["agents"]["wangjue"]["plan"] = [{"type": "farm"}, {"type": "bake"}]
    spy = AsyncMock()
    monkeypatch.setattr("app.ai.planner.Planner.call", spy)
    events = []
    for _ in range(120):
        tick_world(w, events)
    assert w["agents"]["wangjue"]["completed"] > 0
    spy.assert_not_called()


def test_model_credentials_never_returned(auth):
    with Session.begin() as db:
        db.add(
            ModelConfig(
                user_id="wangjue",
                base_url="https://example.com/v1",
                model="test",
                encrypted_key=encryption().encrypt(b"test-private-key").decode(),
            )
        )
    r = auth.get("/api/model")
    assert r.status_code == 200 and r.json()["has_key"]
    assert "test-private-key" not in r.text and "encrypted_key" not in r.text
    auth.post("/api/auth/login", json={"username": "zhangguo", "password": "zhangguo"})
    assert not auth.get("/api/model").json()["configured"]


@pytest.mark.asyncio
async def test_langgraph_full_plan_flow(auth, monkeypatch):
    monkeypatch.setattr(runtime, "online", lambda uid: True)
    p = Planner(runtime)
    spy = AsyncMock(
        return_value={"summary": "先备料再烘焙", "actions": [{"type": "farm"}, {"type": "bake"}]}
    )
    monkeypatch.setattr(p, "call", spy)
    r = await p.run("wangjue", "做面包")
    assert r["summary"] == "先备料再烘焙"
    with Session() as db:
        a = db.get(World, 1).data["agents"]["wangjue"]
        assert (
            a["plan"] == [{"type": "farm", "quantity": 1}, {"type": "bake", "quantity": 1}]
            and a["mode"] == "manual"
        )
    assert spy.await_count == 1


@pytest.mark.asyncio
async def test_late_model_response_not_applied(auth, monkeypatch):
    online = True
    monkeypatch.setattr(runtime, "online", lambda _: online)
    p = Planner(runtime)

    async def provider(*args):
        nonlocal online
        online = False
        return {"summary": "已经离线", "actions": [{"type": "farm"}]}

    monkeypatch.setattr(p, "call", provider)
    with pytest.raises(ValueError, match="离线"):
        await p.run("wangjue", "计划")
    with Session() as db:
        assert db.get(World, 1).data["agents"]["wangjue"]["plan"] == []


@pytest.mark.asyncio
async def test_provider_http_payload_usage_and_bad_response(auth, monkeypatch):
    import app.ai.provider as mod
    from app.db import ModelCall
    from sqlalchemy import select

    with Session.begin() as db:
        db.add(
            ModelConfig(
                user_id="wangjue",
                base_url="https://provider.example/v1",
                model="my-model",
                encrypted_key=encryption().encrypt(b"dummy-private-key").decode(),
            )
        )
    monkeypatch.setattr(runtime, "online", lambda _: True)
    monkeypatch.setattr(
        mod, "validate_base_url", AsyncMock(return_value="https://provider.example/v1")
    )
    seen = []

    def handler(request):
        seen.append(request)
        assert request.headers["authorization"] == "Bearer dummy-private-key"
        payload = json.loads(request.content)
        assert payload["model"] == "my-model" and payload["max_tokens"] == 900
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": json.dumps({"summary": "测试成功", "actions": []})}}
                ],
                "usage": {"prompt_tokens": 120, "completion_tokens": 20},
            },
        )

    original = httpx.AsyncClient
    monkeypatch.setattr(
        mod.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs),
    )
    r = await Planner(runtime).run("wangjue", "连接测试", "test")
    assert r["summary"] == "测试成功" and len(seen) == 1
    with Session() as db:
        record = db.scalar(select(ModelCall).order_by(ModelCall.id.desc()))
        assert record.input_tokens == 120 and record.output_tokens == 20 and record.usage_reported
    assert b"dummy-private-key" not in seen[0].content
