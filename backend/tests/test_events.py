"""Dawn cards, bridge closure and NPC invitations with persisted money/cooldowns."""

from copy import deepcopy
import json
import pytest
from app.balance import balance
from app.catalog import ITEMS, PLACES, initial_world
from app.domain.actions import execute, start_action
from app.domain.economy import price
from app.domain.fortune import draw_daily_event
from app.domain.initiatives import maybe_feast, npc_initiatives
from app.domain.memories import remember
from app.domain.migration import upgrade_world
from app.domain.orders import cancel_order, fill_order, post_order
from app.domain.perishables import inv_add, inv_qty
from app.domain.rules import check_invariants
from app.domain.scheduler import tick_world
from app.pathfinding import CELL, blocked, route
from app.realtime.protocol import delta, personalize

CARD_SEEDS = {"caravan": 0, "bees": 20, "flood": 1, "dispute": 9, "peaceful": 23}


def quiet_world():
    w = initial_world()
    for a in w["agents"].values():
        a["mode"] = "manual"
    return w


def friends(w, relation=60):
    npc, player = w["agents"]["npc-2"], w["agents"]["wangjue"]
    npc["relations"][player["id"]] = relation
    npc.update(x=360, y=480)
    player.update(x=360, y=480)
    return npc, player


@pytest.mark.parametrize("card,seed", CARD_SEEDS.items())
def test_each_seeded_card_at_dawn_emits_its_effect(card, seed):
    w, events = quiet_world(), []
    w.update(tick=95, rng_seed=seed)
    tick_world(w, events)
    cards = [e for e in events if e["type"] == "fortune"]
    assert len(cards) == 1 and cards[0]["tick"] == 96
    assert cards[0]["details"]["card"] == card
    if card == "caravan":
        assert w["market_modifiers"] == {"tool": 0.8, "cloth": 0.8, "expires_tick": 240}
    elif card == "bees":
        assert w["action_modifiers"] == {"gather_honey": 3, "expires_tick": 240}
        a = w["agents"]["wangjue"]
        execute(w, a, {"type": "gather_honey"}, events)
        assert inv_qty(a["inventory"], "honey") == 6
        assert "今日事件增产" in events[-1]["text"]
    elif card == "flood":
        assert w["bridge_closed_until"] == 120
    elif card == "dispute":
        left, right = [w["agents"][uid] for uid in cards[0]["details"]["participants"]]
        assert left["relations"][right["id"]] == right["relations"][left["id"]] == 10
        assert left["name"] in cards[0]["text"] and right["name"] in cards[0]["text"]
        assert all(a["memories"][-1]["topic"] == "dispute" for a in (left, right))
    else:
        assert w["market_modifiers"] == w["action_modifiers"] == {}
        assert "平静的一天" in cards[0]["text"]
    check_invariants(w)


def test_six_dawns_replay_exactly_after_json_restore():
    w, events = quiet_world(), []
    for _ in range(300):
        tick_world(w, events)
    restored, replay = json.loads(json.dumps(w)), []
    for _ in range(516):
        tick_world(w, events)
        tick_world(restored, replay)
    cards = [e for e in events if e["type"] == "fortune"]
    assert [(e["tick"], e["details"]["card"]) for e in cards] == [
        (96, "flood"),
        (240, "flood"),
        (384, "flood"),
        (528, "dispute"),
        (672, "bees"),
        (816, "caravan"),
    ]
    assert restored == w
    assert replay == [e for e in events if e["tick"] > 300]


def test_dispute_floor_and_priority_gossip_after_later_memories():
    w, events = quiet_world(), []
    for a in w["agents"].values():
        if a["npc"]:
            a["relations"] = {uid: 5 for uid in w["agents"] if uid != a["id"]}
    w["rng_seed"] = CARD_SEEDS["dispute"]
    draw_daily_event(w, events)
    left, right = (w["agents"][uid] for uid in events[-1]["details"]["participants"])
    assert left["relations"][right["id"]] == right["relations"][left["id"]] == 0
    player = w["agents"]["wangjue"]
    for npc in (left, right):
        gossip = npc["memories"][-1]["text"]
        remember(w, npc, "今天买了面包")
        player.update(x=npc["x"], y=npc["y"])
        execute(w, player, {"type": "social", "target_id": npc["id"]}, events)
        assert events[-1]["details"]["gossip"] == gossip


def test_closed_bridge_routes_start_action_atomic_error_and_expiry():
    w, events = quiet_world(), []
    w.update(tick=10, bridge_closed_until=34)
    a, target = w["agents"]["wangjue"], PLACES["orchard"]
    points = route(a["x"], a["y"], PLACES["farm"]["x"], PLACES["farm"]["y"], w)
    assert points and all(
        not blocked(int(p["x"] // CELL), int(p["y"] // CELL), True) for p in points
    )
    before = deepcopy(w)
    for attempt in (
        lambda: route(a["x"], a["y"], target["x"], target["y"], w),
        lambda: start_action(w, a, {"type": "gather"}, events),
    ):
        with pytest.raises(ValueError, match="河水上涨，桥暂时无法通行"):
            attempt()
        assert w == before and events == []
    w["tick"] = 34
    start_action(w, a, {"type": "gather"}, events)
    assert a["path"] and a["task"]["type"] == "gather"


def test_flood_stops_existing_cross_bridge_journey_until_reopening():
    w, events = quiet_world(), []
    a = w["agents"]["wangjue"]
    start_action(w, a, {"type": "gather"}, events)
    w.update(tick=95, rng_seed=CARD_SEEDS["flood"])
    initial = (a["x"], a["y"])
    for _ in range(24):
        tick_world(w, events)
        assert (a["x"], a["y"]) == initial
    assert len([e for e in events if e["type"] == "blocked" and e["actor_id"] == a["id"]]) == 1
    tick_world(w, events)
    assert (a["x"], a["y"]) != initial and w["tick"] == 120


def test_caravan_quotes_pure_discounted_and_clear_next_dawn():
    w = quiet_world()
    w["market"].update(tool=8, cloth=8)
    original = {(i, s): price(w, i, s) for i in ("tool", "cloth") for s in ("buy", "sell")}
    w.update(tick=96, rng_seed=CARD_SEEDS["caravan"])
    draw_daily_event(w, [])
    before = deepcopy(w)
    for (item, side), value in original.items():
        assert price(w, item, side) == int(value * 0.8 + 0.5)
    assert w == before
    w.update(tick=239, rng_seed=CARD_SEEDS["peaceful"])
    tick_world(w, [])
    assert w["market_modifiers"] == w["action_modifiers"] == {}
    for (item, side), value in original.items():
        assert price(w, item, side) == value


def test_expired_modifiers_ignored_without_dawn_cleanup():
    w = quiet_world()
    original = price(w, "tool", "buy")
    w.update(
        tick=144,
        market_modifiers={"tool": 0.8, "expires_tick": 144},
        action_modifiers={"gather_honey": 3, "expires_tick": 144},
    )
    assert price(w, "tool", "buy") == original
    execute(w, w["agents"]["wangjue"], {"type": "gather_honey"}, [])
    assert inv_qty(w["agents"]["wangjue"]["inventory"], "honey") == 2


def test_private_order_threshold_escrow_target_total_reward_and_memories():
    w, events = quiet_world(), []
    npc, player = friends(w, 59)
    npc_initiatives(w, npc, events)
    assert not w["orders"]
    w["tick"] = 6
    npc["relations"][player["id"]] = 60
    w["market"]["fish"] = 0  # sell=3: floor(3*2*1.2)=7, not 2*floor(3*1.2)
    cash = npc["cash"]
    npc_initiatives(w, npc, events)
    order = w["orders"][0]
    assert order["private_to"] == player["id"] and order["buyer_id"] == npc["id"]
    assert order["escrow"] == 7 and order["unit_price"] * order["quantity"] == 7
    assert npc["cash"] == cash - 7 and npc["next_private_order_tick"] == 42
    assert "私人采购" in npc["memories"][-1]["text"]
    assert "私人采购邀请" in player["memories"][-1]["text"]
    assert events[-1]["type"] == "order" and "出7镇币" in events[-1]["text"]
    check_invariants(w)


def test_private_order_cooldown_and_existing_item_orders():
    w, events = quiet_world(), []
    npc, player = friends(w)
    npc_initiatives(w, npc, events)
    first = w["orders"][0]
    for tick in (1, 6, 35):
        w["tick"] = tick
        npc_initiatives(w, npc, events)
        assert len(w["orders"]) == 1
    w["tick"] = 41
    npc_initiatives(w, npc, events)
    assert len(w["orders"]) == 2 and w["orders"][1]["item"] != first["item"]
    assert all(o["private_to"] == player["id"] for o in w["orders"])
    check_invariants(w)


@pytest.mark.parametrize("reason", ["poor", "all_items_ordered", "full_bag"])
def test_private_orders_skip_unfunded_duplicate_or_unreceivable_goods(reason):
    w, events = quiet_world(), []
    npc, player = friends(w)
    if reason == "poor":
        w["treasury"] += npc["cash"]
        npc["cash"] = 0
    elif reason == "full_bag":
        npc["inventory"] = {item: 0 for item in ITEMS}
        npc["inventory"]["wood"] = 30
    else:
        for item in balance.events.order_items:
            post_order(w, player, item, 1, 1, events)
    count, cash = len(w["orders"]), npc["cash"]
    npc_initiatives(w, npc, events)
    assert len(w["orders"]) == count and npc["cash"] == cash
    assert npc["next_private_order_tick"] == 0
    check_invariants(w)


def test_private_order_visibility_in_snapshots_and_delta_without_mutation():
    w = quiet_world()
    npc, player = friends(w)
    old = {"world": deepcopy(w), "events": [], "revision": 0}
    npc_initiatives(w, npc, [])
    snapshot = {"world": w, "events": [], "revision": 1}
    before = deepcopy(snapshot)
    own = personalize(snapshot, player["id"], [])
    foreign = personalize(snapshot, "zhangguo", [])
    assert len(own["world"]["orders"]) == 1 and foreign["world"]["orders"] == []
    assert "orders" not in delta(personalize(old, "zhangguo", []), foreign)["set"]
    assert snapshot == before


def test_only_invited_player_can_fill_and_exact_escrow_is_paid():
    w, events = quiet_world(), []
    npc, player = friends(w)
    npc_initiatives(w, npc, events)
    order = w["orders"][0]
    before = deepcopy(w)
    with pytest.raises(ValueError, match="指定居民"):
        fill_order(w, w["agents"]["zhangguo"], order["id"], events)
    assert w == before
    inv_add(player["inventory"], order["item"], order["quantity"], fresh=75)
    cash, total = player["cash"], order["escrow"]
    fill_order(w, player, order["id"], events)
    assert player["cash"] == cash + total and order["escrow"] == 0
    assert order["status"] == "filled" and order["seller_id"] == player["id"]
    check_invariants(w)


@pytest.mark.parametrize("finish", ["cancel", "expire"])
def test_private_order_refunds_on_cancel_or_expiry(finish):
    w, events = quiet_world(), []
    npc, _ = friends(w)
    original = npc["cash"]
    npc_initiatives(w, npc, events)
    order = w["orders"][0]
    if finish == "cancel":
        cancel_order(w, npc, order["id"], events)
    else:
        w["tick"] = order["expires_tick"] - 1
        tick_world(w, events)
    assert npc["cash"] == original and order["escrow"] == 0
    assert order["status"] == ("cancelled" if finish == "cancel" else "expired")
    check_invariants(w)


def test_gift_threshold_cheapest_food_freshness_memories_and_daily_cooldown():
    w, events = quiet_world(), []
    npc, player = friends(w, 79)
    npc["inventory"] = {item: 0 for item in ITEMS}
    inv_add(npc["inventory"], "fruit", 3, fresh=50)
    inv_add(npc["inventory"], "meal", 2)
    npc_initiatives(w, npc, events)
    assert not [e for e in events if e["type"] == "gift"]
    npc["relations"][player["id"]] = 80
    w["tick"] = 6
    npc_initiatives(w, npc, events)
    gifts = [e for e in events if e["type"] == "gift"]
    assert len(gifts) == 1 and gifts[0]["details"]["item"] == "fruit"
    assert inv_qty(npc["inventory"], "fruit") == 2
    assert player["inventory"]["fruit"] == [{"qty": 1, "fresh": 50}]
    assert "赠送给王崛1个水果" in npc["memories"][-1]["text"]
    assert "收到了陈禾赠送的1个水果" in player["memories"][-1]["text"]
    assert npc["next_gift_tick"] == 150
    npc["next_private_order_tick"] = 10000
    for tick in (7, 12, 144):
        w["tick"] = tick
        npc_initiatives(w, npc, events)
    assert len([e for e in events if e["type"] == "gift"]) == 1
    w["tick"] = 150
    npc_initiatives(w, npc, events)
    assert len([e for e in events if e["type"] == "gift"]) == 2
    check_invariants(w)


@pytest.mark.parametrize("reason", ["far", "full", "no_food"])
def test_gift_unavailable_does_not_consume_cooldown(reason):
    w, events = quiet_world(), []
    npc, player = friends(w, 80)
    if reason == "far":
        player["x"] += 100
    elif reason == "full":
        player["inventory"] = {item: 0 for item in ITEMS}
        player["inventory"]["wood"] = 30
    else:
        npc["inventory"] = {item: 0 for item in ITEMS}
        npc["inventory"]["wood"] = 1
    npc_initiatives(w, npc, events)
    assert not [e for e in events if e["type"] == "gift"]
    assert npc["next_gift_tick"] == 0
    check_invariants(w)


def plaza_world():
    w = quiet_world()
    for a in w["agents"].values():
        a.update(x=PLACES["farm"]["x"], y=PLACES["farm"]["y"])
    for uid in ("npc-1", "npc-2", "wangjue"):
        w["agents"][uid].update(x=PLACES["plaza"]["x"], y=PLACES["plaza"]["y"], hunger=50)
    w["tick"] = 60  # 18:00
    return w


def test_feast_host_hunger_mutual_relationships_memories_and_daily_limit():
    w, events = plaza_world(), []
    host = w["agents"]["npc-2"]
    host["relations"]["zhangguo"] = 90
    player = w["agents"]["wangjue"]
    player.update(hunger=5)
    player["relations"][host["id"]] = 99
    maybe_feast(w, events)
    assert events[-1]["type"] == "feast" and events[-1]["actor_id"] == host["id"]
    participants = events[-1]["details"]["participants"]
    assert participants == ["npc-1", "npc-2", "wangjue"]
    assert player["hunger"] == 0 and host["hunger"] == 30
    for uid in participants:
        a = w["agents"][uid]
        assert a["memories"][-1]["text"].endswith("参加了广场聚餐")
        for other in participants:
            if other != uid:
                expected = 100 if (uid, other) == ("wangjue", "npc-2") else 33
                assert a["relations"][other] == expected
    before = deepcopy(w)
    maybe_feast(w, events)
    assert w == before and len(events) == 1
    w["tick"] += 1
    maybe_feast(w, events)
    assert len(events) == 1
    w["tick"] = 204
    maybe_feast(w, events)
    assert len(events) == 2 and w["feast_day"] == 1
    check_invariants(w)


@pytest.mark.parametrize("reason", ["early", "late", "few", "outside", "no_npc"])
def test_feast_requires_evening_three_nearby_agents_and_npc_host(reason):
    w, events = plaza_world(), []
    if reason == "early":
        w["tick"] = 59
    elif reason == "late":
        w["tick"] = 66
    elif reason in {"few", "outside"}:
        w["agents"]["wangjue"]["x"] += 101
    else:
        for uid in ("npc-1", "npc-2"):
            w["agents"][uid]["npc"] = False
    maybe_feast(w, events)
    assert events == [] and w["feast_day"] == -1


def test_scheduler_runs_npc_invitations_and_evening_feast():
    w, events = plaza_world(), []
    npc, player = friends(w, 80)
    npc.update(mode="rules", x=PLACES["plaza"]["x"], y=PLACES["plaza"]["y"])
    player.update(x=npc["x"], y=npc["y"])
    w["tick"] = 59
    tick_world(w, events)
    assert {"order", "gift", "feast"} <= {e["type"] for e in events}
    assert w["feast_day"] == 0
    check_invariants(w)


def test_old_save_upgrade_additive_and_does_not_reset_event_state():
    w = initial_world()
    keys = ("market_modifiers", "action_modifiers", "bridge_closed_until", "feast_day")
    cooldowns = ("next_private_order_tick", "next_gift_tick", "next_interaction_tick")
    for key in keys:
        del w[key]
    for a in w["agents"].values():
        if a["npc"]:
            for key in cooldowns:
                del a[key]
    assert upgrade_world(w)
    w.update(
        market_modifiers={"cloth": 0.8, "expires_tick": 200}, bridge_closed_until=150, feast_day=3
    )
    w["agents"]["npc-2"]["next_gift_tick"] = 900
    before = deepcopy(w)
    assert not upgrade_world(w) and w == before
    check_invariants(w)


def test_private_order_api_visibility_and_unauthorized_fill(auth):
    import asyncio
    from app.main import runtime

    def create(w, events):
        npc, _ = friends(w)
        npc_initiatives(w, npc, events)

    asyncio.run(runtime.mutate(create))
    order = auth.get("/api/world").json()["world"]["orders"][0]
    assert order["private_to"] == "wangjue"
    assert (
        auth.post(
            "/api/auth/login", json={"username": "zhangguo", "password": "zhangguo"}
        ).status_code
        == 200
    )
    assert auth.get("/api/world").json()["world"]["orders"] == []
    response = auth.post(f"/api/orders/{order['id']}/fill")
    assert response.status_code == 400 and "指定居民" in response.text
