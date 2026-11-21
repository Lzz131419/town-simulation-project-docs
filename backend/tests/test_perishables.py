"""Batch inventory, dawn spoilage and economy/consumption integration."""

from copy import deepcopy
import json

import pytest

from app.catalog import ITEMS, initial_world
from app.domain.actions import execute, start_action, validate_action
from app.domain.economy import price
from app.domain.migration import upgrade_world
from app.domain.orders import fill_order, post_order
from app.domain.perishables import (
    PERISHABLES,
    inv_add,
    inv_qty,
    inv_take,
    inv_total,
)
from app.domain.recipes import CONSUMABLES
from app.domain.rules import check_invariants
from app.domain.scheduler import affordable_sale, fallback_action, tick_world


def quiet_world():
    w = initial_world()
    for a in w["agents"].values():
        a["mode"] = "manual"
    return w


def test_batch_add_merges_equal_freshness_and_take_uses_lowest_first():
    inv = {"bread": 3, "grain": 2, "flax": 1}
    inv_add(inv, "fish", 2, fresh=100)
    inv_add(inv, "fish", 3, fresh=25)
    inv_add(inv, "fish", 1, fresh=100)
    assert inv["fish"] == [{"qty": 3, "fresh": 25}, {"qty": 3, "fresh": 100}]
    assert inv_qty(inv, "fish") == 6 and inv_qty(inv, "missing") == 0
    assert inv_total(inv) == 12
    assert inv_take(inv, "fish", 4) == [{"qty": 3, "fresh": 25}, {"qty": 1, "fresh": 100}]
    assert inv["fish"] == [{"qty": 2, "fresh": 100}]
    inv_take(inv, "fish", 2)
    assert inv["fish"] == []
    inv_add(inv, "bread", 2)
    inv_take(inv, "bread", 1)
    assert inv["bread"] == 4 and not PERISHABLES.intersection({"bread", "grain", "flax"})
    before = deepcopy(inv)
    with pytest.raises(ValueError, match="物资不足"):
        inv_take(inv, "bread", 10)
    assert inv == before


def test_legacy_integer_stacks_are_readable_and_convert_on_write():
    inv = {"fish": 3}
    assert inv_qty(inv, "fish") == 3
    assert inv_take(inv, "fish", 1) == [{"qty": 1, "fresh": 100}]
    inv_add(inv, "fish", 1)
    assert inv["fish"] == [{"qty": 3, "fresh": 100}]


def test_dawn_decays_all_food_and_emits_one_summary_per_affected_resident():
    w = quiet_world()
    a = w["agents"]["wangjue"]
    inv_add(a["inventory"], "fish", 2, 75)
    inv_add(a["inventory"], "fish", 3, 25)
    for item in sorted(PERISHABLES - {"fish"}):
        inv_add(a["inventory"], item, 1, 20)
    inv_add(a["inventory"], "spoiled", 1)
    inv_add(a["inventory"], "grain", 2)
    inv_add(a["inventory"], "flax", 2)
    nonperishable = {key: a["inventory"][key] for key in ("bread", "grain", "flax")}
    total = inv_total(a["inventory"])
    w["tick"] = 94
    before = deepcopy(a["inventory"])
    events = []
    tick_world(w, events)
    assert a["inventory"] == before and not any(e["type"] == "spoilage" for e in events)
    tick_world(w, events)
    assert a["inventory"]["fish"] == [{"qty": 2, "fresh": 50}]
    assert a["inventory"]["spoiled"] == 8
    assert inv_total(a["inventory"]) == total
    assert all(a["inventory"][key] == n for key, n in nonperishable.items())
    spoiled = [e for e in events if e["type"] == "spoilage"]
    assert len(spoiled) == 1 and spoiled[0]["actor_id"] == a["id"]
    assert spoiled[0]["text"] == "王崛 的 7 份食物变质了"
    tick_world(w, events)
    assert a["inventory"]["fish"] == [{"qty": 2, "fresh": 50}]
    check_invariants(w)


def test_perishable_sale_rounds_each_unit_and_uses_oldest_batches():
    w = initial_world()
    a = w["agents"]["wangjue"]
    inv_add(a["inventory"], "meal", 3, 100)
    inv_add(a["inventory"], "meal", 2, 25)
    base = price(w, "meal", "sell")
    expected = 2 * max(1, int(base * 0.625)) + base
    before = deepcopy(w)
    execute(w, a, {"type": "sell", "item": "meal", "quantity": 3}, [])
    assert a["cash"] - before["agents"][a["id"]]["cash"] == expected
    assert w["treasury"] == before["treasury"] - expected
    assert w["market"]["meal"] == before["market"]["meal"] + 3
    assert a["inventory"]["meal"] == [{"qty": 2, "fresh": 100}]
    check_invariants(w)


def test_sale_budget_failure_preserves_batches_and_discounted_sale_is_affordable():
    w = initial_world()
    a = w["agents"]["wangjue"]
    a["inventory"] = {}
    inv_add(a["inventory"], "meal", 2, 25)
    a["cash"] += w["treasury"] - 1
    w["treasury"] = 1
    before = deepcopy(w)
    with pytest.raises(ValueError, match="预算不足"):
        execute(w, a, {"type": "sell", "item": "meal"}, [])
    assert w == before
    w["treasury"] = int(price(w, "meal", "sell") * 0.625)
    assert affordable_sale(w, a) == {"type": "sell", "item": "meal", "quantity": 1}


@pytest.mark.parametrize("kind", ["eat_soup", "eat_meal", "eat_fruit", "picnic"])
@pytest.mark.parametrize("fresh", [25, 49, 50, 100])
def test_consumption_effects_halved_strictly_below_50(kind, fresh):
    w = initial_world()
    a = w["agents"]["wangjue"]
    a.update(energy=30, hunger=90)
    effect = CONSUMABLES[kind]
    for item, n in effect["inputs"].items():
        inv_add(a["inventory"], item, n, 100)
        inv_add(a["inventory"], item, n, fresh)
    events = []
    execute(w, a, {"type": kind}, events)
    divisor = 2 if fresh < 50 else 1
    assert a["hunger"] == 90 - effect["hunger_relief"] // divisor
    assert a["energy"] == 30 + effect["energy_gain"] // divisor
    assert ("不太新鲜了" in events[-1]["text"]) == (fresh < 50)
    for item, n in effect["inputs"].items():
        assert a["inventory"][item] == [{"qty": n, "fresh": 100}]
    check_invariants(w)


def test_spoiled_can_be_sold_for_one_but_not_bought_or_eaten():
    w = initial_world()
    a = w["agents"]["wangjue"]
    inv_add(a["inventory"], "spoiled", 2)
    before = deepcopy(w)
    for perform in (execute, start_action):
        with pytest.raises(ValueError, match="没人想买变质食物"):
            perform(w, a, {"type": "buy", "item": "spoiled"}, [])
    with pytest.raises(ValueError, match="变质食物不能食用"):
        validate_action({"type": "eat", "item": "spoiled"})
    assert w == before
    execute(w, a, {"type": "sell", "item": "spoiled", "quantity": 2}, [])
    assert a["cash"] == before["agents"][a["id"]]["cash"] + 2
    assert a["inventory"]["spoiled"] == 0 and w["market"]["spoiled"] == 2
    check_invariants(w)


def test_old_save_migration_is_idempotent_and_does_not_refresh_existing_batches():
    w = initial_world()
    a = w["agents"]["wangjue"]
    for resident in w["agents"].values():
        for item in PERISHABLES:
            resident["inventory"][item] = 0
        resident["inventory"].pop("spoiled")
    a["inventory"]["fish"] = 3
    a["inventory"]["soup"] = [{"qty": 1, "fresh": 25}]
    w["market"].pop("spoiled")
    assert upgrade_world(w)
    assert a["inventory"]["fish"] == [{"qty": 3, "fresh": 100}]
    assert a["inventory"]["fruit"] == [] and a["inventory"]["spoiled"] == 0
    assert a["inventory"]["soup"] == [{"qty": 1, "fresh": 25}]
    before = deepcopy(w)
    assert not upgrade_world(w) and w == before
    assert json.loads(json.dumps(w)) == w
    check_invariants(w)


def test_orders_preserve_freshness_and_take_oldest_first():
    w = initial_world()
    seller, buyer = w["agents"]["wangjue"], w["agents"]["zhangguo"]
    inv_add(seller["inventory"], "fish", 2, 100)
    inv_add(seller["inventory"], "fish", 2, 25)
    inv_add(buyer["inventory"], "fish", 1, 25)
    order = post_order(w, buyer, "fish", 3, 2, [])
    fill_order(w, seller, order["id"], [])
    assert seller["inventory"]["fish"] == [{"qty": 1, "fresh": 100}]
    assert buyer["inventory"]["fish"] == [{"qty": 3, "fresh": 25}, {"qty": 1, "fresh": 100}]
    check_invariants(w)


def test_buy_production_delivery_and_fallback_accept_batch_inventory():
    w = initial_world()
    a = w["agents"]["wangjue"]
    inv_add(a["inventory"], "fish", 1, 25)
    execute(w, a, {"type": "buy", "item": "fish"}, [])
    assert a["inventory"]["fish"] == [{"qty": 1, "fresh": 25}, {"qty": 1, "fresh": 100}]
    inv_add(a["inventory"], "wood", 1)
    execute(w, a, {"type": "grill"}, [])
    assert a["inventory"]["fish"] == [{"qty": 1, "fresh": 100}]
    assert a["inventory"]["meal"] == [{"qty": 1, "fresh": 100}]
    inv_add(a["inventory"], "soup", 2, 25)
    inv_add(a["inventory"], "soup", 1, 100)
    execute(w, a, {"type": "delivery", "item": "soup"}, [])
    assert a["inventory"]["soup"] == [{"qty": 1, "fresh": 100}]
    a["hunger"] = 80
    assert fallback_action(w, a) == {"type": "eat_soup"}
    check_invariants(w)


@pytest.mark.parametrize(
    "invalid",
    [
        [{"qty": -1, "fresh": 50}],
        [{"qty": 1, "fresh": 101}],
        [{"qty": 1, "fresh": -1}],
        [{"qty": 1.5, "fresh": 50}],
        [{"qty": 1}],
    ],
)
def test_invariants_reject_invalid_batches(invalid):
    w = initial_world()
    w["agents"]["wangjue"]["inventory"]["fish"] = invalid
    with pytest.raises(ValueError, match="资产数据错误"):
        check_invariants(w)


def test_json_roundtrip_replays_deterministically_across_dawn():
    w = initial_world()
    w["tick"] = 94
    inv_add(w["agents"]["wangjue"]["inventory"], "fish", 2, 75)
    inv_add(w["agents"]["wangjue"]["inventory"], "fish", 1, 25)
    replay = json.loads(json.dumps(w))
    events, replay_events = [], []
    for _ in range(150):
        tick_world(w, events)
        tick_world(replay, replay_events)
    assert w == replay and events == replay_events
    assert set(w["agents"]["wangjue"]["inventory"]) == set(ITEMS)
    check_invariants(w)
