from copy import deepcopy
import pytest
from app.balance import balance
from app.domain.homes import home_destination
from app.catalog import ACTIONS, initial_world
from app.domain.actions import execute, start_action
from app.domain.initiatives import npc_initiatives
from app.domain.migration import upgrade_world
from app.domain.scheduler import fallback_action, social_neighbor, tick_world
from app.domain.sleep import action_energy_cost, advance_sleep, begin_sleep


def quiet_world(tick=78):
    w = initial_world()
    w["tick"] = tick
    for a in w["agents"].values():
        a["mode"] = "manual"
    a = w["agents"]["wangjue"]
    a.update(**{k: v for k, v in home_destination(w, a).items() if k in ("x", "y")}, energy=0)
    return w, a, []


def test_home_arrival_light_deep_and_natural_wake():
    w, a, events = quiet_world()
    a["x"] -= 80
    start_action(w, a, {"type": "rest"}, events)
    assert not a["sleeping"]
    for _ in range(20):
        tick_world(w, events)
        if a["sleeping"]:
            break
    assert a["sleeping"] == {"since_tick": w["tick"], "phase": "light"}
    assert (a["x"], a["y"]) == (home_destination(w, a)["x"], home_destination(w, a)["y"])
    for i in range(12):
        tick_world(w, events)
        assert a["energy"] == (i + 1) * balance.sleep.light_gain
    assert a["sleeping"]["phase"] == "deep"
    tick_world(w, events)
    assert a["energy"] == 12 * balance.sleep.light_gain + balance.sleep.deep_gain
    tick_world(w, events)
    assert a["sleeping"] is None
    assert [e["type"] for e in events if e["actor_id"] == a["id"]] == [
        "home_claimed",
        "sleep",
        "rest",
        "sleep_phase",
        "wake",
    ]
    assert balance.sleep.light_gain > balance.needs.rest_gain / 4


def test_two_days_deprivation_cap_cost_food_and_sufficient_recovery():
    w, a, events = quiet_world(0)
    a["energy"] = 100
    for _ in range(287):
        tick_world(w, events)
    assert a["fatigue"] == 0
    tick_world(w, events)
    assert a["fatigue"] == 1 and a["energy"] == 80
    w["weather"] = "rain"
    assert action_energy_cost(w, a, "farm", ACTIONS["farm"]["energy"]) == 9 + 3 + 2
    execute(w, a, {"type": "farm"}, events)
    assert a["energy"] == 66
    a["energy"] = 79
    a["inventory"]["herb"] = 2
    execute(w, a, {"type": "brew"}, events)
    assert a["energy"] == 78
    a["energy"] = 0
    a.update(**{k: v for k, v in home_destination(w, a).items() if k in ("x", "y")})
    execute(w, a, {"type": "rest"}, events)
    for _ in range(29):
        tick_world(w, events)
    assert a["fatigue"] == 1 and a["energy"] == 80 and a["sleeping"]
    tick_world(w, events)
    assert a["fatigue"] == 0 and a["energy"] == 90
    tick_world(w, events)
    assert a["sleeping"] is None and a["energy"] == 100
    assert any(e["type"] == "fatigue_recovered" for e in events)


def test_rolling_history_boundary_and_old_archive_grace():
    w, a, events = quiet_world(1000)
    for person in w["agents"].values():
        for key in ("sleeping", "fatigue", "sleep_history", "sleep_tracking_since"):
            person.pop(key)
    assert upgrade_world(w)
    assert a["sleep_tracking_since"] == 1000 and a["sleeping"] is None
    before = deepcopy(w)
    assert not upgrade_world(w)
    assert w == before
    a["sleep_history"] = list(range(1001, 1025))
    w["tick"] = 1288
    advance_sleep(w, a, events)
    assert not a["fatigue"]
    w["tick"] += 1
    advance_sleep(w, a, events)
    assert a["fatigue"] == 1


@pytest.mark.parametrize("kind", ["gift", "social"])
def test_targeted_interaction_wakes_and_loses_relationship(kind):
    w, target, events = quiet_world()
    actor = w["agents"]["npc-3"]
    actor.update(x=target["x"], y=target["y"])
    begin_sleep(w, target, events)
    execute(w, actor, {"type": kind, "target_id": target["id"]}, events)
    assert target["sleeping"] is None
    assert actor["relations"][target["id"]] == 29
    assert target["relations"][actor["id"]] == 29
    assert any("被吵醒了" in e["text"] and e["details"]["reason"] == "disturbed" for e in events)


def test_sleep_blocks_decisions_and_direct_actions_preserving_plan():
    w, a, events = quiet_world()
    a.update(mode="plan", plan=[{"type": "work"}])
    begin_sleep(w, a, events)
    tick_world(w, events)
    assert a["plan"] == [{"type": "work"}] and a["task"] is None
    for fn in (execute, start_action):
        before = deepcopy(a)
        with pytest.raises(ValueError, match="正在睡觉"):
            fn(w, a, {"type": "eat"}, events)
        assert a == before


def test_initiatives_and_social_skip_sleeping_targets():
    w, target, events = quiet_world()
    npc = w["agents"]["npc-3"]
    npc.update(x=target["x"], y=target["y"])
    for a in w["agents"].values():
        if not a["npc"]:
            a.update(x=target["x"], y=target["y"])
            a.update(**{k: v for k, v in home_destination(w, a).items() if k in ("x", "y")})
            begin_sleep(w, a, events)
            npc["relations"][a["id"]] = 90
    npc_initiatives(w, npc, events)
    assert not w["orders"]
    assert not any(e["type"] in ("gift", "wake") for e in events)
    choice = social_neighbor(w, npc)
    assert choice is None or not w["agents"][choice["target_id"]]["sleeping"]


@pytest.mark.parametrize("tick, reason", [(131, "morning"), (78, "maximum_duration")])
def test_other_natural_wake_limits(tick, reason):
    w, a, events = quiet_world(tick)
    a["fatigue"] = 1
    begin_sleep(w, a, events)
    if reason == "maximum_duration":
        a["sleeping"]["since_tick"] = tick - 35
    tick_world(w, events)
    assert a["sleeping"] is None
    assert next(e for e in events if e["type"] == "wake")["details"]["reason"] == reason


def test_personality_bedtimes_and_diligent_full_energy():
    w, _, events = quiet_world(66)
    introvert, diligent, sociable = [w["agents"][uid] for uid in ("npc-1", "npc-2", "npc-5")]
    assert fallback_action(w, introvert) == {"type": "rest"}
    assert fallback_action(w, diligent) != {"type": "rest"}
    w["tick"] = 78
    assert fallback_action(w, diligent) == {"type": "rest"}
    assert fallback_action(w, sociable) != {"type": "rest"}
    w["tick"] = 84
    assert fallback_action(w, sociable) == {"type": "rest"}
    diligent.update(**{k: v for k, v in home_destination(w, diligent).items() if k in ("x", "y")}, energy=88)
    begin_sleep(w, diligent, events)
    tick_world(w, events)
    assert diligent["energy"] == 95 and diligent["sleeping"]
    tick_world(w, events)
    assert diligent["energy"] == 100 and not diligent["sleeping"]


def test_proxy_night_fallback_reaches_sleep():
    w, a, events = quiet_world()
    a.update(mode="rules", proxy_life=True, energy=50)
    tick_world(w, events)
    assert a["task"]["type"] == "rest"
    tick_world(w, events)
    assert a["sleeping"] and a["activity"] == "在家浅睡"


def test_low_energy_fatigue_cannot_softlock_on_food_or_npc_gifts():
    w, a, events = quiet_world(0)
    a.update(energy=0, hunger=90, fatigue=1)
    assert fallback_action(w, a) == {"type": "rest"}
    assert action_energy_cost(w, a, "rest", 0) == 2
    npc = w["agents"]["npc-3"]
    npc.update(energy=0, fatigue=1, x=a["x"], y=a["y"])
    npc["relations"][a["id"]] = 90
    npc_initiatives(w, npc, events)
    assert not any(e["type"] == "gift" for e in events)


def test_sleep_save_restore_is_deterministic_and_plan_finishes_after_waking():
    import json

    w, a, events = quiet_world()
    a.update(mode="plan", plan=[{"type": "rest"}])
    for _ in range(6):
        tick_world(w, events)
    assert a["sleeping"] and a["mode"] == "plan"
    restored = json.loads(json.dumps(w))
    replay, later = [], []
    for _ in range(15):
        tick_world(w, later)
        tick_world(restored, replay)
    assert restored == w and replay == later
    assert a["mode"] == "manual" and not a["sleeping"]
    own = [e["type"] for e in later if e["actor_id"] == a["id"]]
    assert own.index("wake") < own.index("plan_done")


def test_sociable_extension_and_feast_market_hours_stay_awake():
    w, _, _ = quiet_world(39)  # 14:30: extended social period
    sociable, neighbor = w["agents"]["npc-5"], w["agents"]["npc-6"]
    sociable["policy"]["fallback"] = "work"
    sociable.update(x=neighbor["x"], y=neighbor["y"])
    assert fallback_action(w, sociable)["type"] == "social"
    # Standard social and feast hours occur before every configured bedtime.
    from app.domain.sleep import at_bedtime

    for tick in (24, 30, 60, 65):
        w["tick"] = tick
        assert all(not at_bedtime(w, a) for a in w["agents"].values())


def test_sleep_projection_and_api_action_rejection_preserve_persisted_state(auth):
    import asyncio
    from app.main import runtime

    def fall_asleep(w, events):
        a = w["agents"]["wangjue"]
        a.update(**{k: v for k, v in home_destination(w, a).items() if k in ("x", "y")}, energy=0)
        begin_sleep(w, a, events)

    asyncio.run(runtime.mutate(fall_asleep))
    before = auth.get("/api/world").json()["world"]["agents"]["wangjue"]
    assert before["sleeping"]["phase"] == "light"
    assert auth.post("/api/me/action", json={"type": "work"}).status_code == 400
    assert auth.get("/api/world").json()["world"]["agents"]["wangjue"] == before
