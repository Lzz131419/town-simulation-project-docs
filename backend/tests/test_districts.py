from copy import deepcopy
import pytest
from app.catalog import initial_world, PLACES
from app.world_map import LAYOUT
from app.pathfinding import route, blocked, CELL
from app.domain.actions import execute, start_action, validate_action
from app.domain.deliveries import REQUESTS, supply_day
from app.domain.scheduler import tick_world, fallback_action
from app.domain.migration import upgrade_world
from app.domain.rules import check_invariants
from app.domain.perishables import inv_qty

NEW_ITEMS = {"vegetable", "honey", "flax", "cloth", "furniture", "soup"}
NEW_PLACES = {
    "garden",
    "apiary",
    "flax_field",
    "loom",
    "carpentry",
    "kitchen",
    "tea_house",
    "depot",
}


def test_expanded_map_all_entrances_reachable_and_bridge_connects_south():
    assert len(PLACES) == 21 and len(LAYOUT["districts"]) == 5
    for p in PLACES.values():
        points = route(325, 520, p["x"], p["y"])
        assert points[-1] == {"x": p["x"], "y": p["y"]}
        assert all(not blocked(int(n["x"] // CELL), int(n["y"] // CELL)) for n in points)
    points = route(744, 856, PLACES["depot"]["x"], PLACES["depot"]["y"])
    assert any(912 <= p["x"] < 960 and 1008 <= p["y"] <= 1056 for p in points)
    for key in NEW_PLACES:
        assert PLACES[key]["district"] in {"south", "craft", "harbor"}
    for a in LAYOUT["buildings"]:
        for b in LAYOUT["buildings"]:
            if a["id"] == b["id"]:
                continue
            assert (
                a["x"] + a["w"] <= b["x"]
                or b["x"] + b["w"] <= a["x"]
                or a["y"] + a["h"] <= b["y"]
                or b["y"] + b["h"] <= a["y"]
            )


def test_v2_migration_adds_empty_goods_without_grants_and_is_idempotent():
    w = initial_world()
    w["map_version"] = 2
    w.pop("supply")
    for a in w["agents"].values():
        a.pop("delivery_log")
        for item in NEW_ITEMS:
            a["inventory"].pop(item)
    for item in NEW_ITEMS:
        w["market"].pop(item)
    a = w["agents"]["wangjue"]
    a.update(x=1480, y=570, plan=[{"type": "farm"}], mode="plan")
    before = deepcopy(w)
    assert upgrade_world(w) and w["map_version"] == 3
    assert not blocked(int(a["x"] // CELL), int(a["y"] // CELL))
    for key, old in before["agents"].items():
        new = w["agents"][key]
        for field in ["cash", "energy", "hunger", "plan", "mode", "progress"]:
            assert new[field] == old[field]
        assert all(new["inventory"][item] == count for item, count in old["inventory"].items())
        assert all(inv_qty(new["inventory"], item) == 0 for item in NEW_ITEMS)
    assert not upgrade_world(w)
    check_invariants(w)


@pytest.mark.parametrize("item", list(REQUESTS))
def test_delivery_transfers_budget_consumes_goods_and_never_repeats_same_day(item):
    w = initial_world()
    a = w["agents"]["wangjue"]
    request = REQUESTS[item]
    a["inventory"].update(request["inputs"])
    before = deepcopy(w)
    execute(w, a, {"type": "delivery", "item": item}, [])
    assert a["cash"] == before["agents"][a["id"]]["cash"] + request["reward"]
    assert w["treasury"] == before["treasury"] - request["reward"]
    assert inv_qty(a["inventory"], item) == 0
    assert a["delivery_log"] == {"day": supply_day(w["tick"]), "items": [item]}
    assert w["supply"]["completed"] == 1
    assert a["progress"]["metrics"]["supply"] == 1 and "partner" not in a["progress"]["badges"]
    check_invariants(w)
    a["inventory"].update(request["inputs"])
    same = deepcopy(w)
    with pytest.raises(ValueError, match="今天已经"):
        execute(w, a, {"type": "delivery", "item": item}, [])
    assert w == same


def test_delivery_daily_limit_reset_and_budget_failure_are_atomic():
    w = initial_world()
    a = w["agents"]["wangjue"]
    for item in ["bread", "honey", "cloth"]:
        a["inventory"].update(REQUESTS[item]["inputs"])
        execute(w, a, {"type": "delivery", "item": item}, [])
    a["inventory"]["furniture"] = 1
    before = deepcopy(w)
    with pytest.raises(ValueError, match="今日已完成3项"):
        execute(w, a, {"type": "delivery", "item": "furniture"}, [])
    assert w == before
    w["tick"] = 96  # midnight at the end of the first simulation day
    execute(w, a, {"type": "delivery", "item": "furniture"}, [])
    assert a["delivery_log"]["items"] == ["furniture"]
    a["inventory"]["bread"] = 3
    a["cash"] += w["treasury"]
    w["treasury"] = 0
    before = deepcopy(w)
    with pytest.raises(ValueError, match="预算不足"):
        execute(w, a, {"type": "delivery", "item": "bread"}, [])
    assert w == before
    check_invariants(w)


def test_supply_cannot_pay_before_arrival_and_missing_goods_do_not_write_log():
    w = initial_world()
    for p in w["agents"].values():
        p["mode"] = "manual"
    a = w["agents"]["wangjue"]
    start_action(w, a, {"type": "delivery", "item": "bread"}, [])
    assert a["path"] and a["cash"] == 80 and w["supply"]["completed"] == 0
    for _ in range(300):
        tick_world(w, [])
        if a["task"] is None:
            break
    assert a["cash"] == 92 and a["inventory"]["bread"] == 0
    before = deepcopy(w)
    with pytest.raises(ValueError, match="物资不足"):
        execute(w, a, {"type": "delivery", "item": "soup"}, [])
    assert w == before
    for action in [
        {"type": "delivery", "item": "ore"},
        {"type": "delivery", "item": "bread", "quantity": 2},
    ]:
        with pytest.raises(ValueError):
            validate_action(action)


def test_nested_furniture_prerequisites_and_new_orders(auth):
    w = initial_world()
    a = w["agents"]["wangjue"]
    a["policy"]["fallback"] = "assemble"
    assert fallback_action(w, a)["type"] == "craft"
    a["inventory"]["wood"] = 3
    assert fallback_action(w, a)["type"] == "harvest_flax"
    a["inventory"]["flax"] = 2
    assert fallback_action(w, a)["type"] == "weave"
    a["inventory"]["cloth"] = 1
    assert fallback_action(w, a)["type"] == "assemble"
    for item in NEW_ITEMS:
        response = auth.post("/api/orders", json={"item": item, "quantity": 1, "unit_price": 1})
        assert response.status_code == 200
        assert auth.post(f"/api/orders/{response.json()['id']}/cancel").status_code == 200
    catalog = auth.get("/api/catalog").json()
    assert len(catalog["items"]) == 16 and catalog["deliveries"] == REQUESTS
    assert (
        auth.post(
            "/api/me/plan/append", json={"actions": [{"type": "delivery", "item": "bread"}]}
        ).status_code
        == 200
    )
