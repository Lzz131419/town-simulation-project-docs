from copy import deepcopy
import math
from ..catalog import ACTIONS, ITEMS, PLACES
from ..pathfinding import route
from .rules import need, emit, capacity
from .progression import record_progress
from .deliveries import REQUESTS, settle_delivery, delivery_reward
from .market_day import is_market_day
from .recipes import RECIPES, CONSUMABLES, TOOL_BONUS
from .memories import remember
from .social import relationship_gains
from .family import social_blocked, reconcile, maybe_invite
from .economy import price
from .reputation import change_reputation
from .perishables import PERISHABLES, inv_qty, inv_total, inv_add, inv_take, sale_total
from ..balance import balance
from .weather import require_available, production_outputs
from .homes import home_destination, claim_home, upgrade_home, owned_home
from .sleep import action_energy_cost, energy_limit, begin_sleep, disturb


def buy_price(w, a, item):
    """Market modifier rounds first in price(); reputation floors next, then clamps."""
    quote = price(w, item, "buy")
    if a.get("reputation", 0) < balance.reputation.discount_threshold:
        return quote
    lower = max(1, math.ceil(0.5 * ITEMS[item]["buy"]), price(w, item, "sell") + 1)
    upper = math.floor(1.8 * ITEMS[item]["buy"])
    return max(lower, min(upper, math.floor(quote * balance.reputation.buy_multiplier)))


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
    if kind in CONSUMABLES:
        need(action.get("item") != "spoiled", "变质食物不能食用")
    if kind == "buy":
        need(action.get("item") != "spoiled", "没人想买变质食物")
    need(
        "item" not in action or kind in {"buy", "sell", "contribute", "delivery", "gift"},
        "该行动不接受物品参数",
    )
    need("place" not in action or kind == "move", "仅移动行动可指定地点")
    if kind == "reinforce":
        need(quantity == 1, "加固河堤每次只能捐2份木材")
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
            kind in {"social", "gift", "visit"}
            and isinstance(action["target_id"], str)
            and bool(action["target_id"].strip()),
            "仅邻里交流、赠礼或串门可指定有效居民",
        )
    if kind == "gift":
        need(bool(action.get("target_id")), "请选择赠礼对象")
        need(action.get("item", "bread") in balance.events.food_items, "请选择可赠送的食物")
    if kind == "visit":
        need(bool(action.get("target_id")), "请选择串门对象")
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
    need(not a.get("sleeping"), "正在睡觉，请等醒来后再行动")
    action = validate_action(raw)
    kind = action["type"]
    require_available(w, kind)
    if kind in CONSUMABLES and ACTIONS[kind]["place"] is None:
        execute(w, a, action, events, automatic)
        return
    place = action.get("place") if kind == "move" else ACTIONS[kind]["place"]
    target = home_destination(w, a) if place == "home" else PLACES[place]
    if kind == "upgrade_home":
        need(owned_home(w, a) is not None, "请先回家睡一次，认领住宅")
    if kind in {"social", "gift"} and action.get("target_id"):
        other = w["agents"].get(action["target_id"])
        need(other is not None and other["id"] != a["id"], "请选择另一位小镇居民")
        if kind == "social":
            need(not social_blocked(w, a, other), "家人今天拌了嘴，暂时不想交谈")
        target = {"x": other["x"], "y": other["y"], "name": other["name"] + "所在的位置"}
    if kind == "visit":
        from .leisure import visit_candidates, visit_destination
        need(any(other["id"] == action["target_id"] for other in visit_candidates(w, a)),
             "只能去熟悉度至少40且已有住宅的邻居家串门")
        target = visit_destination(w, a, action["target_id"])
    # Reinforcement crews are allowed to reach the work site while the bridge
    # is closed; the task itself is exactly what keeps that route available.
    route_world = None if kind == "reinforce" else w
    a["path"] = route(a["x"], a["y"], target["x"], target["y"], route_world)
    if kind == "rest":
        claim_home(w, a, events)
    a["task"] = {**action, "automatic": automatic}
    a["activity"] = "前往" + target["name"]


def execute(w, a, action, events, automatic=False):
    need(not a.get("sleeping"), "正在睡觉，请等醒来后再行动")
    kind = action["type"]
    require_available(w, kind)
    quantity = action.get("quantity", 1)
    item = action.get("item", "bread")
    inventory = a["inventory"]
    cost = action_energy_cost(w, a, kind, ACTIONS[kind]["energy"])
    interaction_details = {}
    # Recovery must remain reachable at zero energy; its +2 penalty saturates at zero.
    need(kind == "rest" or a["energy"] >= cost, "精力不足，先回家休息")
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
        outputs, climate_hints = production_outputs(w, kind, outputs)
        for key, value in inputs.items():
            need(inv_qty(inventory, key) >= value, f"需要{value}份{ITEMS[key]['name']}")
        need(
            inv_total(inventory) - sum(inputs.values()) + sum(outputs.values()) <= capacity(w, a),
            "背包已满，可出售或交付物资",
        )
        for key, value in inputs.items():
            inv_take(inventory, key, value)
        for key, value in outputs.items():
            inv_add(inventory, key, value)
        gained = "、".join(f"{value}份{ITEMS[key]['name']}" for key, value in outputs.items())
        text = f"{a['name']}{ACTIONS[kind]['name']}，获得{gained}"
        interaction_details = {
            "inputs": inputs,
            "outputs": outputs,
        }
        if climate_hints:
            text += "（" + "、".join(climate_hints) + "）"
    elif kind in CONSUMABLES:
        effect = CONSUMABLES[kind]
        for key, value in effect["inputs"].items():
            need(inv_qty(inventory, key) >= value, f"需要{value}份{ITEMS[key]['name']}")
        need(item != "spoiled", "变质食物不能食用")
        stale = False
        for key, value in effect["inputs"].items():
            batches = inv_take(inventory, key, value)
            stale |= key in PERISHABLES and any(batch["fresh"] < 50 for batch in batches)
        divisor = 2 if stale else 1
        a["hunger"] = max(0, a["hunger"] - effect["hunger_relief"] // divisor)
        a["energy"] = min(energy_limit(a), a["energy"] + effect["energy_gain"] // divisor)
        text = f"{a['name']}{ACTIONS[kind]['name']}"
        if stale:
            text += "（不太新鲜了）"
    elif kind == "delivery":
        text = settle_delivery(w, a, item, events)
        remember(w, a, f"完成了{REQUESTS[item]['name']}交付")
        delivered_quantity = REQUESTS[item]["inputs"].get(item, 1)
        interaction_details = {
            "amount": delivery_reward(w, item),
            "item": item,
            "quantity": delivered_quantity,
            "unit_price": delivery_reward(w, item) / delivered_quantity,
        }
    elif kind == "work":
        need(w["treasury"] >= 6, "公共工作预算不足")
        w["treasury"] -= 6
        a["cash"] += 6
        a["earned"] += 6
        text = f"{a['name']}完成公共工作，获得6镇币"
        interaction_details = {"amount": 6}
    elif kind == "upgrade_home":
        text, interaction_details = upgrade_home(w, a, events, automatic)
    elif kind == "rest":
        begin_sleep(w, a, events)
        text = f"{a['name']}{'回家休息' if owned_home(w, a) else '在广场长椅休息'}，躺下睡觉"
    elif kind == "buy":
        need(item != "spoiled", "没人想买变质食物")
        quoted = price(w, item, "buy")
        unit_price = buy_price(w, a, item)
        total = unit_price * quantity
        interaction_details = {
            "unit_price": unit_price,
            "quoted_unit_price": quoted,
            "discount": (quoted - unit_price) * quantity,
            "amount": total,
            "item": item,
            "quantity": quantity,
        }
        need(w["market"][item] >= quantity, "市场库存不足")
        need(a["cash"] >= total, "余额不足")
        need(inv_total(inventory) + quantity <= capacity(w, a), "背包已满")
        if automatic:
            need(a["cash"] - total >= a["policy"]["reserve"], "购买超出保留余额")
            need(a["spent_today"] + total <= a["policy"]["daily_budget"], "达到每日自主支出上限")
        a["cash"] -= total
        w["treasury"] += total
        a["spent_today"] += total
        inv_add(inventory, item, quantity)
        w["market"][item] -= quantity
        w["activity_goal"]["trades"] += 1
        text = f"{a['name']}以{total}镇币购得{quantity}份{ITEMS[item]['name']}"
    elif kind == "sell":
        need(inv_qty(inventory, item) >= quantity, "物资不足")
        unit_price = price(w, item, "sell")
        total = sale_total(inventory, item, quantity, unit_price)
        need(w["treasury"] >= total, "市场收购预算不足")
        inv_take(inventory, item, quantity)
        w["market"][item] += quantity
        w["treasury"] -= total
        a["cash"] += total
        a["earned"] += total
        w["activity_goal"]["trades"] += 1
        text = f"{a['name']}出售{quantity}份{ITEMS[item]['name']}，获得{total}镇币"
        interaction_details = {
            "amount": total,
            "item": item,
            "quantity": quantity,
            "unit_price": unit_price,
        }
    elif kind == "gift":
        other = w["agents"].get(action.get("target_id"))
        need(other is not None and other["id"] != a["id"], "请选择另一位小镇居民")
        need(
            abs(other["x"] - a["x"]) + abs(other["y"] - a["y"]) < balance.events.gift_range,
            "对方已离开，请重新前往赠礼",
        )
        need(item in balance.events.food_items, "请选择可赠送的食物")
        need(inv_qty(inventory, item) >= 1, f"没有可赠送的{ITEMS[item]['name']}")
        need(inv_total(other["inventory"]) < capacity(w, other), "对方背包已满")
        for batch in inv_take(inventory, item, 1):
            inv_add(other["inventory"], item, batch["qty"], batch["fresh"])
        disturb(w, other, a, events)
        goods = ITEMS[item]["name"]
        remember(w, a, f"赠送给{other['name']}1个{goods}")
        remember(w, other, f"收到了{a['name']}赠送的1个{goods}")
        text = f"{a['name']}赠送给{other['name']}1个{goods}"
        interaction_details = {"partner_id": other["id"], "item": item, "quantity": 1}
        change_reputation(w, a, balance.reputation.gift_gain, "gift", events)
        if a["npc"]:
            a["next_gift_tick"] = w["tick"] + balance.events.gift_cooldown_ticks
    elif kind == "reinforce":
        effort = w.get("flood_effort") or {}
        rules = balance.flood
        need(
            not effort.get("settled", False)
            and w["tick"] < effort.get("deadline_tick", -1)
            and effort.get("donated", 0) < effort.get("goal", rules.goal),
            "当前没有可参与的防洪筑堤任务",
        )
        need(inv_qty(inventory, "wood") >= rules.wood_per_contribution, "木材不足")
        inv_take(inventory, "wood", rules.wood_per_contribution)
        effort["donated"] = effort.get("donated", 0) + rules.wood_per_contribution
        if a["id"] not in effort.setdefault("participants", []):
            effort["participants"].append(a["id"])
        remember(w, a, "参加了防洪筑堤")
        text = f"{a['name']}加固河堤，捐出{rules.wood_per_contribution}份木材"
        interaction_details = {
            "item": "wood",
            "quantity": rules.wood_per_contribution,
            "flood_effort": {
                "goal": effort.get("goal", rules.goal),
                "donated": effort["donated"],
                "deadline_tick": effort.get("deadline_tick"),
            },
        }
    elif kind == "social":
        others = [
            x
            for x in w["agents"].values()
            if x["id"] != a["id"] and not social_blocked(w, a, x) and not x.get("sleeping") and abs(x["x"] - a["x"]) + abs(x["y"] - a["y"]) < 150
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
        need(not social_blocked(w, a, other), "家人今天拌了嘴，暂时不想交谈")
        prior_relationship = a["relations"].get(other["id"], 30)
        interrupted = disturb(w, other, a, events)
        own_gain, other_gain = (0, 0) if interrupted else relationship_gains(w, a, other)
        plaza = PLACES["plaza"]
        if not interrupted and is_market_day(w) and all(
            math.hypot(person["x"] - plaza["x"], person["y"] - plaza["y"])
            <= balance.market_day.social_radius for person in (a, other)
        ):
            own_gain += balance.market_day.social_bonus
            other_gain += balance.market_day.social_bonus
        a["relations"][other["id"]] = min(100, a["relations"].get(other["id"], 30) + own_gain)
        other["relations"][a["id"]] = min(100, other["relations"].get(a["id"], 30) + other_gain)
        text = f"{a['name']}与{other['name']}进行了邻里交流"
        interaction_details = {
            "partner_id": other["id"],
            "relationship": a["relations"][other["id"]],
            "relationship_change": a["relations"][other["id"]] - prior_relationship,
        }
        if other["npc"]:
            memories = other.get("memories", [])
            disputes = [m for m in memories if m.get("topic") == "dispute"]
            gossip = (
                (disputes or memories)[-1]["text"]
                if memories
                else balance.npc.small_talk[w["tick"] % len(balance.npc.small_talk)]
            )
            text += f"，{other['name']}说：“{gossip}”"
            interaction_details["gossip"] = gossip
        remember(w, a, f"与{other['name']}交谈")
        remember(w, other, f"与{a['name']}交谈")
        if not interrupted:
            reconcile(w, a, other, events)
            maybe_invite(w, a, other, events)
    elif kind in {"stroll", "visit", "daydream", "play", "shop_browse"}:
        from .leisure import settle_leisure
        text, interaction_details = settle_leisure(w, a, action, events)
    elif kind == "contribute":
        p = w["project"]
        need(not p["completed"], "仓库已经建成")
        if item == "wood":
            need(inventory["wood"] >= quantity, "木材不足")
            need(p["wood"] + quantity <= p["wood_target"], "超过剩余木材需求")
            inv_take(inventory, "wood", quantity)
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
        interaction_details = {
            "item": item,
            "quantity": quantity,
            **({"amount": quantity} if item == "cash" else {}),
        }
        if p["wood"] >= p["wood_target"] and p["cash"] >= p["cash_target"]:
            p["completed"] = True
            emit(events, w, "town", "construction", "共享仓库落成，全体居民基础背包容量增加至60份")
    else:
        text = f"{a['name']}抵达{PLACES[action['place']]['name']}"
    if kind not in {"stroll", "visit", "daydream", "play", "shop_browse"}:
        record_progress(w, a, "supply" if kind == "delivery" else kind, events, quantity, item)
    a["energy"] = min(energy_limit(a), max(0, a["energy"] - cost + interaction_details.get("energy_gain", 0)))
    a["completed"] += 1
    a["last_outcome"] = text
    leisure = kind in {"stroll", "visit", "daydream", "play", "shop_browse"}
    a["activity"] = a["activity"] if a.get("sleeping") else (
        ACTIONS[kind]["name"] if leisure else ACTIONS[kind]["name"] + "已完成"
    )
    event_kind = "leisure" if leisure else kind
    if leisure:
        interaction_details["kind"] = kind
    emit(
        events,
        w,
        a,
        event_kind,
        text,
        before=before,
        **interaction_details,
        after={
            "cash": a["cash"],
            "inventory": deepcopy(inventory),
            "energy": a["energy"],
            "hunger": a["hunger"],
        },
    )
