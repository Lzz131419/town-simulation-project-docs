from .rules import check_invariants, emit, capacity
from .actions import start_action, execute
from .economy import collect_daily_levy
from .recipes import RECIPES
from .plans import finish_plan, pause_failed_plan
from ..pathfinding import advance
from ..catalog import ITEMS, PLACES
from ..balance import balance


def affordable_sale(w, a):
    # Sell only an amount the treasury can actually pay for.
    for item in sorted(a["inventory"], key=a["inventory"].get, reverse=True):
        quantity = min(5, a["inventory"][item], w["treasury"] // ITEMS[item]["sell"])
        if quantity:
            return {"type": "sell", "item": item, "quantity": quantity}
    return None


def can_buy_bread(w, a):
    price = ITEMS["bread"]["buy"]
    return (
        w["market"]["bread"] > 0
        and sum(a["inventory"].values()) < capacity(w)
        and a["cash"] - price >= a["policy"]["reserve"]
        and a["spent_today"] + price <= a["policy"]["daily_budget"]
    )


def social_neighbor(w, a):
    neighbors = [
        other
        for other in w["agents"].values()
        if other["id"] != a["id"] and abs(other["x"] - a["x"]) + abs(other["y"] - a["y"]) < 150
    ]
    if neighbors:
        other = sorted(neighbors, key=lambda x: x["id"])[(w["tick"] // 5) % len(neighbors)]
        return {"type": "social", "target_id": other["id"]}
    return None


def fallback_action(w, a):
    inventory = a["inventory"]
    used = sum(inventory.values())
    # Hunger relief takes priority over trying to sell a full bag.
    if a["policy"]["auto_eat"] and a["hunger"] >= 55:
        if inventory.get("soup", 0):
            return {"type": "eat_soup"}
        if inventory.get("meal", 0):
            return {"type": "eat_meal"}
        if inventory.get("fruit", 0):
            return {"type": "eat_fruit"}
        if inventory["bread"]:
            return {"type": "eat"}
        if a["energy"] < 6:
            return {"type": "rest"}
        if inventory["grain"] >= 2 and used < capacity(w):
            return {"type": "bake"}
        if can_buy_bread(w, a):
            return {"type": "buy", "item": "bread", "quantity": 1}
        sale = affordable_sale(w, a)
        if used >= capacity(w) - 2:
            return sale
        if used + 3 <= capacity(w) and a["energy"] >= 9:
            return {"type": "farm"}
    if a["energy"] < 25:
        if inventory.get("herb", 0) >= 2:
            return {"type": "brew"}
        return {"type": "rest"}
    if used > capacity(w) - 5:
        return affordable_sale(w, a)
    kind = a["policy"]["fallback"]
    if a["npc"]:
        hour = ((w["tick"] * 10 + 480) % 1440) / 60
        schedule = balance.npc
        if hour < schedule.wake_hour or hour >= schedule.sleep_hour:
            if (
                a["energy"] < 95
                or (abs(a["x"] - PLACES["home"]["x"]) + abs(a["y"] - PLACES["home"]["y"])) > 80
            ):
                return {"type": "rest"}
            return None
        if schedule.social_start_hour <= hour < schedule.social_end_hour:
            return social_neighbor(w, a)
        if hour < 12:
            # Three residents have deterministic east-bank morning occupations.
            kind = {
                "npc-1": "gather",
                "npc-2": "chop",
                "npc-3": "harvest_veg",
                "npc-4": "harvest_flax",
                "npc-5": "gather_honey",
                "npc-6": "forage",
            }.get(a["id"], kind)
        # Consume finished goods when hungry and sell surplus during the afternoon.
        if hour >= 16 and used > 8:
            sale = affordable_sale(w, a)
            if sale:
                return sale
    if kind == "work" and w["treasury"] < 6:
        kind = "bake" if inventory["grain"] >= 2 else "farm"
    if kind == "bake" and inventory["grain"] < 2:
        kind = "farm"
    if kind == "social":
        return social_neighbor(w, a)
    sources = {
        "grain": "farm",
        "wood": "craft",
        "fish": "fish",
        "ore": "mine",
        "vegetable": "harvest_veg",
        "flax": "harvest_flax",
        "cloth": "weave",
    }
    seen = set()
    while kind in RECIPES and kind not in seen:
        seen.add(kind)
        missing = next(
            (item for item, n in RECIPES[kind]["inputs"].items() if inventory.get(item, 0) < n),
            None,
        )
        if missing is None or missing not in sources:
            break
        kind = sources[missing]
    recipe = RECIPES.get(kind, {"inputs": {}, "outputs": {}})
    required_room = sum(recipe["outputs"].values()) - sum(recipe["inputs"].values())
    if kind in ("mine", "chop") and inventory.get("tool", 0):
        required_room += 1
    if used + required_room > capacity(w):
        return affordable_sale(w, a)
    return {"type": kind}


def tick_world(w, events):
    w["tick"] += 1
    if (w["tick"] + 48) % 144 == 0:
        collect_daily_levy(w, events)
    for order in w["orders"]:
        if order["status"] == "open" and order["expires_tick"] <= w["tick"]:
            w["agents"][order["buyer_id"]]["cash"] += order["escrow"]
            order["escrow"] = 0
            order["status"] = "expired"
            emit(
                events,
                w,
                order["buyer_id"],
                "order",
                "订单到期，托管资金已退回",
                order_id=order["id"],
            )
    for a in w["agents"].values():
        if (w["tick"] + 48) % 144 == 0:
            a["spent_today"] = 0
        if w["tick"] % 6 == 0:
            a["hunger"] = min(100, a["hunger"] + 3)
        if a["path"]:
            advance(a)
            if a["path"]:
                continue
        if a["task"]:
            task = a["task"]
            a["task"] = None
            try:
                execute(w, a, task, events, task.get("automatic", False))
            except ValueError as error:
                a["last_outcome"] = str(error)
                a["activity"] = "等待新安排"
                a["next_action_tick"] = w["tick"] + balance.simulation.retry_delay_ticks
                emit(events, w, a, "blocked", a["name"] + "：" + str(error))
                pause_failed_plan(w, a, events)
            else:
                finish_plan(w, a, events)
            continue
        if a["mode"] == "manual" or a.get("next_action_tick", 0) > w["tick"]:
            continue
        if a["mode"] == "plan" and not a["plan"]:
            finish_plan(w, a, events)
            continue
        action = a["plan"].pop(0) if a["plan"] else fallback_action(w, a)
        a["next_action_tick"] = w["tick"] + (4 if action else balance.simulation.retry_delay_ticks)
        if action is None:
            a["activity"] = "休息与等待合适机会"
            continue
        try:
            start_action(w, a, action, events, True)
        except ValueError as error:
            a["last_outcome"] = str(error)
            a["next_action_tick"] = w["tick"] + balance.simulation.retry_delay_ticks
            a["activity"] = "等待新安排"
            emit(events, w, a, "blocked", a["name"] + "：" + str(error))
            pause_failed_plan(w, a, events)
        else:
            finish_plan(w, a, events)
    check_invariants(w)
