def need(condition, message):
    if not condition:
        raise ValueError(message)


def emit(events, w, a, kind, text, **details):
    events.append(
        {
            "tick": w["tick"],
            "actor_id": a["id"] if isinstance(a, dict) else a,
            "type": kind,
            "text": text,
            "details": details,
        }
    )


def capacity(w):
    return 60 if w["project"]["completed"] else 30


def check_invariants(w):
    money = (
        w["treasury"]
        + sum(a["cash"] for a in w["agents"].values())
        + sum(o["escrow"] for o in w["orders"] if o["status"] == "open")
    )
    need(money == w["economy_total"], "资金总量不一致")
    need(w["treasury"] >= 0, "公库不足")
    for a in w["agents"].values():
        need(
            a["cash"] >= 0 and all(isinstance(n, int) and n >= 0 for n in a["inventory"].values()),
            "资产数据错误",
        )
        need(0 <= a["energy"] <= 100 and 0 <= a["hunger"] <= 100, "居民状态错误")
    need(all(n >= 0 for n in w["market"].values()), "市场库存错误")
