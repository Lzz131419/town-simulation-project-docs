"""Versioned, explicit deltas. Baselines are per connection, never per user."""

from copy import deepcopy
from ..domain.reputation import reputation_title


def personalize(snapshot, uid, online):
    packet = deepcopy(snapshot)
    packet["world"]["orders"] = [
        order for order in packet["world"].get("orders", [])
        if order.get("private_to") in (None, uid)
    ]
    for key, agent in packet["world"]["agents"].items():
        agent["online"] = key in online
        agent["title"] = reputation_title(agent.get("reputation", 0))
        if key != uid:
            for field in ("plan", "policy", "spent_today"):
                agent.pop(field, None)
    return packet


def delta(previous, current):
    old, new = previous["world"], current["world"]
    agents = new["agents"]
    last_event = max((e["id"] for e in previous["events"]), default=0)
    return {
        "type": "patch",
        "base_revision": previous["revision"],
        "revision": current["revision"],
        "set": {k: v for k, v in new.items() if k != "agents" and old.get(k) != v},
        "agents": {k: v for k, v in agents.items() if old["agents"].get(k) != v},
        "removed_agents": [k for k in old["agents"] if k not in agents],
        "events": [e for e in current["events"] if e["id"] > last_event],
    }
