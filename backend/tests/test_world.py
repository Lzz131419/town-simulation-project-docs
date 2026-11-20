from copy import deepcopy
import pytest
from app.catalog import initial_world, PLACES
from app.engine import *
from app.pathfinding import route, blocked, CELL
from app.main import runtime
from app.db import Session, World


@pytest.mark.parametrize(
    "uid", ["zhangguo", "wangjue", "lizhanbo", "sunxiang", "qianjunhao", "yaofuen"]
)
def test_member_login(client, uid):
    r = client.post("/api/auth/login", json={"username": uid, "password": uid})
    assert r.status_code == 200 and r.json()["id"] == uid
    assert "password" not in r.text
    w = client.get("/api/world").json()["world"]
    assert len(w["agents"]) == 12


def test_authentication_and_ownership(auth):
    assert (
        auth.post("/api/me/action", json={"type": "work", "actor_id": "zhangguo"}).status_code
        == 422
    )
    data = auth.get("/api/world").json()["world"]
    assert "policy" in data["agents"]["wangjue"] and "policy" not in data["agents"]["zhangguo"]
    assert auth.post("/api/auth/logout").status_code == 200
    assert auth.get("/api/world").status_code == 401


def test_wrong_password(client):
    assert (
        client.post(
            "/api/auth/login", json={"username": "wangjue", "password": "wrong"}
        ).status_code
        == 401
    )


def test_manual_and_rule_execution():
    w = initial_world()
    a = w["agents"]["wangjue"]
    events = []
    start_action(w, a, {"type": "farm"}, events)
    # No yield before arriving.
    assert a["inventory"]["grain"] == 0
    for _ in range(30):
        tick_world(w, events)
    assert a["inventory"]["grain"] == 3 and not a["task"]
    before = a["completed"]
    for _ in range(15):
        tick_world(w, events)
    assert a["completed"] == before
    a["mode"] = "rules"
    a["plan"] = [{"type": "craft"}]
    for _ in range(60):
        tick_world(w, events)
    assert a["inventory"]["wood"] >= 2 and a["completed"] > before


def test_plan_policy_and_session_persistence(auth):
    assert (
        auth.put("/api/me/plan", json={"actions": [{"type": "farm"}, {"type": "bake"}]}).status_code
        == 200
    )
    assert auth.put("/api/me/control", json={"mode": "rules"}).status_code == 200
    assert auth.post("/api/auth/logout").status_code == 200
    with Session() as db:
        stored = deepcopy(db.get(World, 1).data)
    assert stored["agents"]["wangjue"]["mode"] == "rules"
    events = []
    for _ in range(40):
        tick_world(stored, events)
    assert stored["agents"]["wangjue"]["completed"] >= 2
    # Fresh DB session sees a persisted plan, not a browser-local copy.
    with Session() as db:
        assert db.get(World, 1).data["agents"]["wangjue"]["plan"][0]["type"] == "farm"


def test_atomic_rejection(auth):
    before = auth.get("/api/world").json()
    assert auth.post("/api/me/action", json={"type": "nonexistent"}).status_code == 400
    after = auth.get("/api/world").json()
    assert before == after


def test_policy_budget_and_bag_limits():
    w = initial_world()
    a = w["agents"]["wangjue"]
    events = []
    a["policy"]["reserve"] = 79
    with pytest.raises(ValueError):
        execute(w, a, {"type": "buy", "item": "bread", "quantity": 1}, events, True)
    assert a["cash"] == 80
    a["policy"]["reserve"] = 0
    a["policy"]["daily_budget"] = 3
    with pytest.raises(ValueError):
        execute(w, a, {"type": "buy", "item": "bread", "quantity": 1}, events, True)
    a["inventory"]["wood"] = 30
    with pytest.raises(ValueError):
        execute(w, a, {"type": "craft"}, events)


def test_long_world_money_and_bounds():
    w = initial_world()
    events = []
    for a in w["agents"].values():
        a["mode"] = "rules"
    for _ in range(600):
        tick_world(w, events)
    check_invariants(w)
    assert w["tick"] == 600 and any(e["type"] == "work" for e in events)


def test_orders_escrow_delivery_duplicate_and_cancel():
    w = initial_world()
    events = []
    buyer = w["agents"]["wangjue"]
    seller = w["agents"]["zhangguo"]
    seller["inventory"]["wood"] = 5
    o = post_order(w, buyer, "wood", 3, 5, events)
    assert buyer["cash"] == 65 and o["escrow"] == 15
    check_invariants(w)
    fill_order(w, seller, o["id"], events)
    assert seller["cash"] == 95 and buyer["inventory"]["wood"] == 3 and o["escrow"] == 0
    before = deepcopy(w)
    with pytest.raises(ValueError):
        fill_order(w, seller, o["id"], events)
    assert w == before
    check_invariants(w)
    o = post_order(w, buyer, "wood", 1, 5, events)
    cancel_order(w, buyer, o["id"], events)
    assert buyer["cash"] == 65
    o = post_order(w, buyer, "wood", 1, 5, events)
    w["tick"] = o["expires_tick"] - 1
    tick_world(w, events)
    assert o["status"] == "expired" and buyer["cash"] == 65


def test_api_order_requires_owner(auth):
    o = auth.post("/api/orders", json={"item": "wood", "quantity": 2, "unit_price": 3}).json()
    auth.post("/api/auth/login", json={"username": "zhangguo", "password": "zhangguo"})
    assert auth.post(f"/api/orders/{o['id']}/cancel").status_code == 400
    assert auth.post(f"/api/orders/{o['id']}/fill").status_code == 400


def test_cloud_archive_ownership_and_safe_restore(auth):
    auth.put("/api/me/plan", json={"actions": [{"type": "farm"}]})
    aid = auth.post("/api/archives", json={"title": "开店前的计划"}).json()["id"]
    auth.put("/api/me/plan", json={"actions": []})
    cash = auth.get("/api/world").json()["world"]["agents"]["wangjue"]["cash"]
    assert auth.post(f"/api/archives/{aid}/restore-plan").status_code == 200
    own = auth.get("/api/world").json()["world"]["agents"]["wangjue"]
    assert own["cash"] == cash and own["plan"][0]["type"] == "farm"
    auth.post("/api/auth/login", json={"username": "zhangguo", "password": "zhangguo"})
    assert auth.get(f"/api/archives/{aid}").status_code == 404
    assert auth.post(f"/api/archives/{aid}/restore-plan").status_code == 404


def test_private_messages(auth):
    assert (
        auth.post(
            "/api/messages", json={"recipient_id": "zhangguo", "text": "一起开店吧"}
        ).status_code
        == 200
    )
    assert len(auth.get("/api/messages").json()) == 1
    auth.post("/api/auth/login", json={"username": "lizhanbo", "password": "lizhanbo"})
    assert auth.get("/api/messages").json() == []


def test_shared_websocket_world_and_logout(auth):
    token = auth.cookies.get("town_session")
    with auth.websocket_connect("/api/ws", headers={"cookie": "town_session=" + token}) as ws:
        state = ws.receive_json()
        assert state["world"]["agents"]["wangjue"]["online"]
        ws.receive_json()
        assert auth.post("/api/me/action", json={"type": "eat"}).status_code == 200
        update = ws.receive_json()
        assert update["revision"] > state["revision"]
        assert update["world"]["agents"]["wangjue"]["inventory"]["bread"] == 2
        assert auth.post("/api/auth/logout").status_code == 200
        assert not runtime.online("wangjue")


def test_paths_avoid_buildings():
    for source in PLACES.values():
        for destination in PLACES.values():
            nodes = route(source["x"], source["y"], destination["x"], destination["y"])
            assert nodes
            assert all(not blocked(int(n["x"] // CELL), int(n["y"] // CELL)) for n in nodes)


def test_warehouse_unlock():
    w = initial_world()
    a = w["agents"]["wangjue"]
    events = []
    # Funding is held in the public treasury; no money is invented.
    for _ in range(4):
        a["inventory"]["wood"] = 10
        execute(w, a, {"type": "contribute", "item": "wood", "quantity": 10}, events)
    for donor in list(w["agents"].values())[:5]:
        for _ in range(8):
            execute(w, donor, {"type": "contribute", "item": "cash", "quantity": 10}, events)
    assert w["project"]["completed"] and capacity(w) == 60
    check_invariants(w)
