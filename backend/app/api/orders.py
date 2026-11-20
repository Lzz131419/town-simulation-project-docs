from fastapi import APIRouter
from ..schemas import OrderInput
from ..engine import post_order, fill_order, cancel_order
from ..services.container import runtime
from .dependencies import U

router = APIRouter()


@router.post("/api/orders")
async def create_order(data: OrderInput, u: U):
    return await runtime.mutate(
        lambda w, e: post_order(w, w["agents"][u.id], data.item, data.quantity, data.unit_price, e)
    )


@router.post("/api/orders/{oid}/fill")
async def deliver(oid: int, u: U):
    await runtime.mutate(lambda w, e: fill_order(w, w["agents"][u.id], oid, e))
    return {"ok": True}


@router.post("/api/orders/{oid}/cancel")
async def cancel(oid: int, u: U):
    await runtime.mutate(lambda w, e: cancel_order(w, w["agents"][u.id], oid, e))
    return {"ok": True}
