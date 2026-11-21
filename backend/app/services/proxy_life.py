"""Departure checkpoints and event-derived return summaries; no extra ledger."""
from collections import Counter
from copy import deepcopy

from sqlalchemy import func, or_, select

from ..catalog import ITEMS
from ..domain.perishables import inv_qty
from ..models import Departure, Event


def depart(db, world, uid):
    row = db.get(Departure, uid)
    if row and row.checkpoint.get("away", False):
        return False  # Logout and socket teardown can report the same departure.
    a = world["agents"][uid]
    point = {
        "tick": world["tick"], "cash": a["cash"], "completed": a["completed"],
        "mode_at_departure": a["mode"], "away": True,
        "event_id": db.scalar(select(func.max(Event.id))) or 0,
    }
    if row:
        row.checkpoint = point
    else:
        db.add(Departure(user_id=uid, checkpoint=point))
    a["mode"] = "rules"
    a["proxy_life"] = True
    a["next_action_tick"] = world["tick"]
    return True


def summarize(db, world, uid, point):
    # Include counterpart events (gifts/orders/feasts); their actor is the initiator.
    query = select(Event).where(
        Event.tick >= point["tick"], Event.tick <= world["tick"],
        or_(Event.actor_id == uid, Event.type.in_(["gift", "order", "feast"])),
    )
    if "event_id" in point:
        query = query.where(Event.id > point["event_id"])
    else:
        query = query.where(Event.tick > point["tick"])
    earned = spent = deliveries = feasts = 0
    gained, spoiled, leisure = Counter(), Counter(), Counter()
    recent = []
    for event in db.scalars(query.order_by(Event.id)):
        d = event.details or {}
        if event.type == "feast":
            feasts += uid in d.get("participants", [])
        if event.actor_id != uid:
            if ((event.type == "gift" and d.get("partner_id") == uid)
                    or (event.type == "order" and d.get("buyer") == uid)):
                if d.get("item"):
                    gained[d["item"]] += d.get("quantity", 0)
            continue
        recent.append(event.text)
        if event.type == "leisure":
            kind = d.get("kind")
            leisure["plaza_visit" if kind == "visit" and not d.get("at_home") else kind] += 1
        before, after = d.get("before", {}), d.get("after", {})
        if "cash" in before and "cash" in after:
            change = after["cash"] - before["cash"]
            earned += max(0, change)
            spent += max(0, -change)
        elif event.type == "levy":
            spent += d.get("amount", 0)
        elif event.type == "order":
            earned += d.get("amount", 0) + d.get("refund", 0)
            spent += d.get("escrow", 0)
        old, new = before.get("inventory", {}), after.get("inventory", {})
        for item in new:
            gained[item] += max(0, inv_qty(new, item) - inv_qty(old, item))
        if event.type == "delivery" or (event.type == "order" and "buyer" in d):
            deliveries += 1
        if event.type == "spoilage":
            spoiled.update(d.get("items") or {"food": d.get("quantity", 0)})
    gained = {key: value for key, value in sorted(gained.items()) if value}
    leisure_text = {
        "plaza_visit": "你串门时邻居不在，去广场坐了坐",
        "stroll": "你去河边散了步", "visit": "你去邻居家串了门",
        "daydream": "你看着河水发了会儿呆", "play": "你在广场玩耍",
        "shop_browse": "你逛了集市",
    }
    # Reserve a visible slot even when a long absence includes many losses.
    highlights = [leisure_text[kind] for kind, _ in leisure.most_common(1)
                  if kind in leisure_text]
    if deliveries:
        highlights.append(f"你完成了{deliveries}次交付")
    if feasts:
        highlights.append("参加了广场聚餐")
    for item, count in sorted(spoiled.items()):
        name = ITEMS.get(item, {"name": "食物"})["name"]
        highlights.append(f"有{count}份{name}变质了")
    if gained:
        goods = "、".join(f"{n}份{ITEMS.get(k, {'name': k})['name']}" for k, n in gained.items())
        highlights.append("你收获了" + goods)
    highlights.append(f"你赚了{earned}镇币，支出了{spent}镇币")
    a = world["agents"][uid]
    return {
        "since_tick": point["tick"], "current_tick": world["tick"],
        "away_ticks": max(0, world["tick"] - point["tick"]),
        "completed": a["completed"] - point["completed"],
        "cash_change": a["cash"] - point["cash"], "recent": recent[-8:][::-1],
        "summary": {"earned": earned, "spent": spent, "gained_items": gained,
                    "events": highlights[:5]},
    }


def return_home(db, world, uid, only_active=False):
    row = db.get(Departure, uid)
    if not row:
        return None, False
    point = deepcopy(row.checkpoint)
    if not point.get("away", "return_summary" not in point):
        return (None if only_active else point.get("return_summary")), False
    result = summarize(db, world, uid, point)
    a = world["agents"][uid]
    a["mode"] = point.get("mode_at_departure", a["mode"])
    a.pop("proxy_life", None)
    if a["mode"] == "manual":
        a["path"], a["task"] = [], None
        a["activity"] = "等待新安排"
    point.update(away=False, away_ticks=result["away_ticks"], summary=result["summary"],
                 return_summary=result)
    row.checkpoint = point
    return result, True
