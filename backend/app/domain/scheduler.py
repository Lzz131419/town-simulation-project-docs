from random import Random

from .perishables import inv_qty, inv_total, decay_inventory, sale_total
from .rules import check_invariants, emit, capacity
from .actions import start_action, execute, buy_price
from .reputation import change_reputation, reset_reputation_day
from .economy import collect_daily_levy, price
from .recipes import RECIPES, TOOL_BONUS
from .social import close_contacts
from .family import social_blocked, family_dawn, maybe_family_meal, expire_invites
from .plans import finish_plan, pause_failed_plan
from ..pathfinding import advance, bridge_closed, route
from ..world_map import LAYOUT
from ..catalog import ACTIONS, ITEMS
from ..balance import balance
from .fortune import draw_daily_event, settle_flood, start_flood_effort
from .market_day import advance_market_day
from .initiatives import npc_initiatives, maybe_feast
from .migration import upgrade_world
from .homes import home_destination, wants_upgrade, dawn_meal
from .sleep import advance_sleep, action_energy_cost, at_bedtime, wake_energy
from .weather import (
    action_available,
    advance_climate,
    is_dawn,
    production_outputs,
)


def affordable_sale(w, a, highest_price=False):
    # Sell only an amount the treasury can actually pay for.
    values = {item: price(w, item, "sell") for item in a["inventory"]}
    for item in sorted(
        a["inventory"],
        key=lambda item: (
            ITEMS[item]["sell"]
            if highest_price
            else min(5, inv_qty(a["inventory"], item)) * values[item]
        ),
        reverse=True,
    ):
        quantity = min(5, inv_qty(a["inventory"], item))
        while quantity and sale_total(a["inventory"], item, quantity, values[item]) > w["treasury"]:
            quantity -= 1
        if quantity:
            return {"type": "sell", "item": item, "quantity": quantity}
    return None


def can_buy_bread(w, a):
    cost = buy_price(w, a, "bread")
    return (
        w["market"]["bread"] > 0
        and inv_total(a["inventory"]) < capacity(w, a)
        and a["cash"] - cost >= a["policy"]["reserve"]
        and a["spent_today"] + cost <= a["policy"]["daily_budget"]
    )


def social_neighbor(w, a):
    contacts = close_contacts(w, a) if a.get("personality") == "introvert" else None
    neighbors = [
        other
        for other in w["agents"].values()
        if other["id"] != a["id"]
        and not other.get("sleeping")
        and not social_blocked(w, a, other)
        and (contacts is None or other["id"] in contacts)
        and abs(other["x"] - a["x"]) + abs(other["y"] - a["y"]) < 150
    ]
    if neighbors:
        other = sorted(neighbors, key=lambda x: x["id"])[(w["tick"] // 5) % len(neighbors)]
        return {"type": "social", "target_id": other["id"]}
    return None


def _valuable_work(w, a):
    """Choose the greatest gross output sale value among executable recipes."""
    inventory = a["inventory"]
    candidates = []
    for kind, recipe in RECIPES.items():
        if not action_available(w, kind) or a["energy"] < action_energy_cost(
            w, a, kind, ACTIONS[kind]["energy"]
        ):
            continue
        if any(inv_qty(inventory, item) < n for item, n in recipe["inputs"].items()):
            continue
        outputs = dict(recipe["outputs"])
        inputs = dict(recipe["inputs"])
        if kind in TOOL_BONUS and inventory.get("tool", 0):
            inputs["tool"] = 1
            for item, n in TOOL_BONUS[kind].items():
                outputs[item] += n
        outputs, _ = production_outputs(w, kind, outputs)
        room = sum(outputs.values()) - sum(inputs.values())
        if inv_total(inventory) + room <= capacity(w, a):
            value = sum(n * ITEMS[item]["sell"] for item, n in recipe["outputs"].items())
            candidates.append((value, kind))
    if candidates:
        return {"type": max(candidates)[1]}
    return affordable_sale(w, a)


def _personality_overrides(w, a, hour):
    effort = w.get("flood_effort") or {}
    flood_active = (
        effort.get("donated", 0) < effort.get("goal", balance.flood.goal)
        and not effort.get("settled", False)
        and w["tick"] < effort.get("deadline_tick", -1)
        and inv_qty(a["inventory"], "wood") >= balance.flood.wood_per_contribution
        and a["energy"] >= action_energy_cost(w, a, "reinforce", balance.flood.energy)
    )
    if flood_active and (
        a.get("personality") in {"generous", "diligent"}
        or (
            a["relations"]
            and sum(a["relations"].values()) / len(a["relations"]) >= 60
        )
        or a.get("proxy_life")
    ):
        return {"type": "reinforce"}
    personality = a.get("personality")
    if wants_upgrade(w, a):
        return {"type": "upgrade_home"}
    if personality == "diligent":
        return _valuable_work(w, a)
    if personality == "merchant" and hour >= 14:
        return affordable_sale(w, a, highest_price=True)
    if personality == "generous":
        if a["inventory"].get("bread", 0) and w["tick"] >= a.get("next_gift_tick", 0):
            recipients = [
                other
                for other in w["agents"].values()
                if other["id"] != a["id"]
                and not other.get("sleeping")
                and other["cash"] < 20
                and inv_total(other["inventory"]) < capacity(w, other)
                and abs(other["x"] - a["x"]) + abs(other["y"] - a["y"]) < 100
            ]
            if recipients:
                other = min(recipients, key=lambda other: (other["cash"], other["id"]))
                return {"type": "gift", "target_id": other["id"]}
        project = w["project"]
        if a["cash"] > 50 and not project["completed"]:
            quantity = min(
                10,
                project["cash_target"] - project["cash"],
                a["cash"] - a["policy"]["reserve"],
                a["policy"]["daily_budget"] - a["spent_today"],
            )
            if quantity > 0:
                return {"type": "contribute", "item": "cash", "quantity": quantity}
            wood = min(10, project["wood_target"] - project["wood"], a["inventory"].get("wood", 0))
            if wood > 0:
                return {"type": "contribute", "item": "wood", "quantity": wood}
    return None


LEISURE_KINDS = ("stroll", "visit", "daydream", "play", "shop_browse")


def _leisure_window(hour, a=None):
    rules = balance.leisure
    wake = balance.npc.wake_hour
    social_end = balance.npc.social_end_hour + (
        balance.sleep.sociable_social_extension
        if (a or {}).get("personality") == "sociable" else 0
    )
    if balance.npc.social_start_hour <= hour < social_end:
        return False
    return (wake <= hour < wake + rules.morning_hours
            or rules.afternoon_start <= hour < rules.afternoon_end
            or max(rules.evening_start, social_end) <= hour < rules.evening_end)


def _leisure_action(w, a, hour, rng=None):
    """Stable per-resident draws leave the climate RNG sequence untouched."""
    if a.get("sleeping") or at_bedtime(w, a) or not _leisure_window(hour, a):
        return None
    rng = rng or Random(f"leisure:{w.get('rng_seed', 42)}:{w['tick']}:{a['id']}")
    chance = balance.leisure.probability
    personality = a.get("personality")
    if personality == "diligent":
        chance *= balance.leisure.diligent_multiplier
    if rng.random() >= chance:
        return None
    weights = dict(stroll=2, daydream=2, visit=1, play=1, shop_browse=1)
    if personality == "introvert":
        weights.update(stroll=6, daydream=6)
    elif personality in {"sociable", "generous"}:
        weights.update(stroll=1, daydream=1, visit=6, play=6)
    elif personality == "merchant":
        weights.update(stroll=1, daydream=1, shop_browse=10)
    elif personality == "quiet":
        weights.update(daydream=12)
    from .leisure import visit_candidates
    candidates = visit_candidates(w, a)
    if not candidates:
        weights["visit"] = 0
    chosen = rng.choices(list(weights), weights=list(weights.values()), k=1)[0]
    if chosen == "visit":
        return {"type": chosen, "target_id": rng.choice(candidates)["id"]}
    return {"type": chosen}


def fallback_action(w, a):
    if a.get("sleeping"):
        return None
    # A fatigued resident must not get stuck repeatedly trying a +2-cost meal.
    if a["energy"] < action_energy_cost(w, a, "eat", 0):
        return {"type": "rest"}
    if (a["npc"] or a.get("proxy_life")) and at_bedtime(w, a):
        if a["policy"]["auto_eat"] and a["hunger"] >= 55:
            for food, action in (("soup", "eat_soup"), ("meal", "eat_meal"), ("fruit", "eat_fruit"), ("bread", "eat")):
                if inv_qty(a["inventory"], food) and a["energy"] >= action_energy_cost(w, a, action, ACTIONS[action]["energy"]):
                    return {"type": action}
        home = home_destination(w, a)
        if a["energy"] < wake_energy(a) or a.get("fatigue") or abs(a["x"] - home["x"]) + abs(a["y"] - home["y"]) > 1:
            return {"type": "rest"}
        return None
    inventory = a["inventory"]
    used = inv_total(inventory)
    # Hunger relief takes priority over trying to sell a full bag.
    if a["policy"]["auto_eat"] and a["hunger"] >= 55:
        if inv_qty(inventory, "soup"):
            return {"type": "eat_soup"}
        if inv_qty(inventory, "meal"):
            return {"type": "eat_meal"}
        if inv_qty(inventory, "fruit"):
            return {"type": "eat_fruit"}
        if inventory["bread"]:
            return {"type": "eat"}
        if a["energy"] < 6:
            return {"type": "rest"}
        if inventory["grain"] >= 2 and used < capacity(w, a):
            return {"type": "bake"}
        if can_buy_bread(w, a):
            return {"type": "buy", "item": "bread", "quantity": 1}
        sale = affordable_sale(w, a)
        if used >= capacity(w, a) - 2:
            return sale
        farm_outputs, _ = production_outputs(w, "farm", RECIPES["farm"]["outputs"])
        if (
            action_available(w, "farm")
            and used + sum(farm_outputs.values()) <= capacity(w, a)
            and a["energy"] >= action_energy_cost(w, a, "farm", ACTIONS["farm"]["energy"])
        ):
            return {"type": "farm"}
    if a.get("personality") == "diligent" and a["energy"] < 40:
        return {"type": "rest"}
    if a["energy"] < 25:
        if inventory.get("herb", 0) >= 2:
            return {"type": "brew"}
        return {"type": "rest"}
    hour = ((w["tick"] * 10 + 480) % 1440) / 60
    if a["npc"] or a.get("proxy_life"):
        override = _personality_overrides(w, a, hour)
        if override and override["type"] in {"reinforce", "upgrade_home"}:
            return override
        leisure = _leisure_action(w, a, hour)
        if leisure is not None:
            return leisure
        if override is not None:
            return override
    if used > capacity(w, a) - 5:
        return affordable_sale(w, a)
    kind = a["policy"]["fallback"]
    if a["npc"] or a.get("proxy_life"):
        schedule = balance.npc
        social_end = schedule.social_end_hour + (
            balance.sleep.sociable_social_extension if a.get("personality") == "sociable" else 0
        )
        if schedule.social_start_hour <= hour < social_end and w.get("weather", "sunny") not in (
            "rain", "storm",
        ):
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
    # Compare the value added by baking with another harvest; preserve schedules.
    if (a["npc"] or a.get("proxy_life")) and kind == "farm" and inventory["grain"] >= 2:
        grain_value = price(w, "grain", "sell")
        if 3 * price(w, "bread", "sell") - 2 * grain_value > 3 * grain_value:
            kind = "bake"
    if kind == "work" and w["treasury"] < 6:
        kind = "bake" if inventory["grain"] >= 2 else "farm"
    if kind == "bake" and inventory["grain"] < 2:
        kind = "farm"
    if (a["npc"] or a.get("proxy_life")) and kind == "social" and w.get("weather", "sunny") in ("rain", "storm"):
        kind = "craft"
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
            (item for item, n in RECIPES[kind]["inputs"].items() if inv_qty(inventory, item) < n),
            None,
        )
        if missing is None or missing not in sources:
            break
        kind = sources[missing]
    if not action_available(w, kind):
        kind = "fish"
    recipe = RECIPES.get(kind, {"inputs": {}, "outputs": {}})
    outputs, _ = production_outputs(w, kind, recipe["outputs"])
    required_room = sum(outputs.values()) - sum(recipe["inputs"].values())
    if kind in ("mine", "chop") and inventory.get("tool", 0):
        required_room += 1
    if used + required_room > capacity(w, a):
        return affordable_sale(w, a)
    return {"type": kind}


def tick_world(w, events):
    # Direct simulation/replay callers must receive the same upgrades as runtime.mutate.
    upgrade_world(w)
    w["tick"] += 1
    expire_invites(w, events)
    settle_flood(w, events)
    dawn = is_dawn(w)
    if dawn:
        for a in w["agents"].values():
            reset_reputation_day(w, a)
        previous_weather = w.get("weather", "sunny")
        roll = advance_climate(w, events)
        advance_market_day(w, events)
        draw_daily_event(w, events, roll)
        if previous_weather != "storm" and w.get("weather") == "storm":
            start_flood_effort(w, events)
        collect_daily_levy(w, events)
        family_dawn(w, events)
    for order in w["orders"]:
        if order["status"] == "open" and order["expires_tick"] <= w["tick"]:
            refund = order["escrow"]
            w["agents"][order["buyer_id"]]["cash"] += refund
            order["escrow"] = 0
            order["status"] = "expired"
            if order.get("private_to") is not None:
                change_reputation(
                    w, w["agents"][order["buyer_id"]],
                    -balance.reputation.private_order_expiry_loss, "private_order_expired", events,
                )
            emit(
                events,
                w,
                order["buyer_id"],
                "order",
                "订单到期，托管资金已退回",
                order_id=order["id"],
                refund=refund,
                transaction_type="expired",
            )
    for a in w["agents"].values():
        if dawn:
            a["spent_today"] = 0
            before_decay = {item: inv_qty(a["inventory"], item) for item in a["inventory"]}
            spoiled = decay_inventory(a["inventory"])
            if spoiled:
                emit(
                    events,
                    w,
                    a,
                    "spoilage",
                    f"{a['name']} 的 {spoiled} 份食物变质了",
                    quantity=spoiled,
                    items={item: n - inv_qty(a["inventory"], item)
                           for item, n in before_decay.items()
                           if n > inv_qty(a["inventory"], item)},
                )
        if w["tick"] % balance.needs.hunger_interval_ticks == 0:
            gain = (
                balance.season.summer_hunger_gain
                if w.get("season", "spring") == "summer"
                else balance.needs.hunger_gain
            )
            a["hunger"] = min(100, a["hunger"] + gain)
        if dawn:
            dawn_meal(w, a)
        if advance_sleep(w, a, events):
            continue
        if a["path"]:
            if bridge_closed(w) and (a.get("task") or {}).get("type") != "reinforce":
                if a.get("bridge_wait_until", 0) > w["tick"]:
                    continue
                river = LAYOUT["river"]
                if any(river["x"] <= p["x"] < river["x"] + river["width"] for p in a["path"]):
                    target = a["path"][-1]
                    try:
                        a["path"] = route(a["x"], a["y"], target["x"], target["y"], w)
                    except ValueError as error:
                        a["bridge_wait_until"] = w.get("bridge_closed_until", 0)
                        a["last_outcome"] = str(error)
                        a["activity"] = "等待河水回落"
                        emit(events, w, a, "blocked", a["name"] + "：" + str(error))
                        continue
            advance(a)
            if a["path"]:
                continue
        if a["task"]:
            task = a["task"]
            if task["type"] in LEISURE_KINDS:
                from .leisure import visit_destination
                from .family import pending_invite
                if task["type"] == "visit":
                    target = visit_destination(w, a, task.get("target_id"))
                    if abs(a["x"] - target["x"]) + abs(a["y"] - target["y"]) > 4:
                        # The host may have left while the guest was walking.
                        task.pop("stay_until", None)
                        try:
                            a["path"] = route(a["x"], a["y"], target["x"], target["y"], w)
                            a["activity"] = "前往" + target["name"]
                        except ValueError:
                            a["task"] = None
                            a["activity"] = "等路通了再去串门"
                        continue
                if "stay_until" not in task:
                    # A timed invitation settles upon arrival, including its final
                    # valid tick; ordinary visits retain the T14 leisure pause.
                    host = w['agents'].get(task.get('target_id'))
                    invited = task['type'] == 'visit' and host and pending_invite(w, a, host)
                    task["stay_until"] = w["tick"] + (0 if invited else balance.leisure.stay_ticks)
                    a["activity"] = ACTIONS[task["type"]]["name"]
                if w["tick"] < task["stay_until"]:
                    continue
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
        npc_initiatives(w, a, events)
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
    maybe_feast(w, events)
    maybe_family_meal(w, events)
    check_invariants(w)
