from .perishables import valid_inventory
from .market_day import is_market_day


def need(condition, message):
    if not condition:
        raise ValueError(message)


def emit(events, w, a, event_type, text, **details):
    if is_market_day(w):
        details["market_day"] = True
    events.append(
        {
            "tick": w["tick"],
            "actor_id": a["id"] if isinstance(a, dict) else a,
            "type": event_type,
            "text": text,
            "details": details,
        }
    )


def capacity(w, a=None):
    from .homes import owned_home
    from ..balance import balance
    home = owned_home(w, a) if a is not None else None
    return (60 if w["project"]["completed"] else 30) + (
        home['level'] * balance.homes.capacity_per_level if home else 0
    )


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
            a["cash"] >= 0 and valid_inventory(a["inventory"]),
            "资产数据错误",
        )
        need(0 <= a["energy"] <= 100 and 0 <= a["hunger"] <= 100, "居民状态错误")
    need(all(n >= 0 for n in w["market"].values()), "市场库存错误")
