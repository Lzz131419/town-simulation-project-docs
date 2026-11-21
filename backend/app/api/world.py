from ..services import commands
from fastapi import APIRouter, Query
from sqlalchemy import select
from ..database import Session
from ..models import World, Event, WorldSample
from ..catalog import MEMBERS, ITEMS, PLACES, ACTIONS
from ..config import settings
from ..balance import balance
from ..pathfinding import route, MOVEMENT_PER_TICK
import math
from ..domain.progression import MILESTONES
from ..domain.deliveries import REQUESTS, DAILY_LIMIT
from ..domain.homes import home_destination
from ..domain.reputation import project_agent, reputation_title
from ..schemas import Policy, Control, Action, Plan, PlanEdit
from ..services.container import runtime
from .dependencies import U

router = APIRouter()


@router.get("/api/world")
def world(u: U):
    return runtime.snapshot(u.id)


@router.get("/api/catalog")
def catalog(u: U):
    return {
        "rules": balance.model_dump(),
        "deliveries": REQUESTS,
        "delivery_daily_limit": DAILY_LIMIT,
        "milestones": MILESTONES,
        "items": ITEMS,
        "places": PLACES,
        "actions": ACTIONS,
        "members": [{"id": uid, "name": name} for uid, name in MEMBERS],
        "tick_seconds": settings.tick_seconds,
        "movement_per_tick": MOVEMENT_PER_TICK,
    }


@router.post("/api/me/action")
async def action(data: Action, u: U):
    return await commands.action(u.id, data)


@router.put("/api/me/control")
async def control(data: Control, u: U):
    return await commands.control(u.id, data)


@router.put("/api/me/policy")
async def policy(data: Policy, u: U):
    return await commands.policy(u.id, data)


@router.put("/api/me/plan")
async def plan(data: Plan, u: U):
    return await commands.plan(u.id, data)


@router.post("/api/me/plan/append")
async def append_plan(data: Plan, u: U):
    return await commands.append(u.id, data)


@router.post("/api/me/plan/edit")
async def edit_plan(data: PlanEdit, u: U):
    return await commands.edit(u.id, data)


@router.get("/api/events")
def events(
    u: U,
    actor_id: str = Query(default="", max_length=40),
    kind: str = Query(default="", max_length=40),
    before: int = Query(default=2**63 - 1, ge=1, le=2**63 - 1),
    limit: int = Query(default=50, ge=1, le=100),
):
    with Session() as db:
        q = select(Event).where(Event.id < before)
        if actor_id:
            q = q.where(Event.actor_id == actor_id)
        if kind:
            q = q.where(Event.type == kind)
        rows = db.scalars(q.order_by(Event.id.desc()).limit(limit)).all()
        return [
            {
                "id": e.id,
                "tick": e.tick,
                "actor_id": e.actor_id,
                "type": e.type,
                "text": e.text,
                "details": e.details,
            }
            for e in rows
        ]


@router.get("/api/return-summary")
async def return_summary(u: U):
    return await runtime.return_summary(u.id)


@router.get("/api/report")
def report(u: U):
    with Session() as db:
        w = db.get(World, 1).data
        rows = db.scalars(
            select(Event).where(Event.actor_id == u.id).order_by(Event.id.desc()).limit(30)
        ).all()
        samples = db.scalars(
            select(WorldSample)
            .order_by(WorldSample.tick.desc())
            .limit(balance.simulation.history_limit)
        ).all()
        return {
            "series": [{"tick": s.tick, **s.data} for s in reversed(samples)],
            "fiscal": balance.fiscal.model_dump(),
            "me": project_agent(w["agents"][u.id]),
            "recent": [{"id": e.id, "tick": e.tick, "type": e.type, "text": e.text} for e in rows],
            "ranking": [
                {
                    "id": a["id"],
                    "name": a["name"],
                    "reputation": a.get("reputation", 0),
                    "title": reputation_title(a.get("reputation", 0)),
                    "completed": a["completed"],
                    "earned": a["earned"],
                    "contribution": w["project"]["contributors"].get(a["id"], 0),
                }
                for a in w["agents"].values()
                if not a["npc"]
            ],
        }


def _economy_bucket(day):
    """Create a stable daily shape for the economy report and its empty days."""
    return {
        "day": day,
        "trade_amount": 0,
        "trade_count": 0,
        "production": {},
        "levy_total": 0,
        "spoilage_loss": 0,
    }


@router.get("/api/report/economy")
def economy_report(u: U, days: int = Query(default=7, ge=1, le=31)):
    """Aggregate structured economic events over the most recent simulation days."""
    del u  # The dependency is intentionally retained to keep report auth identical.
    ticks_per_day = balance.weather.ticks_per_day
    with Session() as db:
        world_row = db.get(World, 1)
        world_data = world_row.data if world_row else {}
        end_tick = int(world_data.get("tick", 0))
        start_tick = max(0, end_tick - days * ticks_per_day + 1)
        rows = db.scalars(
            select(Event)
            .where(Event.tick >= start_tick, Event.tick <= end_tick)
            .order_by(Event.tick, Event.id)
        ).all()

    # Keep only days that are in the requested range.  Days containing only
    # non-economic events still expose explicit zero metrics for charting.
    buckets = {}
    for event in rows:
        day = event.tick // ticks_per_day
        bucket = buckets.setdefault(day, _economy_bucket(day))
        details = event.details or {}
        event_type = event.type
        if event_type == "leisure":
            continue

        # Market buys/sells and filled orders are transactions.  Posted,
        # cancelled, and expired orders carry amount for auditability but are
        # excluded from turnover.
        is_trade = event_type in {"buy", "sell", "trade"}
        if event_type == "order":
            transaction_type = details.get("transaction_type")
            is_trade = transaction_type in {"filled", "fill"} or (
                transaction_type not in {"posted", "cancelled", "expired"}
                and ("amount" in details or "buyer" in details)
            )
        if is_trade:
            amount = details.get("amount")
            if amount is None:
                amount = details.get("unit_price", 0) * details.get("quantity", 0)
            if isinstance(amount, (int, float)):
                bucket["trade_amount"] += amount
                bucket["trade_count"] += 1

        outputs = details.get("outputs")
        if isinstance(outputs, dict):
            for item, quantity in outputs.items():
                if isinstance(quantity, (int, float)):
                    bucket["production"][item] = bucket["production"].get(item, 0) + quantity

        if event_type == "levy" and isinstance(details.get("amount"), (int, float)):
            bucket["levy_total"] += details["amount"]
        if event_type == "spoilage" and isinstance(details.get("quantity"), (int, float)):
            bucket["spoilage_loss"] += details["quantity"]

    daily = [buckets[day] for day in sorted(buckets)]
    totals = _economy_bucket(-1)
    totals.pop("day")
    for bucket in daily:
        totals["trade_amount"] += bucket["trade_amount"]
        totals["trade_count"] += bucket["trade_count"]
        totals["levy_total"] += bucket["levy_total"]
        totals["spoilage_loss"] += bucket["spoilage_loss"]
        for item, quantity in bucket["production"].items():
            totals["production"][item] = totals["production"].get(item, 0) + quantity
    return {
        "days": days,
        "start_tick": start_tick,
        "end_tick": end_tick,
        "daily": daily,
        "series": daily,
        "totals": totals,
    }


@router.get("/api/me/route")
def preview_route(place: str, u: U):
    if place not in PLACES:
        raise ValueError("地点不存在")
    with Session() as db:
        w = db.get(World, 1).data
        a = w["agents"][u.id]
        target = home_destination(w, a) if place == "home" else PLACES[place]
        points = route(a["x"], a["y"], target["x"], target["y"], w)
        x, y, distance = a["x"], a["y"], 0
        for point in points:
            distance += math.hypot(point["x"] - x, point["y"] - y)
            x, y = point["x"], point["y"]
        return {
            "place": place,
            "path": points,
            "distance": round(distance),
            "seconds": math.ceil(distance / MOVEMENT_PER_TICK) * settings.tick_seconds,
        }
