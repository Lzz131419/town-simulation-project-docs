"""Community supply requests: real goods are consumed, treasury funds are transferred."""

from .rules import need
from .market_day import is_market_day
from .perishables import inv_qty, inv_take
from .reputation import change_reputation
from ..balance import balance

REQUESTS = {
    "bread": {"name": "街坊早餐", "inputs": {"bread": 3}, "reward": 12},
    "vegetable": {"name": "厨房补给", "inputs": {"vegetable": 3}, "reward": 9},
    "honey": {"name": "茶舍备货", "inputs": {"honey": 2}, "reward": 10},
    "cloth": {"name": "街区布置", "inputs": {"cloth": 2}, "reward": 18},
    "furniture": {"name": "新居家具", "inputs": {"furniture": 1}, "reward": 22},
    "soup": {"name": "工坊午餐", "inputs": {"soup": 2}, "reward": 16},
}
DAILY_LIMIT = 3


def supply_day(tick):
    return (tick + 48) // 144 + 1


def delivery_reward(w, item):
    multiplier = balance.market_day.delivery_multiplier if is_market_day(w) else 1
    return REQUESTS[item]["reward"] * multiplier


def settle_delivery(w, a, item, events):
    request = REQUESTS[item]
    reward = delivery_reward(w, item)
    day = supply_day(w["tick"])
    log = a.get("delivery_log", {})
    done = list(log.get("items", [])) if log.get("day") == day else []
    need(item not in done, "今天已经完成这项交付")
    need(len(done) < DAILY_LIMIT, "今日已完成3项交付，明天再来")
    for key, n in request["inputs"].items():
        need(inv_qty(a["inventory"], key) >= n, "交付物资不足，请先准备完整物资")
    need(w["treasury"] >= reward, "公共交付预算不足，请稍后再来")
    for key, n in request["inputs"].items():
        inv_take(a["inventory"], key, n)
    w["treasury"] -= reward
    a["cash"] += reward
    a["earned"] += reward
    a["delivery_log"] = {"day": day, "items": [*done, item]}
    supply = w.setdefault("supply", {"completed": 0, "goods": {}})
    supply["completed"] += 1
    for key, n in request["inputs"].items():
        supply["goods"][key] = supply["goods"].get(key, 0) + n
    change_reputation(w, a, balance.reputation.delivery_gain, "delivery", events)
    return f"{a['name']}完成「{request['name']}」，获得{reward}镇币"
