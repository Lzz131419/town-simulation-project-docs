"""Daily cards, using the same persisted dawn draw as the climate system."""

from itertools import combinations

from ..balance import balance
from .memories import remember
from .market_day import is_market_day
from .rules import emit
from .weather import next_random


def start_flood_effort(w, events):
    """Open one response window when a new storm reaches the town at dawn."""
    current = w.get("flood_effort")
    if current and not current.get("settled", False):
        return False
    rules = balance.flood
    effort = {
        "goal": rules.goal,
        "donated": 0,
        "deadline_tick": w["tick"] + rules.deadline_ticks,
        "participants": [],
        "settled": False,
    }
    w["flood_effort"] = effort
    text = f"暴雨预警！全镇启动防洪筑堤，需捐木材{rules.goal}份，限时{rules.deadline_ticks // 6}小时"
    emit(
        events, w, "town", "flood", text,
        phase="warning", goal=rules.goal, donated=0,
        deadline_tick=effort["deadline_tick"],
    )
    # Stored worlds do not persist socket presence.  Treat residents without a
    # departure checkpoint as present; explicit online=False remains respected
    # by tests and by any future presence projection.
    for agent in w["agents"].values():
        if agent.get("proxy_life") or agent.get("online", True) is False:
            continue
        remember(w, agent, "收到了暴雨预警：参加防洪筑堤")
    return True


def _flood_participants(w, effort):
    return [w["agents"][uid] for uid in effort.get("participants", []) if uid in w["agents"]]


def settle_flood(w, events):
    """Settle an expired response window exactly once."""
    effort = w.get("flood_effort")
    if not effort or effort.get("settled") or w["tick"] < effort.get("deadline_tick", 0):
        return False
    effort["settled"] = True
    participants = _flood_participants(w, effort)
    participant_ids = [a["id"] for a in participants]
    rules = balance.flood
    if effort.get("donated", 0) >= effort.get("goal", rules.goal):
        # A completed response keeps the storm from closing the crossing.
        if w.get("bridge_closed_until", 0) > w["tick"]:
            w["bridge_closed_until"] = w["tick"]
        for left, right in combinations(participants, 2):
            left["relations"][right["id"]] = min(100, left["relations"].get(right["id"], 30) + 10)
            right["relations"][left["id"]] = min(100, right["relations"].get(left["id"], 30) + 10)
        for agent in participants:
            remember(w, agent, "参加了防洪筑堤")
            # The shared daily reputation cap is applied by the existing T7a path.
            from .reputation import change_reputation
            change_reputation(w, agent, 5, "flood_success", events)
        effort["outcome"] = "success"
        emit(
            events, w, "town", "flood", "防洪筑堤成功，暴雨期间桥梁保持畅通",
            phase="settled", outcome="success", goal=effort.get("goal", rules.goal),
            donated=effort.get("donated", 0), participants=participant_ids,
        )
    else:
        # Add the doubled T5 closure duration on top of any existing closure.
        closure = balance.events.bridge_closed_ticks * rules.failure_bridge_multiplier
        w["bridge_closed_until"] = max(w.get("bridge_closed_until", 0), w["tick"] + closure)
        candidates = sorted(item for item, qty in w.get("market", {}).items() if qty > 0)
        lost_item = None
        lost_quantity = 0
        if candidates:
            lost_item = candidates[int(next_random(w) * len(candidates)) % len(candidates)]
            current = w["market"][lost_item]
            lost_quantity = int(current * rules.market_loss_rate)
            w["market"][lost_item] = max(0, current - lost_quantity)
        for agent in participants:
            remember(w, agent, "参加了防洪筑堤")
            from .reputation import change_reputation
            change_reputation(w, agent, 2, "flood_effort", events)
        effort["outcome"] = "failed"
        effort["lost_item"] = lost_item
        effort["lost_quantity"] = lost_quantity
        emit(
            events, w, "town", "flood", "防洪筑堤失败，洪水冲走了集市的部分货物",
            phase="settled", outcome="failed", goal=effort.get("goal", rules.goal),
            donated=effort.get("donated", 0), participants=participant_ids,
            bridge_closed_until=w["bridge_closed_until"], lost_item=lost_item,
            lost_quantity=lost_quantity,
        )
    return True


def draw_daily_event(w, events, roll=None):
    # Sharing the dawn draw preserves the existing seeded climate sequence.
    # Standalone callers can draw directly from the same persisted LCG.
    if roll is None:
        roll = next_random(w)
    rules = balance.events
    w["market_modifiers"] = {}
    w["action_modifiers"] = {}
    w["bridge_closed_until"] = 0
    expires = w["tick"] + balance.weather.ticks_per_day
    weights = {name: weight for name, weight in rules.weights.items()
               if name != "caravan" or not is_market_day(w)}
    cursor = roll * sum(weights.values())
    card = "peaceful"
    for name, weight in weights.items():
        cursor -= weight
        if cursor < 0:
            card = name
            break
    details = {"card": card}
    if card == "caravan":
        w["market_modifiers"] = {
            **dict.fromkeys(rules.caravan_items, rules.caravan_factor),
            "expires_tick": expires,
        }
        text = "商队来访，今日市场工具和布料优惠供应"
    elif card == "bees":
        w["action_modifiers"] = {"gather_honey": rules.honey_factor, "expires_tick": expires}
        text = "蜂群分家，今日采集蜂蜜收获增加"
    elif card == "flood":
        w["bridge_closed_until"] = w["tick"] + rules.bridge_closed_ticks
        details["bridge_closed_until"] = w.get("bridge_closed_until", 0)
        text = "河面涨水，桥暂时封闭，请等待水位回落"
    elif card == "dispute":
        npcs = sorted(a["id"] for a in w["agents"].values() if a["npc"])
        pairs = list(combinations(npcs, 2))
        if pairs:
            fraction = (cursor + rules.weights[card]) / rules.weights[card]
            left, right = (
                w["agents"][uid] for uid in pairs[min(len(pairs) - 1, int(fraction * len(pairs)))]
            )
            for agent, other in ((left, right), (right, left)):
                from .family import change_relation
                change_relation(agent, other, -rules.dispute_loss)
                remember(w, agent, f"与{other['name']}发生了邻里纠纷", topic="dispute")
            details["participants"] = [left["id"], right["id"]]
            text = f"邻里纠纷：{left['name']}与{right['name']}闹了些不愉快"
        else:
            text = "街坊有些小争执，大家决定心平气和地谈谈"
    else:
        text = "平静的一天，雾河镇的生活缓缓向前"
    emit(events, w, "town", "fortune", text, **details)
    return card
