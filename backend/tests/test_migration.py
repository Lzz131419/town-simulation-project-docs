"""Old saved worlds must recover through both direct ticks and runtime transactions."""

from copy import deepcopy

import pytest

from app.balance import balance
from app.catalog import ACTIONS, ITEMS, NPC_PERSONALITIES, initial_world
from app.database import Session
from app.domain.migration import upgrade_world
from app.domain.perishables import PERISHABLES, inv_qty
from app.domain.rules import check_invariants
from app.domain.scheduler import tick_world
from app.domain.weather import action_available, advance_climate, energy_cost, production_outputs
from app.models import World
from app.runtime import TownRuntime


WORLD_FIELDS = (
    "season", "weather", "rng_seed", "market_modifiers", "action_modifiers",
    "bridge_closed_until", "feast_day", "supply", "map_version",
)
AGENT_FIELDS = (
    "personality", "memories", "reputation", "reputation_day", "reputation_changed_today",
    "next_private_order_tick", "next_gift_tick", "next_interaction_tick",
    "delivery_log", "progress",
)
OLD_ITEMS = {"grain", "bread", "wood", "fruit", "fish", "ore", "herb"}


def legacy_world():
    w = initial_world()
    for key in WORLD_FIELDS:
        w.pop(key)
    for a in w["agents"].values():
        for key in AGENT_FIELDS:
            a.pop(key, None)
        # Old saves stored food as integers, and lacked the later catalog items.
        a["inventory"] = {item: inv_qty(a["inventory"], item) for item in OLD_ITEMS}
    w["market"] = {item: qty for item, qty in w["market"].items() if item in OLD_ITEMS}
    w["agents"]["wangjue"]["inventory"]["fish"] = 2
    return w


def assert_current(w):
    assert set(initial_world()) <= w.keys()
    assert set(ITEMS) <= w["market"].keys()
    for uid, a in w["agents"].items():
        assert set(initial_world()["agents"][uid]) <= a.keys()
        assert set(ITEMS) <= a["inventory"].keys()
        assert all(isinstance(a["inventory"][item], list) for item in PERISHABLES)
        if a["npc"]:
            assert a["personality"] == NPC_PERSONALITIES[uid]
    check_invariants(w)


def test_legacy_defaults_preserve_assets_and_are_idempotent():
    w = legacy_world()
    old = deepcopy(w)
    assert upgrade_world(w)
    defaults = initial_world()
    for key in WORLD_FIELDS:
        assert w[key] == defaults[key]
    for uid, a in w["agents"].items():
        assert a["cash"] == old["agents"][uid]["cash"]
        for item, qty in old["agents"][uid]["inventory"].items():
            assert inv_qty(a["inventory"], item) == qty
    assert w["agents"]["wangjue"]["inventory"]["fish"] == [{"qty": 2, "fresh": 100}]
    assert w["tick"] == old["tick"] and w["economy_total"] == old["economy_total"]
    assert_current(w)
    before = deepcopy(w)
    assert not upgrade_world(w)
    assert w == before


def test_bare_legacy_world_survives_200_ticks():
    w, events = legacy_world(), []
    for _ in range(200):
        tick_world(w, events)
    assert w["tick"] == 200
    assert_current(w)
    assert any(e["type"] == "weather" for e in events)  # Crossed dawn, not only fallback.
    assert w["rng_seed"] != initial_world()["rng_seed"]
    before = deepcopy(w)
    assert not upgrade_world(w) and w == before


def test_weather_helpers_accept_missing_climate_without_migration():
    w, current = legacy_world(), initial_world()
    for kind, action in ACTIONS.items():
        assert action_available(w, kind) == action_available(current, kind)
        assert energy_cost(w, kind, action["energy"]) == energy_cost(current, kind, action["energy"])
        assert production_outputs(w, kind, {"grain": 3}) == production_outputs(current, kind, {"grain": 3})
    # Include the seasonal boundary to exercise both climate reads and event payloads.
    w["tick"] = current["tick"] = (
        balance.weather.ticks_per_day * balance.season.days_per_season
        - balance.weather.dawn_offset_ticks
    )
    events, expected = [], []
    assert advance_climate(w, events) == advance_climate(current, expected)
    assert events == expected
    for key in ("weather", "season", "rng_seed"):
        assert w[key] == current[key]


@pytest.mark.asyncio
async def test_runtime_upgrades_legacy_save_before_callback_and_persists_tick(client):
    with Session.begin() as db:
        row = db.get(World, 1)
        row.data = legacy_world()
        revision = row.revision

    def tick_after_upgrade(w, events):
        assert_current(w)  # Runtime must upgrade before handing off to the callback.
        tick_world(w, events)
        return w["tick"]

    rt = TownRuntime()
    assert await rt.mutate(tick_after_upgrade) == 1
    with Session() as db:
        row = db.get(World, 1)
        assert row.revision == revision + 1
        assert row.data["tick"] == 1
        assert_current(row.data)
