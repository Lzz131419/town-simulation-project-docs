from sqlalchemy import delete
from ..models import WorldSample
from ..balance import balance
from ..catalog import ITEMS
from ..domain.economy import price
from ..domain.perishables import inv_qty


def sample_world(db, w):
    rules = balance.simulation
    if w["tick"] % rules.sample_interval_ticks:
        return
    agents = list(w["agents"].values())
    resident_cash = sum(a["cash"] for a in agents)
    completed = sum(a.get("completed", 0) for a in agents)
    reputation = sum(a.get("reputation", 0) for a in agents)
    sample = {
        "tick": w["tick"],
        "treasury": w["treasury"],
        "resident_cash": resident_cash,
        "cash": resident_cash,
        "completed": completed,
        "resident_completed": completed,
        "reputation": reputation,
        "resident_reputation": reputation,
        "escrow": sum(o["escrow"] for o in w["orders"] if o["status"] == "open"),
        "market": dict(w["market"]),
        "prices": {item: price(w, item, "buy") for item in ITEMS},
        "inventory": {k: sum(inv_qty(a["inventory"], k) for a in agents) for k in w["market"]},
        "trades": w["activity_goal"]["trades"],
        "energy": round(sum(a["energy"] for a in agents) / len(agents), 1),
        "hunger": round(sum(a["hunger"] for a in agents) / len(agents), 1),
        "weather": w.get("weather"),
        "season": w.get("season"),
    }
    row = db.get(WorldSample, w["tick"])
    if row:
        row.data = sample
    else:
        db.add(WorldSample(tick=w["tick"], data=sample))
    db.execute(
        delete(WorldSample).where(
            WorldSample.tick <= w["tick"] - rules.sample_interval_ticks * rules.history_limit
        )
    )
