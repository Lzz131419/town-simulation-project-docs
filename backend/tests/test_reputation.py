"""Daily reputation budget, rewards, projections and bounded market discounts."""
from copy import deepcopy
import asyncio
import json
import math

import pytest

from app.catalog import ITEMS, initial_world
from app.domain.actions import buy_price, execute
from app.domain.deliveries import settle_delivery
from app.domain.initiatives import npc_initiatives
from app.domain.migration import upgrade_world
from app.domain.orders import fill_order, post_order
from app.domain.perishables import inv_add
from app.domain.reputation import reputation_title
from app.domain.rules import check_invariants
from app.domain.scheduler import can_buy_bread, tick_world
from app.domain.economy import price
from app.realtime.protocol import delta, personalize


def quiet_world():
    w = initial_world()
    for a in w["agents"].values():
        a.update(mode="manual", x=360, y=480)
    return w


def reps(events):
    return [e for e in events if e["type"] == "reputation"]


def gift(w, a, events):
    execute(w, a, {"type": "gift", "target_id": "zhangguo"}, events)


def order(w, buyer, seller, events, private=True):
    kwargs = {"private_to": seller["id"], "total_reward": 2} if private else {}
    return post_order(w, buyer, "bread", 1, 2, events, **kwargs)


def test_initial_and_successful_delivery_once():
    w, events = quiet_world(), []
    assert all(a["reputation"] == 0 for a in w["agents"].values())
    a = w["agents"]["wangjue"]
    settle_delivery(w, a, "bread", events)
    assert a["reputation"] == 2
    assert reps(events)[0]["details"] == {"delta": 2, "reason": "delivery", "total": 2}
    before = deepcopy(w)
    with pytest.raises(ValueError):
        settle_delivery(w, a, "bread", events)
    assert w == before and len(reps(events)) == 1
    check_invariants(w)


@pytest.mark.parametrize("uid", ["wangjue", "npc-1"])
def test_unified_gift_reward_only_sender(uid):
    w, events = quiet_world(), []
    a = w["agents"][uid]
    gift(w, a, events)
    assert a["reputation"] == 5 and w["agents"]["zhangguo"]["reputation"] == 0
    assert len(reps(events)) == 1
    assert reps(events)[0]["details"] == {"delta": 5, "reason": "gift", "total": 5}
    check_invariants(w)


def test_npc_initiative_gift_does_not_double_reward():
    w, events = quiet_world(), []
    npc = w["agents"]["npc-2"]
    npc["relations"]["wangjue"] = 80
    npc_initiatives(w, npc, events)
    assert npc["reputation"] == 5 and len(reps(events)) == 1


@pytest.mark.parametrize("private", [False, True])
def test_order_fill_rewards_only_private_seller(private):
    w, events = quiet_world(), []
    buyer, seller = w["agents"]["npc-1"], w["agents"]["wangjue"]
    o = order(w, buyer, seller, events, private)
    fill_order(w, seller, o["id"], events)
    assert seller["reputation"] == (3 if private else 0) and buyer["reputation"] == 0
    assert len(reps(events)) == int(private)
    if private:
        assert reps(events)[0]["details"] == {"delta": 3, "reason": "private_order", "total": 3}
    before = deepcopy(w)
    with pytest.raises(ValueError):
        fill_order(w, seller, o["id"], events)
    assert before == w
    check_invariants(w)


@pytest.mark.parametrize("private", [False, True])
def test_expiry_penalizes_only_private_buyer_once(private):
    w, events = quiet_world(), []
    buyer, seller = w["agents"]["npc-1"], w["agents"]["wangjue"]
    cash = buyer["cash"]
    o = order(w, buyer, seller, events, private)
    w["tick"] = o["expires_tick"] - 1
    tick_world(w, events)
    tick_world(w, events)
    assert buyer["reputation"] == (-3 if private else 0)
    assert seller["reputation"] == 0 and buyer["cash"] == cash
    assert len(reps(events)) == int(private)
    if private:
        assert reps(events)[0]["details"] == {"delta": -3, "reason": "private_order_expired", "total": -3}
    check_invariants(w)


def test_mixed_delivery_gifts_cap_and_dawn_reset():
    w, events = quiet_world(), []
    a = w["agents"]["wangjue"]
    inv_add(a["inventory"], "bread", 8)
    execute(w, a, {"type": "delivery", "item": "bread"}, events)
    for _ in range(3):
        gift(w, a, events)
    assert a["reputation"] == a["reputation_changed_today"] == 10
    assert [e["details"]["delta"] for e in reps(events)] == [2, 5, 3]
    w["tick"] = 95
    tick_world(w, events)
    assert a["reputation_changed_today"] == 0 and a["reputation"] == 10
    gift(w, a, events)
    assert a["reputation"] == 15
    check_invariants(w)


def test_losses_share_absolute_budget_and_survive_restore():
    w, events = quiet_world(), []
    buyer, seller = w["agents"]["npc-1"], w["agents"]["wangjue"]
    gift(w, buyer, events)
    for _ in range(3):
        o = order(w, buyer, seller, events)
        o["expires_tick"] = 1
    w = json.loads(json.dumps(w))
    tick_world(w, events)
    buyer = w["agents"]["npc-1"]
    assert buyer["reputation"] == 0 and buyer["reputation_changed_today"] == 10
    assert [e["details"]["delta"] for e in reps(events)] == [5, -3, -2]
    check_invariants(w)


def test_negative_cap_and_expiry_on_dawn_uses_new_budget():
    w, events = quiet_world(), []
    buyer, seller = w["agents"]["npc-1"], w["agents"]["wangjue"]
    gift(w, buyer, events)
    gift(w, buyer, events)
    for _ in range(5):
        o = order(w, buyer, seller, events)
        o["expires_tick"] = 96
    w["tick"] = 95
    tick_world(w, events)
    assert buyer["reputation"] == 0 and buyer["reputation_changed_today"] == 10
    assert [e["details"]["delta"] for e in reps(events)][2:] == [-3, -3, -3, -1]
    check_invariants(w)


@pytest.mark.parametrize("score,title", [(-3, ""), (19, ""), (20, "可靠的"), (49, "可靠的"),
                                         (50, "巧手的"), (99, "巧手的"), (100, "慷慨的")])
def test_title_boundaries_and_pure_projection(score, title):
    w = quiet_world()
    a = w["agents"]["wangjue"]
    a["reputation"] = score
    snapshot = {"world": w, "events": [], "revision": 1}
    before = deepcopy(snapshot)
    assert reputation_title(score) == title
    assert personalize(snapshot, a["id"], [])["world"]["agents"][a["id"]]["title"] == title
    assert snapshot == before and "title" not in a


def test_title_gain_and_loss_in_realtime_delta():
    w = quiet_world()
    a = w["agents"]["wangjue"]
    a["reputation"] = 19
    old = personalize({"world": w, "events": [], "revision": 1}, a["id"], [])
    a["reputation"] = 20
    current = personalize({"world": w, "events": [], "revision": 2}, a["id"], [])
    assert delta(old, current)["agents"][a["id"]]["title"] == "可靠的"
    a["reputation"] = 19
    new = personalize({"world": w, "events": [], "revision": 3}, a["id"], [])
    assert delta(current, new)["agents"][a["id"]]["title"] == ""


@pytest.mark.parametrize("modifier,expected", [(None, (9, 8)), (0.8, (7, 6))])
def test_buy_threshold_and_stacked_rounding(modifier, expected):
    charged = []
    for reputation in (49, 50):
        w, events = quiet_world(), []
        a = w["agents"]["wangjue"]
        a["reputation"] = reputation
        w["market"]["cloth"] = 8
        if modifier:
            w["market_modifiers"] = {"cloth": modifier, "expires_tick": 100}
        cash = a["cash"]
        sell_quote = price(w, "cloth", "sell")
        execute(w, a, {"type": "buy", "item": "cloth", "quantity": 2}, events)
        charged.append((cash - a["cash"]) // 2)
        details = events[-1]["details"]
        assert details["discount"] == (0 if reputation == 49 else 2)
        assert details["quoted_unit_price"] == expected[0]
        assert details["unit_price"] == charged[-1]
        assert sell_quote < charged[-1]
        check_invariants(w)
    assert tuple(charged) == expected


@pytest.mark.parametrize("modifier", [None, 0.8])
def test_discount_all_items_stocks_envelope_spread_no_surcharge(modifier):
    w = quiet_world()
    a = w["agents"]["wangjue"]
    a["reputation"] = 50
    for item in ITEMS:
        if item == "spoiled":
            continue
        for stock in (1, 8, 20, 100, 10000):
            w["market"][item] = stock
            w["market_modifiers"] = ({item: modifier, "expires_tick": 100} if modifier else {})
            before = deepcopy(w)
            unit = buy_price(w, a, item)
            assert w == before
            assert math.ceil(0.5 * ITEMS[item]["buy"]) <= unit <= math.floor(1.8 * ITEMS[item]["buy"])
            assert price(w, item, "sell") < unit <= price(w, item, "buy")
            trade = deepcopy(w)
            execute(trade, trade["agents"][a["id"]], {"type": "buy", "item": item}, [])
            check_invariants(trade)


def test_automatic_budget_uses_discounted_price():
    w = quiet_world()
    a = w["agents"]["wangjue"]
    w["market"]["cloth"] = 8
    a["reputation"] = 50
    discounted = buy_price(w, a, "cloth")
    assert discounted < price(w, "cloth", "buy")
    a["policy"].update(reserve=0, daily_budget=discounted)
    execute(w, a, {"type": "buy", "item": "cloth"}, [], automatic=True)
    assert a["spent_today"] == discounted
    assert not can_buy_bread(w, a)
    a["policy"]["daily_budget"] += buy_price(w, a, "bread")
    assert can_buy_bread(w, a)
    check_invariants(w)


def test_migration_additive_idempotent_preserves_score_budget():
    w = quiet_world()
    for a in w["agents"].values():
        for key in ("reputation", "reputation_day", "reputation_changed_today"):
            del a[key]
    assert upgrade_world(w)
    assert all(a["reputation"] == 0 for a in w["agents"].values())
    w["agents"]["wangjue"].update(reputation=51, reputation_day=0, reputation_changed_today=7)
    before = deepcopy(w)
    assert not upgrade_world(w) and w == before
    assert all("title" not in a for a in w["agents"].values())


def test_world_report_api_and_catalog_expose_reputation(auth):
    from app.main import runtime

    def reward(w, events):
        w["agents"]["wangjue"]["reputation"] = 20

    asyncio.run(runtime.mutate(reward))
    agent = auth.get("/api/world").json()["world"]["agents"]["wangjue"]
    assert agent["reputation"] == 20 and agent["title"] == "可靠的"
    report = auth.get("/api/report").json()
    assert report["me"]["title"] == "可靠的"
    assert next(a for a in report["ranking"] if a["id"] == "wangjue")["title"] == "可靠的"
    assert auth.get("/api/catalog").json()["rules"]["reputation"]["daily_limit"] == 10
