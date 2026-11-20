from ..services import commands
from fastapi import APIRouter, Query
from sqlalchemy import select
from ..database import Session
from ..models import World, Event, Departure, WorldSample
from ..catalog import MEMBERS, ITEMS, PLACES, ACTIONS
from ..config import settings
from ..balance import balance
from ..pathfinding import route, MOVEMENT_PER_TICK
import math
from ..domain.progression import MILESTONES
from ..domain.deliveries import REQUESTS, DAILY_LIMIT
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
def return_summary(u: U):
    with Session() as db:
        point = db.get(Departure, u.id)
        if not point:
            return None
        w = db.get(World, 1).data
        a = w["agents"][u.id]
        p = point.checkpoint
        rows = db.scalars(
            select(Event)
            .where(Event.actor_id == u.id, Event.tick > p["tick"])
            .order_by(Event.id.desc())
            .limit(8)
        ).all()
        return {
            "since_tick": p["tick"],
            "current_tick": w["tick"],
            "completed": a["completed"] - p["completed"],
            "cash_change": a["cash"] - p["cash"],
            "recent": [r.text for r in rows],
        }


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
            "me": w["agents"][u.id],
            "recent": [{"id": e.id, "tick": e.tick, "type": e.type, "text": e.text} for e in rows],
            "ranking": [
                {
                    "id": a["id"],
                    "name": a["name"],
                    "completed": a["completed"],
                    "earned": a["earned"],
                    "contribution": w["project"]["contributors"].get(a["id"], 0),
                }
                for a in w["agents"].values()
                if not a["npc"]
            ],
        }


@router.get("/api/me/route")
def preview_route(place: str, u: U):
    if place not in PLACES:
        raise ValueError("地点不存在")
    with Session() as db:
        a = db.get(World, 1).data["agents"][u.id]
        points = route(a["x"], a["y"], PLACES[place]["x"], PLACES[place]["y"])
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
