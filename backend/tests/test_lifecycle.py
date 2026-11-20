import asyncio
from copy import deepcopy

import pytest

from app.database import Session
from app.domain.orders import fill_order, post_order
from app.domain.rules import check_invariants
from app.engine import tick_world
from app.main import runtime
from app.models import World


def test_return_summary_tracks_only_departed_players_progress(auth):
    assert auth.get("/api/return-summary").json() is None
    auth.put("/api/me/plan", json={"actions": [{"type": "farm"}]})
    auth.put("/api/me/control", json={"mode": "rules"})
    before = auth.get("/api/world").json()["world"]
    auth.post("/api/auth/logout")

    # Advance the same persisted world while the player's session is absent.
    async def advance():
        for _ in range(40):
            await runtime.mutate(tick_world)

    asyncio.run(advance())
    auth.post("/api/auth/login", json={"username": "wangjue", "password": "wangjue"})
    summary = auth.get("/api/return-summary").json()
    after = auth.get("/api/world").json()["world"]
    me, old = after["agents"]["wangjue"], before["agents"]["wangjue"]
    assert summary["since_tick"] == before["tick"]
    assert summary["current_tick"] == after["tick"]
    assert summary["completed"] == me["completed"] - old["completed"] > 0
    assert summary["cash_change"] == me["cash"] - old["cash"]
    assert summary["recent"] and len(summary["recent"]) <= 8
    auth.post("/api/auth/login", json={"username": "zhangguo", "password": "zhangguo"})
    assert auth.get("/api/return-summary").json() is None


@pytest.mark.asyncio
async def test_concurrent_delivery_has_one_winner_and_one_payment(auth):
    def prepare(w, events):
        for uid in ["zhangguo", "lizhanbo"]:
            w["agents"][uid]["inventory"]["wood"] = 3
        return deepcopy(post_order(w, w["agents"]["wangjue"], "wood", 3, 5, events))

    order = await runtime.mutate(prepare)

    async def deliver(uid):
        return await runtime.mutate(
            lambda w, events: fill_order(w, w["agents"][uid], order["id"], events)
        )

    results = await asyncio.gather(deliver("zhangguo"), deliver("lizhanbo"), return_exceptions=True)
    assert sum(isinstance(r, ValueError) for r in results) == 1
    with Session() as db:
        w = db.get(World, 1).data
        check_invariants(w)
        assert w["orders"][0]["status"] == "filled" and w["orders"][0]["escrow"] == 0
        assert w["agents"]["wangjue"]["inventory"]["wood"] == 3
        assert sum(w["agents"][uid]["cash"] for uid in ["zhangguo", "lizhanbo"]) == 175
