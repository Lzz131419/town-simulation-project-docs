"""Storm-triggered cooperative flood response."""

from copy import deepcopy

from app.catalog import initial_world
from app.domain.actions import execute
from app.domain.fortune import settle_flood, start_flood_effort
from app.domain.migration import upgrade_world
from app.domain.perishables import inv_add, inv_qty
from app.domain.scheduler import fallback_action, tick_world


def world():
    w = initial_world()
    for agent in w["agents"].values():
        agent["mode"] = "manual"
    return w


def test_storm_dawn_warning_contribute_and_success_records_social_state():
    w, events = world(), []
    # Seed 33 makes the sunny climate transition into storm at tick 96.
    w.update(tick=95, rng_seed=33)
    tick_world(w, events)
    effort = w["flood_effort"]
    assert effort and effort["goal"] == 30 and effort["deadline_tick"] == 108
    assert any(e["type"] == "flood" and e["details"]["phase"] == "warning" for e in events)

    left, right = w["agents"]["wangjue"], w["agents"]["npc-4"]
    for agent in (left, right):
        agent["energy"] = 100
        agent["inventory"]["wood"] = 40
    for _ in range(14):
        execute(w, left, {"type": "reinforce"}, events)
    execute(w, right, {"type": "reinforce"}, events)
    assert effort["donated"] == 30
    w["tick"] = effort["deadline_tick"]
    settle_flood(w, events)
    assert effort["outcome"] == "success"
    assert left["relations"][right["id"]] == right["relations"][left["id"]] == 40
    assert left["reputation"] == right["reputation"] == 5
    assert any("参加了防洪筑堤" in memory["text"] for memory in right["memories"])
    assert any(e["type"] == "flood" and e["details"].get("outcome") == "success" for e in events)


def test_failed_flood_doubles_bridge_closure_and_loses_market_goods():
    w, events = world(), []
    w.update(tick=96, market={**initial_world()["market"], "wood": 100})
    start_flood_effort(w, events)
    participant = w["agents"]["wangjue"]
    participant["energy"] = 100
    participant["inventory"]["wood"] = 3
    execute(w, participant, {"type": "reinforce"}, events)
    w["tick"] = w["flood_effort"]["deadline_tick"]
    before = w["market"]["wood"]
    settle_flood(w, events)
    assert w["flood_effort"]["outcome"] == "failed"
    assert w["bridge_closed_until"] == 156
    assert w["market"][w["flood_effort"]["lost_item"]] <= before
    assert participant["reputation"] == 2
    assert "洪水冲走了集市的部分货物" in events[-1]["text"]


def test_reinforce_consumes_two_wood_and_respects_batch_inventory_helpers():
    w, events = world(), []
    w["tick"] = 20
    start_flood_effort(w, events)
    agent = w["agents"]["wangjue"]
    inv_add(agent["inventory"], "fish", 2, fresh=40)
    agent["inventory"]["wood"] = 4
    agent["energy"] = 100
    execute(w, agent, {"type": "reinforce"}, events)
    assert agent["inventory"]["wood"] == 2
    assert inv_qty(agent["inventory"], "fish") == 2
    assert w["flood_effort"]["donated"] == 2


def test_generous_npc_fallback_prefers_reinforcement():
    w = world()
    w["tick"] = 20
    start_flood_effort(w, [])
    npc = w["agents"]["npc-4"]
    npc["energy"] = 80
    npc["inventory"]["wood"] = 6
    assert fallback_action(w, npc) == {"type": "reinforce"}


def test_old_save_without_flood_effort_upgrades_idempotently():
    w = world()
    w.pop("flood_effort")
    assert upgrade_world(w)
    assert w["flood_effort"] is None
    before = deepcopy(w)
    assert not upgrade_world(w)
    assert w == before
