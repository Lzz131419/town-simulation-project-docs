from app.world_map import LAYOUT
import asyncio
from copy import deepcopy
import json
import threading

import pytest
from sqlalchemy import select
from app.catalog import initial_world, PLACES
from app.runtime import TownRuntime
from app.realtime.protocol import personalize, delta
from app.api.realtime import valid_origin
from app.domain.scheduler import fallback_action, tick_world
from app.domain.actions import execute
from app.domain.economy import collect_daily_levy
from app.domain.rules import check_invariants
from app.domain.migration import upgrade_world
from app.pathfinding import route, advance, blocked
from app.ai.response import parse_response
from app.database import Session
from app.models import World, WorldSample
from app.services.history import sample_world
from app.balance import balance


class Socket:
    def __init__(self, slow=False):
        self.packets = []
        self.slow = slow
        self.started = asyncio.Event()
        self.delivered = asyncio.Event()
        self.release = asyncio.Event()
        self.closed = False

    async def send_json(self, packet):
        self.started.set()
        if self.slow:
            await self.release.wait()
        self.packets.append(deepcopy(packet))
        self.delivered.set()

    async def close(self, code=1000):
        self.closed = True


def packet(revision=0):
    return {"type": "world", "revision": revision, "world": initial_world(), "events": []}


@pytest.mark.asyncio
async def test_slow_socket_never_holds_transaction_or_grows_queue(auth):
    rt = TownRuntime()
    slow, fast = Socket(True), Socket()
    rt.connect(slow, "wangjue", "slow", 2)
    rt.connect(fast, "zhangguo", "fast", 2)
    try:
        await rt.broadcast()
        await asyncio.wait_for(slow.started.wait(), 1)
        await asyncio.wait_for(fast.delivered.wait(), 1)
        for _ in range(5):
            await asyncio.wait_for(rt.mutate(lambda w, e: tick_world(w, e)), 0.8)
        assert not slow.packets  # The slow client still has not completed its first send.
        assert rt.clients[slow]["queue"].qsize() == 1
        slow.release.set()
        await asyncio.wait_for(slow.delivered.wait(), 1)
        for _ in range(100):
            if slow.packets[-1]["revision"] == 5 and fast.packets[-1]["revision"] == 5:
                break
            await asyncio.sleep(0.01)
        assert fast.packets[-1]["revision"] == slow.packets[-1]["revision"] == 5
        for previous, current in zip(slow.packets, slow.packets[1:]):
            assert current["base_revision"] == previous["revision"]
        assert all("policy" not in p.get("agents", {}).get("wangjue", {}) for p in fast.packets)
    finally:
        await rt.shutdown()


@pytest.mark.asyncio
async def test_cancelled_worker_keeps_lock_until_transaction_finishes(auth, monkeypatch):
    rt = TownRuntime()
    entered, release = threading.Event(), threading.Event()
    original = rt._commit

    def delayed(fn):
        entered.set()
        assert release.wait(3)
        return original(fn)

    monkeypatch.setattr(rt, "_commit", delayed)
    first = asyncio.create_task(rt.mutate(lambda w, e: tick_world(w, e)))
    try:
        assert await asyncio.to_thread(entered.wait, 1)
        first.cancel()
        second = asyncio.create_task(rt.mutate(lambda w, e: tick_world(w, e)))
        # Event-loop responsiveness and lock ownership while worker is blocked.
        await asyncio.sleep(0.02)
        assert rt.lock.locked() and not first.done() and not second.done()
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await first
        await asyncio.wait_for(second, 2)
        assert rt.snapshot("wangjue")["revision"] == 2
    finally:
        release.set()
        await rt.shutdown()


@pytest.mark.asyncio
async def test_resync_sends_full_state_even_at_same_revision(auth):
    rt, ws = TownRuntime(), Socket()
    rt.connect(ws, "wangjue", "x", 2)
    try:
        await rt.broadcast()
        await asyncio.wait_for(ws.delivered.wait(), 1)
        ws.delivered.clear()
        await rt.resync(ws)
        await asyncio.wait_for(ws.delivered.wait(), 1)
        assert [p["type"] for p in ws.packets] == ["world", "world"]
    finally:
        await rt.shutdown()


def test_delta_roundtrip_and_private_fields():
    old = personalize(packet(), "wangjue", {"wangjue"})
    new = deepcopy(old)
    new["revision"] = 4
    new["world"]["agents"]["wangjue"]["x"] += 10
    new["world"]["tick"] += 4
    new["events"] = [{"id": 2, "tick": 4, "actor_id": "wangjue", "type": "move", "text": "到达"}]
    patch = delta(old, new)
    restored = deepcopy(old["world"])
    restored.update(patch["set"])
    restored["agents"].update(patch["agents"])
    assert restored == new["world"]
    assert len(json.dumps(patch)) < len(json.dumps(new)) / 2
    assert "policy" in new["world"]["agents"]["wangjue"]
    assert "policy" not in new["world"]["agents"]["zhangguo"]


def test_websocket_protocol2_patch_and_resync(auth):
    with auth.websocket_connect("/api/ws?protocol=2") as ws:
        first = ws.receive_json()
        assert first["type"] == "world"
        assert auth.post("/api/me/action", json={"type": "eat"}).status_code == 200
        patch = ws.receive_json()
        assert patch["type"] == "patch" and patch["base_revision"] == first["revision"]
        assert patch["agents"]["wangjue"]["inventory"]["bread"] == 2
        ws.send_text("resync")
        full = ws.receive_json()
        assert full["type"] == "world" and full["revision"] == patch["revision"]
        ws.send_text("ping")
        assert ws.receive_json() == {"type": "pong"}


@pytest.mark.parametrize(
    "origin",
    [
        "https://evil-town.test",
        "https://town.test.evil.test",
        "https://sub.town.test",
        "https://user@town.test",
        "https://town.test/path",
        "https://town.test?x=1",
        "https://town.test:443",
    ],
)
def test_websocket_origin_exact_match(origin):
    assert not valid_origin(origin, "town.test")
    assert valid_origin("https://town.test", "town.test")


def test_daily_levy_preserves_money_and_personal_reserve():
    w, events = initial_world(), []
    a = w["agents"]["wangjue"]
    a["cash"] += 421
    w["treasury"] -= 421
    a["policy"]["reserve"] = 400
    collect_daily_levy(w, events)
    assert a["cash"] == 495 and events[0]["details"]["amount"] == 6
    assert w["agents"]["zhangguo"]["cash"] == 80
    check_invariants(w)


def test_poor_treasury_full_bag_and_lonely_social_do_not_fail_forever():
    w = initial_world()
    a = w["agents"]["wangjue"]
    a["inventory"] = {k: 0 for k in a["inventory"]}
    a["inventory"]["wood"] = 30
    w["market"]["wood"] = balance.pricing.basic_target_stock
    w["treasury"] = 2
    assert fallback_action(w, a) is None
    w["treasury"] = 7
    assert fallback_action(w, a) == {"type": "sell", "item": "wood", "quantity": 2}
    a["inventory"]["wood"] = 0
    a["policy"]["fallback"] = "social"
    a["x"], a["y"] = 1400, 900
    assert fallback_action(w, a) is None
    a["policy"]["fallback"] = "work"
    w["treasury"] = 0
    assert fallback_action(w, a)["type"] == "farm"


def test_npc_schedule_hunger_and_rest():
    w = initial_world()
    a = w["agents"]["npc-1"]
    w["tick"] = 84  # 22:00
    assert fallback_action(w, a)["type"] == "rest"
    from app.domain.homes import home_destination
    target = home_destination(w, a)
    a["x"], a["y"], a["energy"] = target["x"], target["y"], 100
    assert fallback_action(w, a) is None
    a["hunger"] = 90
    assert fallback_action(w, a)["type"] == "eat"
    a["energy"] = 10
    execute(w, a, {"type": "rest"}, [])
    assert a["energy"] == 10 and a["sleeping"]["phase"] == "light"
    tick_world(w, [])
    assert a["energy"] == 17


def test_ten_days_rules_preserve_invariants_and_continue_activity():
    w, events = initial_world(), []
    for a in w["agents"].values():
        a["mode"] = "rules"
    for _ in range(1440):
        tick_world(w, events)
    check_invariants(w)
    assert all(a["completed"] > 5 for a in w["agents"].values())
    assert any(e["type"] == "fiscal" for e in events)
    assert any(e["tick"] > 1300 and e["type"] not in {"blocked", "fiscal", "levy"} for e in events)


def test_history_upsert_retention_and_report(auth, monkeypatch):
    monkeypatch.setattr(balance.simulation, "history_limit", 3)
    with Session.begin() as db:
        w = deepcopy(db.get(World, 1).data)
        for t in range(0, 31, 6):
            w["tick"] = t
            sample_world(db, w)
        sample_world(db, w)
    data = auth.get("/api/report").json()
    assert [p["tick"] for p in data["series"]] == [18, 24, 30]
    assert all(
        p["treasury"] + p["resident_cash"] + p["escrow"] == w["economy_total"]
        for p in data["series"]
    )
    assert data["fiscal"]["protected_cash"] == 100
    with Session() as db:
        assert len(db.scalars(select(WorldSample)).all()) == 3
    r = auth.get("/api/health")
    assert r.json()["ok"] and len(r.headers["x-request-id"]) == 32
    assert auth.get("/metrics").status_code == 200


def test_old_save_upgrade_is_additive_and_idempotent():
    w = initial_world()
    for a in w["agents"].values():
        del a["inventory"]["fruit"]
    del w["market"]["fruit"]
    cash = w["economy_total"]
    assert upgrade_world(w)
    assert not upgrade_world(w)
    assert w["market"]["fruit"] == 0 and w["economy_total"] == cash
    check_invariants(w)


@pytest.mark.parametrize(
    "target",
    [
        (-1, 40),
        (LAYOUT["navigation"]["width"] + 16, 40),
        (40, LAYOUT["navigation"]["height"] + 16),
        (float("nan"), 40),
        (float("inf"), 40),
    ],
)
def test_path_rejects_out_of_world_target(target):
    with pytest.raises(ValueError):
        route(320, 520, *target)


def test_route_and_motion_exact_arrival():
    target = PLACES["orchard"]
    nodes = route(320, 520, target["x"], target["y"])
    assert all(not blocked(int(n["x"] // 16), int(n["y"] // 16)) for n in nodes)
    a = {"x": 320, "y": 520, "path": nodes}
    while a["path"]:
        advance(a)
    assert (a["x"], a["y"]) == (target["x"], target["y"])


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "[]",
        '{"choices":[]}',
        '{"choices":[{"message":{"content":"[]"}}]}',
        '{"choices":[{"message":{"content":"{}"}}],"usage":{"prompt_tokens":-1}}',
    ],
)
def test_bad_model_response_has_friendly_error(payload):
    with pytest.raises(ValueError, match="模型返回格式不正确"):
        parse_response(payload)
