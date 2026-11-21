"""Closed-economy redistribution, never creates money."""

import math
from ..balance import balance
from ..catalog import ITEMS
from .rules import emit
from .market_day import is_market_day


def price(w, item, side):
    """Quote the pre-trade stock without mutating the world (round half up)."""
    if side not in ("buy", "sell"):
        raise ValueError("价格方向必须为 buy 或 sell")
    # Spoiled food has only a fixed salvage value; actions reject purchasing it.
    if item == "spoiled":
        return 1
    rules = balance.pricing
    target = rules.basic_target_stock if item in rules.basic_items else rules.processed_target_stock
    multiplier = min(
        1.8, max(0.5, 1 + 0.4 * math.tanh((target - w["market"].get(item, 0)) / target))
    )

    def rounded_quote(base):
        lower, upper = max(1, math.ceil(0.5 * base)), math.floor(1.8 * base)
        return min(upper, max(lower, math.floor(base * multiplier + 0.5)))

    # Keep both integer bounds and the spread: raise buy when buy - 1 would
    # undercut the sell floor (e.g. abundant bread must remain buy=3, sell=2).
    sell_floor = max(1, math.ceil(0.5 * ITEMS[item]["sell"]))
    buy = max(sell_floor + 1, rounded_quote(ITEMS[item]["buy"]))
    sell = min(buy - 1, rounded_quote(ITEMS[item]["sell"]))
    modifiers = w.get("market_modifiers", {})
    if w["tick"] < modifiers.get("expires_tick", 0):
        factor = modifiers.get(item, 1)
        # Event discounts also respect the base-price integer envelope, so a
        # later reputation discount never has to raise an out-of-bounds quote.
        sell = min(math.floor(1.8 * ITEMS[item]["sell"]),
                   max(sell_floor, math.floor(sell * factor + 0.5)))
        buy = min(math.floor(1.8 * ITEMS[item]["buy"]),
                  max(math.ceil(0.5 * ITEMS[item]["buy"]), sell + 1,
                      math.floor(buy * factor + 0.5)))
    if is_market_day(w):
        sell = min(buy - 1, math.floor(sell * balance.market_day.sell_multiplier + 0.5))
    return buy if side == "buy" else sell


def collect_daily_levy(w, events):
    total = 0
    for a in w["agents"].values():
        protected = max(balance.fiscal.protected_cash, a["policy"]["reserve"])
        surplus = max(0, a["cash"] - protected)
        amount = min(surplus, math.ceil(surplus * balance.fiscal.daily_surplus_rate))
        if amount:
            a["cash"] -= amount
            w["treasury"] += amount
            total += amount
            emit(
                events,
                w,
                a,
                "levy",
                f"{a['name']}缴纳{amount}镇币公共维护金",
                amount=amount,
                protected=protected,
            )
    if total:
        emit(events, w, "town", "fiscal", f"今日公共维护金{total}镇币已进入国库", amount=total)
