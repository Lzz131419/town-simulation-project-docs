from ..infrastructure.async_io import run_blocking
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, func
from ..database import Session
from ..models import User, Archive
from ..schemas import Policy, SaveInput
from ..engine import need, validate_action, emit
from ..services.container import runtime
from .dependencies import U, user_view

router = APIRouter()


@router.get("/api/archives")
def archives(u: U):
    with Session() as db:
        rows = db.scalars(
            select(Archive).where(Archive.user_id == u.id).order_by(Archive.id.desc())
        ).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "created_at": r.created_at,
                "tick": r.data["world"]["tick"],
            }
            for r in rows
        ]


@router.post("/api/archives")
async def archive(data: SaveInput, u: U):
    def save():
        snapshot = runtime.snapshot(u.id)["world"]
        with Session.begin() as db:
            need(
                db.scalar(select(func.count()).select_from(Archive).where(Archive.user_id == u.id))
                < 20,
                "最多保留20份归档，请删除旧归档",
            )
            profile = db.get(User, u.id)
            row = Archive(
                user_id=u.id,
                title=data.title,
                data={"world": snapshot, "profile": user_view(profile)},
            )
            db.add(row)
            db.flush()
            return {"id": row.id}

    async with runtime.lock:
        return await run_blocking(save)


def own_archive(db, aid, u):
    a = db.get(Archive, aid)
    if not a or a.user_id != u.id:
        raise HTTPException(404, "归档不存在")
    return a


@router.get("/api/archives/{aid}")
def archive_detail(aid: int, u: U):
    with Session() as db:
        r = own_archive(db, aid, u)
        return {"id": r.id, "title": r.title, "created_at": r.created_at, "data": r.data}


@router.post("/api/archives/{aid}/restore-plan")
async def restore_plan(aid: int, u: U):
    def load():
        with Session() as db:
            return own_archive(db, aid, u).data

    data = await run_blocking(load)
    a = data["world"]["agents"][u.id]
    pol = Policy(**a["policy"]).model_dump()
    actions = [validate_action(x) for x in a["plan"]]
    runtime.cancel_calls(u.id)

    def apply(w, e):
        me = w["agents"][u.id]
        me.update(
            plan=actions, policy=pol, mode="manual", task=None, path=[], activity="等待新安排"
        )
        emit(
            e,
            w,
            me,
            "archive",
            me["name"] + "从归档恢复了个人计划与规则；资产和共享世界继续保持当前进度",
        )

    await runtime.mutate(apply)
    return {"ok": True}


@router.delete("/api/archives/{aid}")
def delete_archive(aid: int, u: U):
    with Session.begin() as db:
        db.delete(own_archive(db, aid, u))
    return {"ok": True}
