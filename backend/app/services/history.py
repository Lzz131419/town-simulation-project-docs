from sqlalchemy import delete
from ..models import WorldSample
from ..balance import balance


def sample_world(db, w):
    rules = balance.simulation
    if w["tick"] % rules.sample_interval_ticks:
        return
    agents = list(w["agents"].values())
    sample = {
        "treasury": w["treasury"],
        "resident_cash": sum(a["cash"] for a in agents),
        "escrow": sum(o["escrow"] for o in w["orders"] if o["status"] == "open"),
        "market": dict(w["market"]),
        "inventory": {k: sum(a["inventory"].get(k, 0) for a in agents) for k in w["market"]},
        "trades": w["activity_goal"]["trades"],
        "energy": round(sum(a["energy"] for a in agents) / len(agents), 1),
        "hunger": round(sum(a["hunger"] for a in agents) / len(agents), 1),
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
