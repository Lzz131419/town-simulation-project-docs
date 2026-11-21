"""Deterministic close contacts and personality-sensitive relationship gains."""


def close_contacts(w, agent):
    known = [uid for uid in agent["relations"] if uid in w["agents"] and uid != agent["id"]]
    # New residents start with a stable pair until they form explicit relationships.
    candidates = known or [uid for uid in w["agents"] if uid != agent["id"]]
    return sorted(
        candidates,
        key=lambda uid: (
            -agent["relations"].get(uid, 30),
            not w["agents"][uid]["npc"],
            uid,
        ),
    )[:2]


def relationship_gains(w, agent, other):
    if agent.get("personality") == "introvert":
        return (4, 8) if other["id"] in close_contacts(w, agent) else (2, 4)
    if other.get("personality") == "introvert":
        return (8, 4) if agent["id"] in close_contacts(w, other) else (4, 2)
    return 5, 5
