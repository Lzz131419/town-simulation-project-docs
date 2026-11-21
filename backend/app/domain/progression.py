"""Durable personal progression; successful server actions are the only input."""

from .rules import emit
from ..balance import balance
from .market_day import is_market_day

MILESTONES = [
    {
        "id": "grower",
        "name": "第一畦收成",
        "metric": "harvested",
        "target": 6,
        "description": "累计收获6份谷物",
        "action": "farm",
        "place": "farm",
    },
    {
        "id": "baker",
        "name": "面包出炉",
        "metric": "baked",
        "target": 6,
        "description": "累计烘焙6份面包",
        "action": "bake",
        "place": "bakery",
    },
    {
        "id": "merchant",
        "name": "街坊生意",
        "metric": "trades",
        "target": 3,
        "description": "完成3笔集市买卖",
        "action": "buy",
        "place": "market",
    },
    {
        "id": "neighbor",
        "name": "熟悉的面孔",
        "metric": "socials",
        "target": 2,
        "description": "完成2次邻里交流",
        "action": "social",
        "place": "plaza",
    },
    {
        "id": "builder",
        "name": "一起建小镇",
        "metric": "contributed",
        "target": 2,
        "description": "为共享仓库捐建2份木材",
        "action": "contribute",
        "place": "hall",
    },
    {
        "id": "partner",
        "name": "合作伙伴",
        "metric": "deliveries",
        "target": 1,
        "description": "向另一位玩家交付1笔订单",
        "action": "order",
        "place": "market",
    },
]
XP = {
    "supply": 10,
    "harvest_veg": 6,
    "gather_honey": 6,
    "harvest_flax": 6,
    "weave": 9,
    "assemble": 12,
    "cook": 8,
    "gather": 5,
    "fish": 6,
    "chop": 8,
    "mine": 10,
    "forage": 5,
    "grill": 6,
    "forge": 10,
    "farm": 6,
    "craft": 8,
    "bake": 8,
    "work": 5,
    "buy": 6,
    "sell": 6,
    "social": 6,
    "contribute": 5,
    "delivery": 12,
}


def new_progress():
    return {"xp": 0, "metrics": {}, "badges": []}


def record_progress(w, a, kind, events, quantity=1, item=None):
    multiplier = balance.market_day.progress_multiplier if is_market_day(w) else 1
    progress = a.setdefault("progress", new_progress())
    metrics = progress["metrics"]
    metric, amount = {
        "farm": ("harvested", 3),
        "craft": ("crafted", 2),
        "bake": ("baked", 3),
        "buy": ("trades", 1),
        "sell": ("trades", 1),
        "social": ("socials", 1),
        "delivery": ("deliveries", 1),
        "contribute": ("contributed", quantity if item == "wood" else 0),
    }.get(kind, (kind, 1))
    metrics[metric] = metrics.get(metric, 0) + amount * multiplier
    progress["xp"] += XP.get(kind, 0) * multiplier
    for milestone in MILESTONES:
        if (
            milestone["id"] not in progress["badges"]
            and metrics.get(milestone["metric"], 0) >= milestone["target"]
        ):
            progress["badges"].append(milestone["id"])
            progress["xp"] += 20 * multiplier
            emit(
                events,
                w,
                a,
                "milestone",
                f"{a['name']}达成「{milestone['name']}」",
                badge=milestone["id"],
                xp=20 * multiplier,
            )
