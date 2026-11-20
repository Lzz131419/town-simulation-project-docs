from copy import deepcopy
import math
import pytest
from app.catalog import initial_world, ITEMS, PLACES, ACTIONS
from app.world_map import LAYOUT
from app.pathfinding import route, blocked, CELL, advance
from app.domain.actions import execute, start_action
from app.domain.recipes import RECIPES, CONSUMABLES
from app.domain.migration import upgrade_world
from app.domain.rules import check_invariants
from app.domain.scheduler import fallback_action


def test_all_crossings_stay_on_bridges_and_arrive_at_every_new_place():
    for key in ["forest", "orchard", "mine", "fishery", "herb_garden", "meadow"]:
        target = PLACES[key]
        nodes = route(325, 520, target["x"], target["y"])
        assert nodes and not blocked(int(target["x"] // CELL), int(target["y"] // CELL))
        crossings = []
        for p in nodes:
            if LAYOUT["river"]["x"] <= p["x"] < LAYOUT["river"]["x"] + LAYOUT["river"]["width"]:
                crossings.append(p)
                assert any(b["y"] <= p["y"] <= b["y"] + b["h"] for b in LAYOUT["bridges"])
        if key != "meadow":
            assert crossings
        a = {"x": 325, "y": 520, "path": nodes}
        while a["path"]:
            advance(a)
        assert (a["x"], a["y"]) == (target["x"], target["y"])
    assert blocked(58, 25)  # middle of river, away from either bridge
    with pytest.raises(ValueError):
        route(325, 520, 936, 408)


def test_layout_buildings_do_not_overlap_water_or_their_entrances():
    river = LAYOUT["river"]
    for b in LAYOUT["buildings"]:
        assert b["x"] + b["w"] <= river["x"] or b["x"] >= river["x"] + river["width"]
    for p in PLACES.values():
        assert not blocked(int(p["x"] // CELL), int(p["y"] // CELL))


def test_map_upgrade_preserves_assets_plan_and_repaths_active_trip():
    w = initial_world()
    w["map_version"] = 1
    a = w["agents"]["wangjue"]
    a.update(
        x=936,
        y=408,
        task={"type": "gather", "quantity": 1, "automatic": False},
        path=[{"x": 1040, "y": 330}],
        plan=[{"type": "mine"}],
    )
    before = deepcopy(a)
    total = w["economy_total"]
    assert upgrade_world(w)
    assert not blocked(int(a["x"] // CELL), int(a["y"] // CELL))
    assert a["path"][-1] == {"x": PLACES["orchard"]["x"], "y": PLACES["orchard"]["y"]}
    for field in ["inventory", "cash", "energy", "hunger", "plan", "task"]:
        assert a[field] == before[field]
    assert w["economy_total"] == total and not upgrade_world(w)
    check_invariants(w)


@pytest.mark.parametrize("kind", list(RECIPES))
def test_recipes_match_catalog_and_actual_inventory(kind):
    w = initial_world()
    a = w["agents"]["wangjue"]
    a["energy"] = 100
    a["inventory"] = {k: 0 for k in ITEMS}
    a["inventory"].update(RECIPES[kind]["inputs"])
    execute(w, a, {"type": kind}, [])
    assert {k: n for k, n in a["inventory"].items() if n} == RECIPES[kind]["outputs"]
    assert ACTIONS[kind]["outputs"] == RECIPES[kind]["outputs"]
    assert a["energy"] == 100 - ACTIONS[kind]["energy"]
    check_invariants(w)


def test_tool_chain_bonus_and_failed_work_do_not_consume_assets():
    w = initial_world()
    a = w["agents"]["wangjue"]
    a["inventory"] = {k: 0 for k in ITEMS}
    a["inventory"].update(ore=2, wood=2)
    execute(w, a, {"type": "forge"}, [])
    assert a["inventory"]["tool"] == 1 and a["inventory"]["ore"] == 0
    a["energy"] = 0
    before = deepcopy(a)
    with pytest.raises(ValueError):
        execute(w, a, {"type": "mine"}, [])
    assert a == before
    a["energy"] = 100
    execute(w, a, {"type": "mine"}, [])
    assert a["inventory"]["ore"] == 4 and a["inventory"]["tool"] == 0
    # Net-capacity accounting can turn a full bag of inputs into fewer outputs.
    a["inventory"] = {k: 0 for k in ITEMS}
    a["inventory"].update(ore=28, wood=2)
    execute(w, a, {"type": "forge"}, [])
    assert sum(a["inventory"].values()) == 27
    a["inventory"].update(tool=1, ore=29, wood=0)
    before = deepcopy(a)
    with pytest.raises(ValueError):
        execute(w, a, {"type": "mine"}, [])
    assert a == before


@pytest.mark.parametrize("kind", list(CONSUMABLES))
def test_food_tea_and_picnic_have_real_bounded_effects(kind):
    w = initial_world()
    a = w["agents"]["wangjue"]
    a.update(energy=90, hunger=10)
    a["inventory"] = {k: 0 for k in ITEMS}
    a["inventory"].update(CONSUMABLES[kind]["inputs"])
    execute(w, a, {"type": kind}, [])
    assert a["energy"] == min(100, 90 + CONSUMABLES[kind]["energy_gain"])
    assert a["hunger"] == max(0, 10 - CONSUMABLES[kind]["hunger_relief"])
    assert sum(a["inventory"].values()) == 0
    before = deepcopy(a)
    with pytest.raises(ValueError):
        execute(w, a, {"type": kind}, [])
    assert a == before


def test_arrival_required_and_rule_fallback_gathers_missing_ingredients():
    w = initial_world()
    a = w["agents"]["wangjue"]
    events = []
    start_action(w, a, {"type": "gather"}, events)
    assert a["inventory"]["fruit"] == 0 and a["path"] and a["task"]["type"] == "gather"
    a["policy"]["fallback"] = "grill"
    assert fallback_action(w, a)["type"] == "fish"
    a["inventory"]["fish"] = 1
    assert fallback_action(w, a)["type"] == "craft"
    a["inventory"]["wood"] = 1
    assert fallback_action(w, a)["type"] == "grill"
    a["hunger"] = 80
    a["inventory"]["fruit"] = 1
    assert fallback_action(w, a)["type"] == "eat_fruit"


def test_route_preview_is_read_only_and_new_goods_can_be_ordered(auth):
    before = auth.get("/api/world").json()
    result = auth.get("/api/me/route?place=mine")
    assert result.status_code == 200
    points = result.json()["path"]
    x, y = before["world"]["agents"]["wangjue"]["x"], before["world"]["agents"]["wangjue"]["y"]
    distance = 0
    for p in points:
        distance += math.hypot(p["x"] - x, p["y"] - y)
        x, y = p["x"], p["y"]
    assert result.json()["distance"] == round(distance)
    assert auth.get("/api/world").json()["revision"] == before["revision"]
    assert auth.get("/api/me/route?place=unknown").status_code == 400
    for item in ["fruit", "fish", "ore", "herb", "tool"]:
        assert (
            auth.post(
                "/api/orders", json={"item": item, "quantity": 1, "unit_price": 1}
            ).status_code
            == 200
        )
    assert (
        auth.put(
            "/api/me/plan",
            json={"actions": [{"type": "fish"}, {"type": "grill"}, {"type": "eat_meal"}]},
        ).status_code
        == 200
    )
    assert (
        auth.put(
            "/api/me/policy",
            json={"reserve": 20, "daily_budget": 20, "fallback": "forge", "auto_eat": True},
        ).status_code
        == 200
    )


@pytest.mark.asyncio
async def test_client_disconnect_during_close_is_normal(auth, monkeypatch):
    from app.api.realtime import socket, runtime
    from starlette.websockets import WebSocketDisconnect
    from unittest.mock import AsyncMock

    class GoneSocket:
        headers = {"host": "testserver"}
        cookies = {"town_session": auth.cookies.get("town_session")}
        query_params = {"protocol": "2"}

        async def accept(self):
            pass

        async def receive_text(self):
            raise WebSocketDisconnect(1006)

        async def close(self):
            raise WebSocketDisconnect(1006)

    ws = GoneSocket()
    monkeypatch.setattr(runtime, "broadcast", AsyncMock())
    await socket(ws)
    assert ws not in runtime.clients


def test_stop_clears_active_journey_but_preserves_saved_plan(auth):
    from app.database import Session
    from app.models import World
    from copy import deepcopy
    from app.pathfinding import MOVEMENT_PER_TICK

    plan = [{"type": "rest"}, {"type": "farm"}]
    assert auth.put("/api/me/plan", json={"actions": plan}).status_code == 200
    assert auth.post("/api/me/action", json={"type": "move", "place": "mine"}).status_code == 200
    with Session() as db:
        before = deepcopy(db.get(World, 1).data["agents"]["wangjue"])
    assert before["path"] and before["task"]
    assert auth.put("/api/me/control", json={"mode": "manual"}).status_code == 200
    after = auth.get("/api/world").json()["world"]["agents"]["wangjue"]
    assert after["path"] == [] and after["task"] is None
    assert after["activity"] == "等待新安排"
    for key in ("x", "y", "inventory", "cash", "plan", "progress"):
        assert after[key] == before[key]
    assert auth.get("/api/catalog").json()["movement_per_tick"] == MOVEMENT_PER_TICK
