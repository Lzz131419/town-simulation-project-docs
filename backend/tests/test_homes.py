from copy import deepcopy
import json
import pytest
from app.catalog import initial_world
from app.balance import balance
from app.domain.homes import new_homes, owned_home, home_destination, claim_home, dawn_meal
from app.domain.actions import start_action, execute
from app.domain.migration import upgrade_world
from app.domain.rules import capacity, check_invariants
from app.domain.scheduler import fallback_action, tick_world
from app.domain.sleep import begin_sleep, advance_sleep
from app.pathfinding import route


def setup():
    w = initial_world()
    for a in w["agents"].values():
        a["mode"] = "manual"
    a = w["agents"]["wangjue"]
    w["treasury"] -= 420
    a["cash"] += 420
    a["inventory"]["wood"] = 45
    return w, a, []


def at_home(w, a, events):
    claim_home(w, a, events)
    t = home_destination(w, a)
    a.update(x=t["x"], y=t["y"])
    return owned_home(w, a)


def test_nearest_claim_unique_and_bench_overflow():
    w, _, events = setup()
    for a in w["agents"].values():
        free = [h for h in w["homes"] if h["owner_id"] is None]
        nearest = (
            min(free, key=lambda h: ((h["x"] - a["x"]) ** 2 + (h["y"] - a["y"]) ** 2, h["id"]))
            if free
            else None
        )
        start_action(w, a, {"type": "rest"}, events)
        assert a["home_id"] == (nearest["id"] if nearest else None)
        target = a["path"][-1]
        a.update(x=target["x"], y=target["y"], energy=0)
        execute(w, a, {"type": "rest"}, events)
        if not nearest:
            assert "长椅" in a["activity"]
            w["tick"] += 1
            advance_sleep(w, a, events)
            assert a["energy"] == balance.sleep.light_gain * balance.homes.bench_sleep_multiplier
    assert len({h["owner_id"] for h in w["homes"]}) == 7
    assert len([e for e in events if e["type"] == "home_claimed"]) == 7
    assert all("南岸安了家" in e["text"] for e in events if e["type"] == "home_claimed")


def test_all_home_doors_reachable_and_own_home_routing():
    w, a, events = setup()
    for home in w["homes"]:
        home["owner_id"], a["home_id"] = a["id"], home["id"]
        t = home_destination(w, a)
        assert route(325, 520, t["x"], t["y"], w)[-1] == {"x": t["x"], "y": t["y"]}
        start_action(w, a, {"type": "upgrade_home"}, events)
        assert a["path"][-1] == {"x": t["x"], "y": t["y"]}
        home["owner_id"] = None


@pytest.mark.parametrize("level,multiplier", [(1, 1), (2, 1.3), (3, 1.6)])
def test_upgrade_cost_capacity_and_sleep_rate(level, multiplier):
    w, a, events = setup()
    home = at_home(w, a, events)
    before_cash, before_wood = a["cash"], a["inventory"]["wood"]
    for _ in range(level - 1):
        execute(w, a, {"type": "upgrade_home"}, events)
    assert home["level"] == level
    assert before_cash - a["cash"] == [0, 60, 210][level - 1]
    assert before_wood - a["inventory"]["wood"] == [0, 15, 45][level - 1]
    assert capacity(w, a) == 30 + level * 10 and capacity(w) == 30
    w["project"]["completed"] = True
    assert capacity(w, a) == 60 + level * 10 and capacity(w) == 60
    a["energy"] = 0
    begin_sleep(w, a, events)
    w["tick"] += 1
    advance_sleep(w, a, events)
    assert a["energy"] == pytest.approx(7 * multiplier)
    check_invariants(w)


@pytest.mark.parametrize("reason", ["unowned", "max", "wood", "cash", "away"])
def test_failed_upgrade_is_atomic(reason):
    w, a, events = setup()
    home = at_home(w, a, events)
    if reason == "unowned":
        home["owner_id"], a["home_id"] = None, None
    if reason == "max":
        home["level"] = 3
    if reason == "wood":
        a["inventory"]["wood"] = 0
    if reason == "cash":
        a["cash"] = 0
    if reason == "away":
        a["x"] = 500
    before = deepcopy(w)
    with pytest.raises(ValueError):
        execute(w, a, {"type": "upgrade_home"}, events)
    assert before == w


def test_level_three_dawn_once_and_hunger_clamp():
    w, a, events = setup()
    home = at_home(w, a, events)
    home["level"] = 3
    # Compare a full world tick against an identical level-two control.
    a["hunger"] = 40
    w["tick"] = 95
    control = deepcopy(w)
    owned_home(control, control["agents"][a["id"]])["level"] = 2
    tick_world(w, events)
    tick_world(control, [])
    assert a["hunger"] == control["agents"][a["id"]]["hunger"] - 5
    tick_world(w, events)
    assert a["hunger"] == control["agents"][a["id"]]["hunger"] - 5
    a["hunger"] = 2
    dawn_meal(w, a)
    assert a["hunger"] == 0


@pytest.mark.parametrize(
    "personality,expected", [("diligent", True), ("generous", True), ("quiet", False)]
)
def test_npc_upgrade_priority_and_memory(personality, expected):
    w, a, events = setup()
    a.update(npc=True, personality=personality, energy=100, hunger=0)
    at_home(w, a, events)
    choice = fallback_action(w, a)
    assert (choice["type"] == "upgrade_home") == expected
    if expected:
        start_action(w, a, choice, events, True)
        execute(w, a, choice, events, True)
        assert any("家升到了 2 级" in m["text"] for m in a["memories"])
        a["cash"] = a["policy"]["reserve"] * 3
        assert fallback_action(w, a)["type"] != "upgrade_home"


def test_migration_idempotent_and_existing_ownership_preserved():
    w, a, events = setup()
    del w["homes"]
    for agent in w["agents"].values():
        agent.pop("home_id")
    assert upgrade_world(w)
    assert w["homes"] == new_homes()
    at_home(w, a, events)["level"] = 3
    before = deepcopy(w)
    assert not upgrade_world(w) and w == before
    assert not upgrade_world(json.loads(json.dumps(w)))


def test_proxy_returns_to_owned_home_and_sleep_survives_json():
    w, a, events = setup()
    at_home(w, a, events)
    a.update(x=325, y=520, energy=10, proxy_life=True, mode="rules")
    w["tick"] = 78
    for _ in range(30):
        tick_world(w, events)
        if a["sleeping"]:
            break
    assert a["sleeping"] and owned_home(w, a)
    t = home_destination(w, a)
    assert (a["x"], a["y"]) == (t["x"], t["y"])
    copy = json.loads(json.dumps(w))
    tick_world(w, [])
    tick_world(copy, [])
    assert copy == w


def test_personal_capacity_applies_to_production_purchase_and_recipient():
    w, a, events = setup()
    at_home(w, a, events)
    a["inventory"] = {k: 0 for k in a["inventory"]}
    a["inventory"]["wood"] = 30
    execute(w, a, {"type": "craft"}, events)
    execute(w, a, {"type": "buy", "item": "wood", "quantity": 1}, events)
    other = w["agents"]["npc-1"]
    other.update(x=a["x"], y=a["y"])
    execute(w, other, {"type": "gift", "target_id": a["id"]}, events)
    from app.domain.perishables import inv_total

    assert 30 < inv_total(a["inventory"]) <= capacity(w, a)
    # Recipient, not giver, determines capacity; the other resident owns no home.
    other["inventory"] = {k: 0 for k in other["inventory"]}
    other["inventory"]["wood"] = 30
    with pytest.raises(ValueError, match="对方背包已满"):
        execute(w, a, {"type": "gift", "target_id": other["id"]}, events)
    check_invariants(w)


def test_order_capacity_uses_home_of_buyer():
    from app.domain.orders import post_order, fill_order

    w, buyer, events = setup()
    at_home(w, buyer, events)
    buyer["inventory"] = {k: 0 for k in buyer["inventory"]}
    buyer["inventory"]["wood"] = 30
    seller = w["agents"]["npc-1"]
    post_order(w, buyer, "wood", 2, 3, events)
    fill_order(w, seller, w["orders"][-1]["id"], events)
    assert buyer["inventory"]["wood"] == 32
    check_invariants(w)
