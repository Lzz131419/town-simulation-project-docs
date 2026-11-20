from ..infrastructure.async_io import run_blocking
import asyncio
from fastapi import APIRouter, HTTPException
from sqlalchemy import select, delete
from ..database import Session
from ..models import ModelConfig, ModelCall
from ..config import encryption
from ..schemas import ModelInput, Prompt
from ..engine import need
from ..ai.provider import validate_base_url
from ..services.container import runtime, planner
from .dependencies import U

router = APIRouter()


@router.get("/api/model")
def model(u: U):
    with Session() as db:
        cfg = db.get(ModelConfig, u.id)
        rows = db.scalars(
            select(ModelCall)
            .where(ModelCall.user_id == u.id)
            .order_by(ModelCall.id.desc())
            .limit(20)
        ).all()
        return {
            "configured": cfg is not None,
            "base_url": cfg.base_url if cfg else "",
            "model": cfg.model if cfg else "",
            "has_key": bool(cfg and cfg.encrypted_key),
            "calls": [
                {
                    "id": r.id,
                    "purpose": r.purpose,
                    "status": r.status,
                    "input_tokens": r.input_tokens,
                    "output_tokens": r.output_tokens,
                    "usage_reported": r.usage_reported,
                    "created_at": r.created_at,
                }
                for r in rows
            ],
        }


@router.put("/api/model")
async def save_model(data: ModelInput, u: U):
    base = await validate_base_url(data.base_url)
    runtime.cancel_calls(u.id)

    def save():
        with Session.begin() as db:
            cfg = db.get(ModelConfig, u.id)
            if not cfg:
                need(bool(data.api_key.strip()), "首次配置需要API Key")
                cfg = ModelConfig(user_id=u.id, base_url=base, model=data.model, encrypted_key="")
                db.add(cfg)
            cfg.base_url = base
            cfg.model = data.model.strip()
            if data.api_key.strip():
                cfg.encrypted_key = encryption().encrypt(data.api_key.strip().encode()).decode()

    await run_blocking(save)
    return {"ok": True}


@router.delete("/api/model")
async def remove_model(u: U):
    runtime.cancel_calls(u.id)

    def remove():
        with Session.begin() as db:
            db.execute(delete(ModelConfig).where(ModelConfig.user_id == u.id))

    await run_blocking(remove)
    return {"ok": True}


@router.post("/api/agent/plan")
async def ai_plan(data: Prompt, u: U):
    try:
        return await planner.run(u.id, data.instruction)
    except asyncio.CancelledError:
        raise HTTPException(409, "已停止本次AI请求")


@router.post("/api/agent/test")
async def ai_test(u: U):
    try:
        return await planner.run(u.id, "连接测试，请简短确认。", "test")
    except asyncio.CancelledError:
        raise HTTPException(409, "已停止本次AI请求")


@router.post("/api/agent/cancel")
async def ai_cancel(u: U):
    runtime.cancel_calls(u.id)
    return {"ok": True}
