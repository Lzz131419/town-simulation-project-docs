"""Rate-limited NPC invitations and a daily plaza gathering."""

from math import hypot

from ..balance import balance
from ..catalog import PLACES, ACTIONS
from .actions import execute
from .economy import price
from .memories import remember
from .orders import post_order
from .perishables import inv_qty, inv_total
from .rules import capacity, emit
from .sleep import action_energy_cost


def npc_initiatives(w, npc, events):
    rules = balance.events
    if npc.get("sleeping") or not npc["npc"] or w["tick"] < npc.get("next_interaction_tick", 0):
        return
    npc["next_interaction_tick"] = w["tick"] + rules.interaction_interval_ticks
    players = sorted(
        (a for a in w["agents"].values() if not a["npc"] and not a.get("sleeping")),
        key=lambda a: (-npc["relations"].get(a["id"], 30), a["id"]),
    )
    if players and w["tick"] >= npc.get("next_private_order_tick", 0):
        target = players[0]
        reserved = sum(
            o["quantity"]
            for o in w["orders"]
            if o["status"] == "open" and o["buyer_id"] == npc["id"]
        )
        if npc["relations"].get(target["id"], 30) >= rules.order_relation and inv_total(
            npc["inventory"]
        ) + reserved + rules.order_quantity <= capacity(w, npc):
            for item in rules.order_items:
                if any(o["status"] == "open" and o["item"] == item for o in w["orders"]):
                    continue
                unit = price(w, item, "sell")
                total = int(unit * rules.order_quantity * rules.order_reward_factor)
                if npc["cash"] < total:
                    continue
                if (
                    sum(o["status"] == "open" and o["buyer_id"] == npc["id"] for o in w["orders"])
                    >= 5
                ):
                    break
                post_order(
                    w,
                    npc,
                    item,
                    rules.order_quantity,
                    unit,
                    events,
                    private_to=target["id"],
                    total_reward=total,
                )
                npc["next_private_order_tick"] = w["tick"] + rules.order_cooldown_ticks
                break
    if (w["tick"] < npc.get("next_gift_tick", 0)
            or npc["energy"] < action_energy_cost(w, npc, "gift", ACTIONS["gift"]["energy"])):
        return
    foods = [item for item in rules.food_items if inv_qty(npc["inventory"], item)]
    if not foods:
        return
    item = min(foods, key=lambda item: (price(w, item, "sell"), item))
    for target in players:
        if (
            npc["relations"].get(target["id"], 30) >= rules.gift_relation
            and abs(npc["x"] - target["x"]) + abs(npc["y"] - target["y"]) < rules.gift_range
            and inv_total(target["inventory"]) < capacity(w, target)
        ):
            execute(w, npc, {"type": "gift", "item": item, "target_id": target["id"]}, events)
            break


def maybe_feast(w, events):
    rules = balance.events
    hour = ((w["tick"] * 10 + 480) % 1440) / 60
    day = (w["tick"] + balance.weather.dawn_offset_ticks) // balance.weather.ticks_per_day
    if not rules.feast_start_hour <= hour < rules.feast_end_hour or w.get("feast_day", -1) == day:
        return
    plaza = PLACES["plaza"]
    participants = sorted(
        (
            a
            for a in w["agents"].values()
            if not a.get("sleeping") and a.get("shared_meal_day") != day and hypot(a["x"] - plaza["x"], a["y"] - plaza["y"]) <= rules.feast_radius
        ),
        key=lambda a: a["id"],
    )
    hosts = [a for a in participants if a["npc"]]
    if len(participants) < rules.feast_min_agents or not hosts:
        return
    host = min(
        hosts,
        key=lambda a: (
            -sum(a["relations"].get(uid, 30) for uid in w["agents"] if uid != a["id"]),
            a["id"],
        ),
    )
    w["feast_day"] = day
    for agent in participants:
        agent["shared_meal_day"] = day
        agent["hunger"] = max(0, agent["hunger"] - rules.feast_hunger_relief)
        for other in participants:
            if other["id"] != agent["id"]:
                agent["relations"][other["id"]] = min(
                    100, agent["relations"].get(other["id"], 30) + rules.feast_relation_gain
                )
        remember(w, agent, "参加了广场聚餐")
    emit(
        events,
        w,
        host,
        "feast",
        f"{host['name']}发起广场聚餐，街坊们围坐在一起",
        participants=[a["id"] for a in participants],
    )
