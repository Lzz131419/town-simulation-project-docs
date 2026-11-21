from copy import deepcopy

import pytest

from app.balance import balance
from app.catalog import ITEMS, NPC_PERSONALITIES, initial_world
from app.domain.actions import execute, start_action, validate_action
from app.domain.memories import remember
from app.domain.migration import upgrade_world
from app.domain.orders import fill_order, post_order
from app.domain.recipes import RECIPES
from app.domain.rules import capacity, check_invariants
from app.domain.scheduler import fallback_action, tick_world


def nearby(w, *uids):
    for uid in uids:
        w["agents"][uid].update(x=360, y=480)


def test_personalities_and_memories_are_additive_for_existing_saves():
    w = initial_world()
    assert {uid: w["agents"][uid]["personality"] for uid in NPC_PERSONALITIES} == NPC_PERSONALITIES
    assert all(a["memories"] == [] for a in w["agents"].values())
    for a in w["agents"].values():
        a.pop("memories")
        a.pop("personality", None)
    before = deepcopy(w)
    assert upgrade_world(w)
    assert not upgrade_world(w)
    for uid, a in w["agents"].items():
        assert a["memories"] == []
        if a["npc"]:
            assert a["personality"] == NPC_PERSONALITIES[uid]
        assert {k: v for k, v in a.items() if k not in {"personality", "memories"}} == before[
            "agents"
        ][uid]
    check_invariants(w)


def test_diligent_selects_highest_feasible_output_value_and_rests_below_40():
    w = initial_world()
    a = w["agents"]["npc-2"]
    # With every recipe's inputs available, furniture has the highest sale value.
    a["inventory"] = {item: 0 for item in ITEMS}
    for recipe in RECIPES.values():
        for item, n in recipe["inputs"].items():
            a["inventory"][item] = max(a["inventory"][item], n)
    values = {
        kind: sum(n * ITEMS[item]["sell"] for item, n in r["outputs"].items())
        for kind, r in RECIPES.items()
    }
    for tick in (0, 24, 54):  # morning, social hour, evening; nights now sleep (T12)
        w["tick"] = tick
        action = fallback_action(w, a)
        assert action["type"] == "assemble"
        assert values[action["type"]] == max(values.values())
    a["inventory"] = {item: 0 for item in ITEMS}
    a["energy"] = 40
    assert fallback_action(w, a)["type"] == "mine"
    a["energy"] = 39
    assert fallback_action(w, a) == {"type": "rest"}


def test_merchant_sells_highest_price_item_from_1400():
    w = initial_world()
    a = w["agents"]["npc-3"]
    a["inventory"].update(furniture=1, bread=12)
    w["tick"] = 35
    assert fallback_action(w, a)["type"] != "sell"
    w["tick"] = 36
    action = fallback_action(w, a)
    assert action == {"type": "sell", "item": "furniture", "quantity": 1}
    execute(w, a, action, [])
    assert a["inventory"]["furniture"] == 0
    check_invariants(w)


def test_generous_gift_transfers_one_bread_and_records_both_memories():
    w = initial_world()
    a, other = w["agents"]["npc-4"], w["agents"]["wangjue"]
    nearby(w, a["id"], other["id"])
    w["treasury"] += other["cash"] - 19
    other["cash"] = 19
    action = fallback_action(w, a)
    assert action == {"type": "gift", "target_id": other["id"]}
    events = []
    execute(w, a, action, events)
    assert a["inventory"]["bread"] == 2 and other["inventory"]["bread"] == 4
    assert events[-1]["type"] == "gift"
    assert "赠送给王崛1个面包" in a["memories"][-1]["text"]
    assert "收到了许宁赠送的1个面包" in other["memories"][-1]["text"]
    check_invariants(w)


def test_generous_donation_respects_remaining_target_and_automatic_budget():
    w = initial_world()
    a = w["agents"]["npc-4"]
    a["spent_today"] = a["policy"]["daily_budget"] - 2
    w["project"]["cash"] = w["project"]["cash_target"] - 1
    action = fallback_action(w, a)
    assert action == {"type": "contribute", "item": "cash", "quantity": 1}
    execute(w, a, action, [], automatic=True)
    assert w["project"]["cash"] == w["project"]["cash_target"]
    assert fallback_action(w, a) == {"type": "contribute", "item": "wood", "quantity": 2}
    w["project"]["completed"] = True
    assert fallback_action(w, a)["type"] != "contribute"
    check_invariants(w)


@pytest.mark.parametrize("problem", ["empty", "full", "departed", "self", "missing"])
def test_gift_failures_leave_world_unchanged(problem):
    w = initial_world()
    a, other = w["agents"]["npc-4"], w["agents"]["wangjue"]
    nearby(w, a["id"], other["id"])
    action = {"type": "gift", "target_id": other["id"]}
    if problem == "empty":
        a["inventory"]["bread"] = 0
    elif problem == "full":
        other["inventory"] = {item: 0 for item in ITEMS}
        other["inventory"]["bread"] = capacity(w)
    elif problem == "departed":
        other["x"] = 800
    else:
        action["target_id"] = a["id"] if problem == "self" else "missing"
    before, events = deepcopy(w), []
    with pytest.raises(ValueError):
        execute(w, a, action, events)
    assert w == before and events == []
    check_invariants(w)


def test_gift_validation_and_arrival():
    for action in [{"type": "gift"}, {"type": "gift", "target_id": "npc-1", "quantity": 2}]:
        with pytest.raises(ValueError):
            validate_action(action)
    w = initial_world()
    for a in w["agents"].values():
        a["mode"] = "manual"
    a, other = w["agents"]["npc-4"], w["agents"]["wangjue"]
    start_action(w, a, {"type": "gift", "target_id": other["id"]}, [])
    assert a["path"] and other["inventory"]["bread"] == 3
    events = []
    for _ in range(100):
        tick_world(w, events)
        if a["task"] is None:
            break
    assert a["task"] is None and other["inventory"]["bread"] == 4
    assert any(e["type"] == "gift" for e in events)


def test_introvert_only_selects_top_two_contacts_and_deepens_ties_asymmetrically():
    w = initial_world()
    a = w["agents"]["npc-1"]
    a["relations"] = {"npc-2": 60, "npc-3": 50, "wangjue": 30}
    nearby(w, a["id"], "npc-2", "npc-3", "wangjue")
    selected = set()
    for tick in range(24, 36):
        w["tick"] = tick
        selected.add(fallback_action(w, a)["target_id"])
    assert selected == {"npc-2", "npc-3"}
    execute(w, a, {"type": "social", "target_id": "npc-2"}, [])
    assert a["relations"]["npc-2"] == 64
    assert w["agents"]["npc-2"]["relations"][a["id"]] == 38
    execute(w, a, {"type": "social", "target_id": "wangjue"}, [])
    assert a["relations"]["wangjue"] == 32
    assert w["agents"]["wangjue"]["relations"][a["id"]] == 34
    for uid in ("npc-2", "npc-3"):
        w["agents"][uid]["x"] = 800
    assert fallback_action(w, a) is None


@pytest.mark.parametrize("uid", ["npc-5", "npc-6"])
def test_sociable_and_quiet_keep_default_behavior(uid):
    w = initial_world()
    a = w["agents"][uid]
    default = deepcopy(a)
    default.pop("personality")
    for tick in (0, 24, 36, 84):
        w["tick"] = tick
        assert fallback_action(w, a) == fallback_action(w, default)


def test_memory_fifo_keeps_ten_latest_entries_and_dates():
    w = initial_world()
    a = w["agents"]["npc-1"]
    for i in range(12):
        w["tick"] = 144 + i
        remember(w, a, f"故事{i}")
    assert len(a["memories"]) == 10
    assert a["memories"][0] == {"tick": 146, "text": "第2天，故事2"}
    assert a["memories"][-1] == {"tick": 155, "text": "第2天，故事11"}


def test_social_gossip_uses_previous_memory_and_records_both_agents():
    w = initial_world()
    a, npc = w["agents"]["wangjue"], w["agents"]["npc-1"]
    nearby(w, a["id"], npc["id"])
    remember(w, npc, "完成了街坊早餐交付")
    prior = npc["memories"][-1]["text"]
    events = []
    execute(w, a, {"type": "social", "target_id": npc["id"]}, events)
    assert f"林溪说：“{prior}”" in events[-1]["text"]
    assert events[-1]["details"]["gossip"] == prior
    assert a["memories"][-1]["text"] == "第1天，与林溪交谈"
    assert npc["memories"][-1]["text"] == "第1天，与王崛交谈"


@pytest.mark.parametrize("tick", [0, 1, 2])
def test_social_without_memories_rotates_configured_small_talk(tick):
    w = initial_world()
    w["tick"] = tick
    a, npc = w["agents"]["wangjue"], w["agents"]["npc-3"]
    nearby(w, a["id"], npc["id"])
    events = []
    execute(w, a, {"type": "social", "target_id": npc["id"]}, events)
    assert "说：" in events[-1]["text"]
    assert events[-1]["details"]["gossip"] == balance.npc.small_talk[tick]


def test_order_and_delivery_record_memories_but_market_trades_do_not():
    w = initial_world()
    w["tick"] = 144
    npc, player = w["agents"]["npc-1"], w["agents"]["wangjue"]
    events = []
    order = post_order(w, player, "bread", 2, 4, events)
    fill_order(w, npc, order["id"], events)
    assert npc["memories"][-1] == {"tick": 144, "text": "第2天，向王崛出售了2个面包"}
    assert player["memories"][-1]["text"] == "第2天，向林溪购买了2个面包"
    before = deepcopy(w)
    with pytest.raises(ValueError):
        fill_order(w, npc, order["id"], events)
    assert w == before
    execute(w, player, {"type": "delivery", "item": "bread"}, events)
    assert player["memories"][-1]["text"] == "第2天，完成了街坊早餐交付"
    previous = deepcopy(player["memories"])
    execute(w, player, {"type": "buy", "item": "bread"}, events)
    execute(w, player, {"type": "sell", "item": "bread"}, events)
    assert player["memories"] == previous
    check_invariants(w)


def test_memories_and_personality_survive_persistence_and_world_projection(auth):
    import asyncio
    from app.main import runtime

    def interact(w, events):
        npc, player = w["agents"]["npc-1"], w["agents"]["wangjue"]
        nearby(w, npc["id"], player["id"])
        execute(w, player, {"type": "social", "target_id": npc["id"]}, events)
        order = post_order(w, player, "bread", 2, 4, events)
        fill_order(w, npc, order["id"], events)

    asyncio.run(runtime.mutate(interact))
    response = auth.get("/api/world")
    assert response.status_code == 200
    agents = response.json()["world"]["agents"]
    assert agents["npc-1"]["personality"] == "introvert"
    assert [m["text"] for m in agents["npc-1"]["memories"]] == [
        "第1天，与王崛交谈",
        "第1天，向王崛出售了2个面包",
    ]
    assert agents["wangjue"]["memories"][-1]["text"] == "第1天，向林溪购买了2个面包"
