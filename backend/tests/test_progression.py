from copy import deepcopy
import pytest
from app.catalog import initial_world
from app.domain.actions import execute
from app.domain.orders import post_order, fill_order
from app.domain.rules import check_invariants
from app.domain.progression import MILESTONES


def test_progression_only_success_and_one_badge():
    w = initial_world()
    a = w["agents"]["wangjue"]
    events = []
    before = deepcopy(a["progress"])
    with pytest.raises(ValueError):
        execute(w, a, {"type": "bake"}, events)
    assert a["progress"] == before
    execute(w, a, {"type": "farm"}, events)
    assert a["progress"]["metrics"]["harvested"] == 3
    assert a["progress"]["xp"] == 6 and not a["progress"]["badges"]
    execute(w, a, {"type": "farm"}, events)
    assert a["progress"]["badges"] == ["grower"]
    assert a["progress"]["xp"] == 32
    execute(w, a, {"type": "farm"}, events)
    assert a["progress"]["xp"] == 38
    assert sum(e["type"] == "milestone" for e in events) == 1
    check_invariants(w)


def test_order_progression_cannot_be_duplicated():
    w = initial_world()
    a = w["agents"]["wangjue"]
    b = w["agents"]["zhangguo"]
    b["inventory"]["wood"] = 3
    events = []
    order = post_order(w, a, "wood", 2, 3, events)
    assert not a["progress"]["badges"]
    fill_order(w, b, order["id"], events)
    assert b["progress"]["badges"] == ["partner"]
    assert b["progress"]["xp"] == 32
    before = deepcopy(w)
    with pytest.raises(ValueError):
        fill_order(w, b, order["id"], events)
    assert w == before
    check_invariants(w)


def test_old_agent_compatible_without_inventing_history():
    w = initial_world()
    a = w["agents"]["wangjue"]
    del a["progress"]
    a["completed"] = 500
    execute(w, a, {"type": "farm"}, [])
    assert a["progress"]["xp"] == 6
    assert a["progress"]["metrics"] == {"harvested": 3}


def test_progression_catalog_and_archive_persist(auth):
    catalog = auth.get("/api/catalog").json()
    assert catalog["milestones"] == MILESTONES
    auth.post("/api/me/action", json={"type": "eat"})
    own = auth.get("/api/world").json()["world"]["agents"]["wangjue"]
    assert own["progress"]["metrics"]["eat"] == 1
    aid = auth.post("/api/archives", json={"title": "成长进度"}).json()["id"]
    saved = auth.get(f"/api/archives/{aid}").json()["data"]["world"]["agents"]["wangjue"]
    assert saved["progress"] == own["progress"]
    auth.post("/api/me/action", json={"type": "eat"})
    auth.post(f"/api/archives/{aid}/restore-plan")
    current = auth.get("/api/world").json()["world"]["agents"]["wangjue"]
    assert current["progress"]["metrics"]["eat"] == 2


def test_targeted_social_requires_arrival_and_updates_both_residents():
    from app.domain.actions import start_action
    from app.domain.scheduler import tick_world

    w = initial_world()
    a = w["agents"]["wangjue"]
    b = w["agents"]["zhangguo"]
    events = []
    start_action(w, a, {"type": "social", "target_id": b["id"]}, events)
    assert not a["relations"] and a["path"]
    for _ in range(8):
        tick_world(w, events)
    assert a["relations"][b["id"]] == 35 and b["relations"][a["id"]] == 35
    assert a["progress"]["metrics"]["socials"] == 1
    assert any(e.get("details", {}).get("partner_id") == b["id"] for e in events)
    a["relations"][b["id"]] = 99
    b["relations"][a["id"]] = 100
    execute(w, a, {"type": "social", "target_id": b["id"]}, events)
    assert a["relations"][b["id"]] == b["relations"][a["id"]] == 100
    assert events[-1]["details"]["relationship_change"] == 1


def test_targeted_social_rejects_self_missing_and_departed_neighbor():
    from app.domain.actions import start_action

    w = initial_world()
    a = w["agents"]["wangjue"]
    b = w["agents"]["zhangguo"]
    for target in ["missing", a["id"]]:
        before = deepcopy(w)
        with pytest.raises(ValueError):
            start_action(w, a, {"type": "social", "target_id": target}, [])
        assert w == before
    b["x"], b["y"] = 800, 100
    before = deepcopy(w)
    with pytest.raises(ValueError):
        execute(w, a, {"type": "social", "target_id": b["id"]}, [])
    assert w == before


def test_additive_migration_preserves_existing_world(auth):
    from app.database import Session
    from app.models import World
    from app.main import initialize

    with Session.begin() as db:
        row = db.get(World, 1)
        data = deepcopy(row.data)
        for a in data["agents"].values():
            a.pop("progress")
        data["tick"] = 123
        data["agents"]["wangjue"]["plan"] = [{"type": "farm"}]
        row.data = data
        before = deepcopy(data)
        revision = row.revision
    initialize()
    with Session() as db:
        row = db.get(World, 1)
        after = deepcopy(row.data)
        assert row.revision == revision + 1
        assert all(
            a.pop("progress") == {"xp": 0, "metrics": {}, "badges": []}
            for a in after["agents"].values()
        )
        assert after == before
    initialize()
    with Session() as db:
        assert db.get(World, 1).revision == revision + 1
