"""Closed-economy redistribution, never creates money."""

import math
from ..balance import balance
from .rules import emit


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
