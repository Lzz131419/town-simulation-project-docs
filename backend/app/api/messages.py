from fastapi import APIRouter, Query
from sqlalchemy import select
from ..database import Session
from ..models import User, Message
from ..schemas import MessageInput
from ..engine import need
from .dependencies import U

router = APIRouter()


@router.get("/api/messages")
def messages(
    u: U,
    before: int = Query(default=2**63 - 1, ge=1, le=2**63 - 1),
    limit: int = Query(default=100, ge=1, le=100),
):
    with Session() as db:
        rows = db.scalars(
            select(Message)
            .where((Message.sender_id == u.id) | (Message.recipient_id == u.id))
            .where(Message.id < before)
            .order_by(Message.id.desc())
            .limit(limit)
        ).all()
        return [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "recipient_id": m.recipient_id,
                "text": m.text,
                "created_at": m.created_at,
            }
            for m in rows
        ]


@router.post("/api/messages")
def message(data: MessageInput, u: U):
    with Session.begin() as db:
        need(
            data.recipient_id != u.id and db.get(User, data.recipient_id) is not None,
            "请选择其他小组成员",
        )
        need(bool(data.text.strip()), "留言不能为空")
        db.add(Message(sender_id=u.id, recipient_id=data.recipient_id, text=data.text.strip()))
    return {"ok": True}
