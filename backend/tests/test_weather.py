"""Climate transitions, persisted randomness, and observable gameplay effects."""

from copy import deepcopy
import json

import pytest

from app.catalog import ACTIONS, initial_world
from app.domain.actions import execute, start_action
from app.domain.migration import upgrade_world
from app.domain.rules import check_invariants
from app.domain.perishables import inv_qty
from app.domain.scheduler import fallback_action, tick_world


def quiet_world():
    w = initial_world()
    for agent in w["agents"].values():
        agent["mode"] = "manual"
    return w


def test_four_dawns_are_seeded_and_survive_json_restore():
    w = quiet_world()
    w["rng_seed"] = 42
    events = []
    for _ in range(240):
        tick_world(w, events)
    restored = json.loads(json.dumps(w))
    restored_events = []
    for _ in range(360):
        tick_world(w, events)
        tick_world(restored, restored_events)
    weather = [e for e in events if e["type"] == "weather"]
    assert [e["tick"] for e in weather] == [96, 240, 384, 528]
    assert [e["details"]["to"] for e in weather] == ["cloudy", "cloudy", "cloudy", "rain"]
    assert weather[0]["details"] == {"from": "sunny", "to": "cloudy"}
    assert weather[-1]["text"] == "今日天气：雨天"
    seasons = [e for e in events if e["type"] == "season"]
    assert len(seasons) == 1 and seasons[0]["tick"] == 528
    assert seasons[0]["details"] == {"from": "spring", "to": "summer"}
    assert w == restored
    assert restored_events == [e for e in events if e["tick"] > 240]
    check_invariants(w)


def test_seasons_cycle_every_four_dawns():
    w = quiet_world()
    events = []
    for _ in range(2256):
        tick_world(w, events)
    seasons = [e for e in events if e["type"] == "season"]
    assert [e["tick"] for e in seasons] == [528, 1104, 1680, 2256]
    assert [e["details"]["to"] for e in seasons] == ["summer", "autumn", "winter", "spring"]


@pytest.mark.parametrize(
    "kind,item,amount",
    [
        ("farm", "grain", 5),
        ("harvest_veg", "vegetable", 5),
        ("harvest_flax", "flax", 5),
        ("gather", "fruit", 3),
    ],
)
def test_rain_production_and_energy(kind, item, amount):
    w = initial_world()
    w["weather"] = "rain"
    a = w["agents"]["wangjue"]
    before = deepcopy(a)
    events = []
    execute(w, a, {"type": kind}, events)
    assert inv_qty(a["inventory"], item) - inv_qty(before["inventory"], item) == amount
    assert a["energy"] == before["energy"] - ACTIONS[kind]["energy"] - 3
    assert "雨天丰收" in events[-1]["text"]
    check_invariants(w)


@pytest.mark.parametrize("kind", ["farm", "harvest_veg", "harvest_flax", "gather", "gather_honey"])
@pytest.mark.parametrize("perform", [execute, start_action])
def test_winter_farm_rejected_without_mutation(kind, perform):
    w = initial_world()
    w["season"] = "winter"
    before = deepcopy(w)
    events = []
    with pytest.raises(ValueError, match="冬季农场休耕"):
        perform(w, w["agents"]["wangjue"], {"type": kind}, events)
    assert w == before and events == []


@pytest.mark.parametrize(
    "kind,item,amount",
    [
        ("bake", "bread", 3),
        ("craft", "wood", 2),
        ("mine", "ore", 2),
        ("fish", "fish", 1),
    ],
)
def test_winter_other_work_remains_available(kind, item, amount):
    w = initial_world()
    w["season"] = "winter"
    a = w["agents"]["wangjue"]
    a["inventory"]["grain"] = 2
    before = inv_qty(a["inventory"], item)
    execute(w, a, {"type": kind}, [])
    assert inv_qty(a["inventory"], item) == before + amount


@pytest.mark.parametrize(
    "season,gain", [("spring", 3), ("summer", 4), ("autumn", 3), ("winter", 3)]
)
def test_hunger_grows_every_six_ticks(season, gain):
    w = quiet_world()
    w["season"] = season
    a = w["agents"]["wangjue"]
    initial = a["hunger"]
    for _ in range(5):
        tick_world(w, [])
    assert a["hunger"] == initial
    tick_world(w, [])
    assert a["hunger"] == initial + gain


def test_storm_doubles_fish():
    w = initial_world()
    w["weather"] = "storm"
    a = w["agents"]["wangjue"]
    energy = a["energy"]
    execute(w, a, {"type": "fish"}, [])
    assert inv_qty(a["inventory"], "fish") == 2
    assert a["energy"] == energy - ACTIONS["fish"]["energy"]


@pytest.mark.parametrize("weather", ["rain", "storm"])
@pytest.mark.parametrize("npc_id", ["npc-1", "npc-5"])
def test_wet_weather_skips_npc_social_schedule(weather, npc_id):
    w = initial_world()
    w["tick"] = 24  # Noon: inside the social window, with neighbors nearby.
    a = w["agents"][npc_id]
    assert fallback_action(w, a)["type"] == "social"
    w["weather"] = weather
    action = fallback_action(w, a)
    assert action is not None and action["type"] != "social"


@pytest.mark.parametrize(
    "season,kind,item,amount,hint",
    [
        ("summer", "farm", "grain", 7, "夏季丰收"),  # ceil(ceil(3 * 1.5) * 1.3)
        ("autumn", "gather", "fruit", 6, "秋季水果丰收"),
    ],
)
def test_weather_then_season_rounding(season, kind, item, amount, hint):
    w = initial_world()
    w.update(weather="rain", season=season)
    a = w["agents"]["wangjue"]
    events = []
    execute(w, a, {"type": kind}, events)
    assert inv_qty(a["inventory"], item) == amount
    assert "雨天丰收" in events[-1]["text"] and hint in events[-1]["text"]


def test_boosted_yield_respects_capacity_and_energy_atomically():
    w = initial_world()
    w.update(weather="rain", season="summer")
    a = w["agents"]["wangjue"]
    a["inventory"]["wood"] = 23
    before = deepcopy(w)
    with pytest.raises(ValueError, match="背包已满"):
        execute(w, a, {"type": "farm"}, [])
    assert w == before
    a["inventory"]["wood"] = 0
    a["energy"] = ACTIONS["farm"]["energy"]
    before = deepcopy(w)
    with pytest.raises(ValueError, match="精力不足"):
        execute(w, a, {"type": "farm"}, [])
    assert w == before


def test_legacy_world_seed_is_added_without_resetting_existing_seed():
    w = initial_world()
    del w["rng_seed"]
    assert upgrade_world(w)
    assert w["rng_seed"] == 42 and w["schema_version"] == 2
    w["rng_seed"] = 123
    assert not upgrade_world(w)
    assert w["rng_seed"] == 123
