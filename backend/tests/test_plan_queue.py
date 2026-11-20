from copy import deepcopy
import pytest
from app.catalog import initial_world
from app.domain.plans import append_plan, edit_plan
from app.domain.scheduler import tick_world
from app.domain.rules import check_invariants


def quiet_world():
    world = initial_world()
    for agent in world["agents"].values():
        agent["mode"] = "manual"
    return world, world["agents"]["wangjue"]


def run_until_stopped(w, a, events):
    for _ in range(500):
        tick_world(w, events)
        if a["mode"] == "manual":
            return
    pytest.fail("finite plan did not stop")


def test_append_preserves_active_task_and_eight_step_limit():
    _, a = quiet_world()
    a.update(task={"type": "farm"}, path=[{"x": 5, "y": 5}])
    append_plan(a, [{"type": "bake"}] * 8)
    before = deepcopy(a)
    with pytest.raises(ValueError, match="计划已满"):
        append_plan(a, [{"type": "rest"}])
    assert a == before
    assert a["task"] == {"type": "farm"} and a["mode"] == "manual"
    with pytest.raises(ValueError):
        append_plan(a, [])


def test_stale_edit_cannot_reintroduce_executed_or_new_steps():
    _, a = quiet_world()
    append_plan(a, [{"type": "farm"}, {"type": "bake"}])
    before = deepcopy(a["plan"])
    a["plan"].pop(0)
    with pytest.raises(ValueError, match="计划已变化"):
        edit_plan(a, before, list(reversed(before)))
    assert a["plan"] == before[1:]
    edit_plan(a, [{"type": "bake"}], [{"type": "rest"}, {"type": "bake"}])
    assert [step["type"] for step in a["plan"]] == ["rest", "bake"]


def test_finite_production_chain_stops_without_fallback():
    w, a = quiet_world()
    a["mode"] = "plan"
    append_plan(a, [{"type": "farm"}, {"type": "bake"}, {"type": "eat"}])
    events = []
    run_until_stopped(w, a, events)
    assert [e["type"] for e in events if e["actor_id"] == a["id"]] == [
        "farm", "bake", "eat", "plan_done"
    ]
    assert a["inventory"]["grain"] == 1 and a["inventory"]["bread"] == 5
    assert a["completed"] == 3 and a["activity"] == "本轮计划已完成"
    before = deepcopy(a["inventory"])
    for _ in range(30):
        tick_world(w, events)
    assert a["inventory"] == before and a["completed"] == 3
    assert sum(e["type"] == "plan_done" for e in events) == 1
    check_invariants(w)


@pytest.mark.parametrize("actions", [
    [{"type": "bake"}, {"type": "farm"}],
    [{"type": "eat_fruit"}, {"type": "rest"}],
    [{"type": "social", "target_id": "missing"}, {"type": "rest"}],
])
def test_failure_pauses_later_steps_without_consuming_resources(actions):
    w, a = quiet_world()
    a["mode"] = "plan"
    append_plan(a, actions)
    before = deepcopy(a["inventory"])
    events = []
    run_until_stopped(w, a, events)
    assert a["activity"] == "计划已暂停"
    assert a["plan"][0]["type"] == actions[1]["type"]
    assert a["inventory"] == before and a["completed"] == 0
    assert a["task"] is None and not a["path"]
    assert any(e["type"] == "plan_paused" for e in events)


def test_empty_plan_never_runs_fallback_and_rules_still_do():
    w, a = quiet_world()
    a["mode"] = "plan"
    events = []
    tick_world(w, events)
    assert a["mode"] == "manual" and a["completed"] == 0
    a["mode"] = "rules"
    tick_world(w, events)
    assert a["task"]["type"] == "work" and a["mode"] == "rules"


def test_queue_api_ownership_limits_and_conflict(auth):
    assert auth.put("/api/me/control", json={"mode": "plan"}).status_code == 400
    before = auth.get("/api/world").json()["world"]["agents"]["zhangguo"]
    for action in ["farm", "bake"]:
        assert auth.post("/api/me/plan/append", json={"actions": [{"type": action}]}).status_code == 200
    assert auth.post("/api/me/plan/edit", json={
        "expected": [], "actions": []
    }).status_code == 400
    assert auth.post("/api/me/plan/append", json={"actions": [{"type": "rest"}] * 7}).status_code == 400
    assert auth.post("/api/me/plan/append", json={"actions": [{"type": "unsupported"}]}).status_code == 400
    assert auth.post("/api/me/plan/edit", json={
        "expected": [{"type": "farm"}, {"type": "bake"}],
        "actions": [{"type": "bake"}, {"type": "farm"}],
    }).status_code == 200
    state = auth.get("/api/world").json()["world"]
    assert state["agents"]["zhangguo"] == before
    assert [x["type"] for x in state["agents"]["wangjue"]["plan"]] == ["bake", "farm"]


def test_offline_plan_runs_to_completion_without_model_calls(auth, monkeypatch):
    from app.database import Session
    from app.models import World, ModelCall
    from app.services.container import planner
    from sqlalchemy import select, func

    async def forbidden(*args, **kwargs):
        pytest.fail("offline finite plan must never call a model")
    monkeypatch.setattr(planner, "run", forbidden)
    auth.post("/api/me/plan/append", json={"actions": [{"type": "farm"}, {"type": "bake"}]})
    assert auth.put("/api/me/control", json={"mode": "plan"}).status_code == 200
    auth.post("/api/auth/logout")
    with Session.begin() as db:
        row = db.get(World, 1)
        w = deepcopy(row.data)
        a = w["agents"]["wangjue"]
        run_until_stopped(w, a, [])
        row.data = w
        assert a["completed"] == 2 and a["plan"] == []
        assert db.scalar(select(func.count()).select_from(ModelCall)) == 0
    auth.post("/api/auth/login", json={"username": "wangjue", "password": "wangjue"})
    assert auth.get("/api/world").json()["world"]["agents"]["wangjue"]["mode"] == "manual"
