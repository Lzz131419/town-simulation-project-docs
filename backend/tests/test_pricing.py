from copy import deepcopy
from random import Random

import pytest

from app.balance import balance
from app.catalog import ITEMS, initial_world
from app.database import Session
from app.domain.actions import execute
from app.domain.economy import price
from app.domain.scheduler import affordable_sale, can_buy_bread, tick_world
from app.models import WorldSample
from app.services.history import sample_world


@pytest.mark.parametrize("item", ["bread", "wood", "cloth", "furniture"])
@pytest.mark.parametrize("side", ["buy", "sell"])
def test_stock_moves_price_around_base(item, side):
    w = initial_world()
    target = (
        balance.pricing.basic_target_stock
        if item in balance.pricing.basic_items
        else balance.pricing.processed_target_stock
    )
    w["market"][item] = 0
    assert price(w, item, side) > ITEMS[item][side]
    w["market"][item] = target
    assert price(w, item, side) == ITEMS[item][side]
    w["market"][item] = target * 4
    assert price(w, item, side) < ITEMS[item][side]


@pytest.mark.parametrize("item", ITEMS)
def test_prices_are_monotone_and_bounded(item):
    w = initial_world()
    for side in ("buy", "sell"):
        prices = []
        for stock in range(201):
            w["market"][item] = stock
            prices.append(price(w, item, side))
        # Integer rounding creates plateaus, but never reverses the smooth curve.
        assert prices == sorted(prices, reverse=True)
        assert all(0.5 * ITEMS[item][side] <= p <= 1.8 * ITEMS[item][side] for p in prices)
        assert all(a - b <= 2 for a, b in zip(prices, prices[1:]))


def test_spread_for_one_hundred_random_stock_snapshots_and_purity():
    rng = Random(20261121)
    w = initial_world()
    for _ in range(100):
        w["market"] = {item: rng.randint(0, 10000) for item in ITEMS}
        before = deepcopy(w)
        for item in ITEMS:
            if item == "spoiled":
                # Non-purchasable salvage has no buy/sell spread.
                assert price(w, item, "sell") == price(w, item, "buy") == 1
            else:
                assert 1 <= price(w, item, "sell") < price(w, item, "buy")
        assert w == before
    assert "prices" not in w


def test_transactions_charge_live_quote_and_preserve_money_through_tick():
    w, events = initial_world(), []
    a = w["agents"]["wangjue"]
    for side in ("buy", "sell"):
        w["market"]["bread"] = 5 if side == "buy" else 80
        total = price(w, "bread", side) * 2
        before_cash, before_treasury = a["cash"], w["treasury"]
        execute(w, a, {"type": side, "item": "bread", "quantity": 2}, events)
        change = -total if side == "buy" else total
        assert a["cash"] == before_cash + change
        assert w["treasury"] == before_treasury - change
        assert f"{total}镇币" in events[-1]["text"]
        tick_world(w, events)


def test_sale_selection_and_treasury_limit_use_dynamic_value():
    w = initial_world()
    a = w["agents"]["npc-1"]
    a["inventory"] = {item: 0 for item in ITEMS}
    a["inventory"].update(bread=5, wood=5)
    w["market"].update(bread=0, wood=100)
    assert affordable_sale(w, a)["item"] == "bread"
    w["market"].update(bread=100, wood=0)
    w["treasury"] = price(w, "wood", "sell") * 2
    assert affordable_sale(w, a) == {"type": "sell", "item": "wood", "quantity": 2}


def test_automatic_purchase_budget_uses_dynamic_quote():
    w = initial_world()
    a = w["agents"]["wangjue"]
    w["market"]["bread"] = 100
    a["policy"].update(reserve=0, daily_budget=price(w, "bread", "buy"))
    assert can_buy_bread(w, a)
    execute(w, a, {"type": "buy", "item": "bread"}, [], automatic=True)
    assert a["spent_today"] == 3
    a["spent_today"] = 0
    w["market"]["bread"] = 1
    assert not can_buy_bread(w, a)


def test_sample_prices_persist_and_reach_report_series(auth):
    w = initial_world()
    w["tick"] = balance.simulation.sample_interval_ticks
    w["market"]["bread"] = 5
    expected = {item: price(w, item, "buy") for item in ITEMS}
    with Session.begin() as db:
        sample_world(db, w)
    with Session() as db:
        assert db.get(WorldSample, w["tick"]).data["prices"] == expected
    response = auth.get("/api/report")
    assert response.status_code == 200
    sample = next(s for s in response.json()["series"] if s["tick"] == w["tick"])
    assert sample["prices"] == expected
    assert sample["market"] == w["market"]
