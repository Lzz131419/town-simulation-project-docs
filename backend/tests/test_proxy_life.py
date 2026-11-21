"""Explicit departure, autonomous life and event-based return accounting."""
import asyncio
from copy import deepcopy

import pytest
from sqlalchemy import select

from app.database import Session
from app.domain.rules import check_invariants
from app.domain.scheduler import fallback_action, tick_world
from app.main import runtime
from app.models import Departure, Event, World

UID = "wangjue"


def read_world():
    with Session() as db:
        return deepcopy(db.get(World, 1).data)


def checkpoint():
    with Session() as db:
        return deepcopy(db.get(Departure, UID).checkpoint)


def advance(count):
    async def run():
        for _ in range(count):
            await runtime.mutate(tick_world)
    asyncio.run(run())


def login(client):
    assert client.post("/api/auth/login", json={"username": UID, "password": UID}).status_code == 200


def test_manual_departure_runs_rules_restores_mode_and_conserves_money(auth):
    auth.put("/api/me/control", json={"mode": "manual"})
    before = read_world()
    assert auth.post("/api/auth/logout").status_code == 200
    point = checkpoint()
    assert point["mode_at_departure"] == "manual" and point["tick"] == before["tick"]
    assert read_world()["agents"][UID]["mode"] == "rules"
    advance(180)
    away = read_world()
    assert away["agents"][UID]["completed"] > before["agents"][UID]["completed"]
    check_invariants(away)
    assert away["economy_total"] == before["economy_total"]
    with Session() as db:
        assert db.scalar(select(Event).where(Event.actor_id == UID, Event.type == "levy"))
    login(auth)
    returned = read_world()["agents"][UID]
    assert returned["mode"] == "manual" and not returned.get("proxy_life")
    assert returned["task"] is None and returned["path"] == []
    summary = auth.get("/api/return-summary").json()
    assert summary["away_ticks"] == 180 and summary["completed"] > 0
    assert summary["summary"] == checkpoint()["summary"]
    assert checkpoint()["away"] is False
    advance(10)
    assert read_world()["agents"][UID]["completed"] == returned["completed"]
    assert auth.get("/api/return-summary").json() == summary


@pytest.mark.parametrize("mode", ["manual", "rules", "plan"])
def test_duplicate_departure_and_new_cycle_preserve_original_checkpoint(auth, mode):
    auth.put("/api/me/plan", json={"actions": [{"type": "farm"}]})
    auth.put("/api/me/control", json={"mode": mode})
    auth.post("/api/auth/logout")
    point = checkpoint()
    advance(5)
    asyncio.run(runtime.record_departure(UID))
    assert checkpoint() == point
    login(auth)
    assert read_world()["agents"][UID]["mode"] == mode
    assert auth.get("/api/return-summary").json()["away_ticks"] == 5
    auth.post("/api/auth/logout")
    assert checkpoint()["tick"] == 5 and checkpoint()["mode_at_departure"] == mode


def test_non_departed_manual_player_stays_manual(auth):
    auth.put("/api/me/control", json={"mode": "manual"})
    old = read_world()["agents"][UID]
    advance(40)
    new = read_world()["agents"][UID]
    assert new["mode"] == "manual" and new["completed"] == old["completed"]
    assert new["inventory"] == old["inventory"]
    assert auth.get("/api/return-summary").json() is None


def test_summary_exact_money_items_participation_and_same_tick_boundary(auth):
    def event(kind, details, actor=UID, tick=0):
        return Event(tick=tick, actor_id=actor, type=kind, text=kind, details=details)

    with Session.begin() as db:
        db.add(event("work", {"before": {"cash": 0}, "after": {"cash": 999}}))
    auth.post("/api/auth/logout")
    with Session.begin() as db:
        db.add_all([
            event("farm", {"before": {"inventory": {"grain": 2}},
                           "after": {"inventory": {"grain": 14}}}),
            event("work", {"before": {"cash": 30}, "after": {"cash": 38}}),
            event("buy", {"before": {"cash": 38, "inventory": {"fish": []}},
                          "after": {"cash": 32, "inventory": {"fish": [{"qty": 3, "fresh": 100}]}}}),
            event("levy", {"amount": 2}),
            event("delivery", {"before": {"cash": 32}, "after": {"cash": 44}}),
            event("order", {"buyer": "npc-1", "amount": 5}),
            event("order", {"escrow": 4}),
            event("order", {"refund": 4}),
            event("spoilage", {"quantity": 3, "items": {"fish": 3}}),
            event("feast", {"participants": [UID, "npc-1"]}, "npc-1"),
            event("gift", {"partner_id": UID, "item": "bread", "quantity": 1}, "npc-1"),
            event("order", {"buyer": UID, "item": "wood", "quantity": 2, "amount": 20}, "npc-2"),
            event("feast", {"participants": ["npc-1", "npc-2"]}, "npc-2"),
            event("work", {"before": {"cash": 0}, "after": {"cash": 999}}, "zhangguo"),
        ])
    login(auth)
    result = auth.get("/api/return-summary").json()
    assert result["away_ticks"] == 0
    summary = result["summary"]
    assert summary["earned"] == 29  # 8 work + 12 delivery + 5 order + 4 escrow refund
    assert summary["spent"] == 12  # 6 purchase + 2 levy + 4 escrow
    assert summary["gained_items"] == {"grain": 12, "fish": 3, "bread": 1, "wood": 2}
    assert "你完成了2次交付" in summary["events"]
    assert "参加了广场聚餐" in summary["events"]
    assert "有3份鲜鱼变质了" in summary["events"]
    assert len(summary["events"]) <= 5


def test_socket_disconnect_and_reconnect_restore_without_logging_out(auth):
    auth.put("/api/me/control", json={"mode": "manual"})
    with auth.websocket_connect("/api/ws") as ws:
        assert ws.receive_json()["type"] == "world"
    assert checkpoint()["away"]
    advance(30)
    with auth.websocket_connect("/api/ws") as ws:
        packets = [ws.receive_json() for _ in range(2)]
        summary = next(p["summary"] for p in packets if p["type"] == "return_summary")
        assert summary["away_ticks"] == 30
        assert read_world()["agents"][UID]["mode"] == "manual"
        assert checkpoint()["away"] is False


def test_remaining_socket_prevents_departure(auth):
    auth.put("/api/me/control", json={"mode": "manual"})
    with auth.websocket_connect("/api/ws") as first:
        first.receive_json()
        with auth.websocket_connect("/api/ws") as second:
            second.receive_json()
        with Session() as db:
            assert db.get(Departure, UID) is None
        assert read_world()["agents"][UID]["mode"] == "manual"


def test_proxy_uses_npc_default_schedule_and_weather(auth):
    world = read_world()
    agent = world["agents"][UID]
    agent.update(mode="rules", proxy_life=True, energy=80, hunger=0)
    assert "personality" not in agent
    world["tick"] = 96  # Midnight: NPC/default proxy goes home to rest.
    assert fallback_action(world, agent) == {"type": "rest"}
    world.update(tick=0, weather="storm")
    agent["policy"]["fallback"] = "social"
    assert fallback_action(world, agent)["type"] == "craft"


def test_actual_spoilage_event_retains_food_type(auth):
    def prepare(w, events):
        w["tick"] = 95
        w["agents"][UID]["inventory"]["fish"] = [{"qty": 3, "fresh": 25}]
    asyncio.run(runtime.mutate(prepare))
    auth.post("/api/auth/logout")
    advance(1)
    login(auth)
    assert "有3份鲜鱼变质了" in auth.get("/api/return-summary").json()["summary"]["events"]
