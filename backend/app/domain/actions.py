from copy import deepcopy
from ..catalog import ACTIONS, ITEMS, PLACES
from ..pathfinding import route
from .rules import need, emit, capacity
from .progression import record_progress
from .deliveries import REQUESTS, settle_delivery
from .recipes import RECIPES, CONSUMABLES, TOOL_BONUS
from ..balance import balance


def validate_action(action):
    need(
        isinstance(action, dict)
        and set(action) <= {"type", "item", "quantity", "place", "target_id"},
        "行动格式不正确",
    )
    kind = action.get("type")
    need(isinstance(kind, str) and kind in ACTIONS, "不支持的行动")
    quantity = action.get("quantity", 1)
    need(type(quantity) is int and 1 <= quantity <= 10, "数量必须为1至10")
    for field in ("item", "place", "target_id"):
        if field in action:
            need(
                isinstance(action[field], str)
                and bool(action[field].strip())
                and len(action[field]) <= 40,
                "行动参数必须为有效文本",
            )
    need(
        "item" not in action or kind in {"buy", "sell", "contribute", "delivery"},
        "该行动不接受物品参数",
    )
    need("place" not in action or kind == "move", "仅移动行动可指定地点")
    if kind not in {"buy", "sell", "contribute"}:
        need(quantity == 1, "该行动每步只能执行一次")
    if kind in ["buy", "sell", "contribute"]:
        need(
            action.get("item") in (["wood", "cash"] if kind == "contribute" else ITEMS),
            "物品不正确",
        )
    if kind == "delivery":
        need(action.get("item") in REQUESTS and quantity == 1, "请选择一项有效的完整交付")
    if "target_id" in action:
        need(
            kind == "social"
            and isinstance(action["target_id"], str)
            and bool(action["target_id"].strip()),
            "仅邻里交流可指定有效居民",
        )
    if kind == "move":
        need(action.get("place") in PLACES, "地点不存在")
    return {
        "type": kind,
        "quantity": quantity,
        **({"item": action["item"]} if "item" in action else {}),
        **({"place": action["place"]} if "place" in action else {}),
        **({"target_id": action["target_id"]} if "target_id" in action else {}),
    }


def start_action(w, a, raw, events, automatic=False):
    action = validate_action(raw)
    kind = action["type"]
    if kind in CONSUMABLES and ACTIONS[kind]["place"] is None:
        execute(w, a, action, events, automatic)
        return
    place = action.get("place") if kind == "move" else ACTIONS[kind]["place"]
    target = PLACES[place]
    if kind == "social" and action.get("target_id"):
        other = w["agents"].get(action["target_id"])
        need(other is not None and other["id"] != a["id"], "请选择另一位小镇居民")
        target = {"x": other["x"], "y": other["y"], "name": other["name"] + "所在的位置"}
    a["path"] = route(a["x"], a["y"], target["x"], target["y"])
    a["task"] = {**action, "automatic": automatic}
    a["activity"] = "前往" + target["name"]


def execute(w, a, action, events, automatic=False):
    kind = action["type"]
    quantity = action.get("quantity", 1)
    item = action.get("item", "bread")
    inventory = a["inventory"]
    cost = ACTIONS[kind]["energy"]
    need(a["energy"] >= cost, "精力不足，先回家休息")
    before = {
        "cash": a["cash"],
        "inventory": deepcopy(inventory),
        "energy": a["energy"],
        "hunger": a["hunger"],
    }
    if kind in RECIPES:
        recipe = RECIPES[kind]
        inputs, outputs = dict(recipe["inputs"]), dict(recipe["outputs"])
        if kind in TOOL_BONUS and inventory.get("tool", 0) > 0:
            inputs["tool"] = 1
            for key, value in TOOL_BONUS[kind].items():
                outputs[key] += value
        for key, value in inputs.items():
            need(inventory.get(key, 0) >= value, f"需要{value}份{ITEMS[key]['name']}")
        need(
            sum(inventory.values()) - sum(inputs.values()) + sum(outputs.values()) <= capacity(w),
            "背包已满，可出售或交付物资",
        )
        for key, value in inputs.items():
            inventory[key] -= value
        for key, value in outputs.items():
            inventory[key] = inventory.get(key, 0) + value
        gained = "、".join(f"{value}份{ITEMS[key]['name']}" for key, value in outputs.items())
        text = f"{a['name']}{ACTIONS[kind]['name']}，获得{gained}"
    elif kind in CONSUMABLES:
        effect = CONSUMABLES[kind]
        for key, value in effect["inputs"].items():
            need(inventory.get(key, 0) >= value, f"需要{value}份{ITEMS[key]['name']}")
        for key, value in effect["inputs"].items():
            inventory[key] -= value
        a["hunger"] = max(0, a["hunger"] - effect["hunger_relief"])
        a["energy"] = min(100, a["energy"] + effect["energy_gain"])
        text = f"{a['name']}{ACTIONS[kind]['name']}"
    elif kind == "delivery":
        text = settle_delivery(w, a, item)
    elif kind == "work":
        need(w["treasury"] >= 6, "公共工作预算不足")
        w["treasury"] -= 6
        a["cash"] += 6
        a["earned"] += 6
        text = f"{a['name']}完成公共工作，获得6镇币"
    elif kind == "rest":
        gain = (
            balance.needs.hungry_rest_gain
            if a["hunger"] >= balance.needs.high_hunger
            else balance.needs.rest_gain
        )
        a["energy"] = min(100, a["energy"] + gain)
        text = f"{a['name']}回家休息，恢复精力"
    elif kind == "buy":
        price = ITEMS[item]["buy"] * quantity
        need(w["market"][item] >= quantity, "市场库存不足")
        need(a["cash"] >= price, "余额不足")
        need(sum(inventory.values()) + quantity <= capacity(w), "背包已满")
        if automatic:
            need(a["cash"] - price >= a["policy"]["reserve"], "购买超出保留余额")
            need(a["spent_today"] + price <= a["policy"]["daily_budget"], "达到每日自主支出上限")
        a["cash"] -= price
        w["treasury"] += price
        a["spent_today"] += price
        inventory[item] += quantity
        w["market"][item] -= quantity
        w["activity_goal"]["trades"] += 1
        text = f"{a['name']}购买{quantity}份{ITEMS[item]['name']}，花费{price}镇币"
    elif kind == "sell":
        price = ITEMS[item]["sell"] * quantity
        need(inventory[item] >= quantity, "物资不足")
        need(w["treasury"] >= price, "市场收购预算不足")
        inventory[item] -= quantity
        w["market"][item] += quantity
        w["treasury"] -= price
        a["cash"] += price
        a["earned"] += price
        w["activity_goal"]["trades"] += 1
        text = f"{a['name']}出售{quantity}份{ITEMS[item]['name']}，获得{price}镇币"
    elif kind == "social":
        others = [
            x
            for x in w["agents"].values()
            if x["id"] != a["id"] and abs(x["x"] - a["x"]) + abs(x["y"] - a["y"]) < 150
        ]
        if action.get("target_id"):
            other = w["agents"].get(action["target_id"])
            need(other is not None and other["id"] != a["id"], "请选择另一位小镇居民")
            need(
                abs(other["x"] - a["x"]) + abs(other["y"] - a["y"]) < 100,
                "对方已离开，请重新前往交流",
            )
        else:
            need(bool(others), "广场附近暂无邻居，可以稍后再来")
            other = sorted(others, key=lambda x: x["id"])[(w["tick"] // 5) % len(others)]
        prior_relationship = a["relations"].get(other["id"], 30)
        a["relations"][other["id"]] = min(100, prior_relationship + 5)
        other["relations"][a["id"]] = min(100, other["relations"].get(a["id"], 30) + 5)
        text = f"{a['name']}与{other['name']}进行了邻里交流"
    elif kind == "contribute":
        p = w["project"]
        need(not p["completed"], "仓库已经建成")
        if item == "wood":
            need(inventory["wood"] >= quantity, "木材不足")
            need(p["wood"] + quantity <= p["wood_target"], "超过剩余木材需求")
            inventory["wood"] -= quantity
            p["wood"] += quantity
        else:
            need(a["cash"] >= quantity, "余额不足")
            need(p["cash"] + quantity <= p["cash_target"], "超过剩余资金需求")
            if automatic:
                need(
                    a["cash"] - quantity >= a["policy"]["reserve"]
                    and a["spent_today"] + quantity <= a["policy"]["daily_budget"],
                    "捐建超出自主预算",
                )
            a["cash"] -= quantity
            w["treasury"] += quantity
            a["spent_today"] += quantity
            p["cash"] += quantity
        p["contributors"][a["id"]] = p["contributors"].get(a["id"], 0) + quantity
        text = f"{a['name']}为共享仓库捐建{quantity}{'份木材' if item == 'wood' else '镇币'}"
        if p["wood"] >= p["wood_target"] and p["cash"] >= p["cash_target"]:
            p["completed"] = True
            emit(events, w, "town", "construction", "共享仓库落成，全体居民背包容量增加至60份")
    else:
        text = f"{a['name']}抵达{PLACES[action['place']]['name']}"
    record_progress(w, a, "supply" if kind == "delivery" else kind, events, quantity, item)
    a["energy"] = max(0, a["energy"] - cost)
    a["completed"] += 1
    a["last_outcome"] = text
    a["activity"] = ACTIONS[kind]["name"] + "已完成"
    emit(
        events,
        w,
        a,
        kind,
        text,
        before=before,
        **(
            {
                "partner_id": other["id"],
                "relationship": a["relations"][other["id"]],
                "relationship_change": a["relations"][other["id"]] - prior_relationship,
            }
            if kind == "social"
            else {}
        ),
        after={
            "cash": a["cash"],
            "inventory": deepcopy(inventory),
            "energy": a["energy"],
            "hunger": a["hunger"],
        },
    )
