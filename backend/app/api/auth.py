from ..infrastructure.async_io import run_blocking
from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy import delete
from ..database import Session
from ..models import User, LoginSession
from ..security import passwords, issue_session, digest, COOKIE
from ..schemas import Login
from ..services.container import runtime
from .dependencies import U, user_view

router = APIRouter()


@router.post("/api/auth/login")
def login(data: Login, response: Response):
    with Session.begin() as db:
        u = db.get(User, data.username)
        if not u or not passwords.verify(data.password, u.password_hash):
            raise HTTPException(401, "用户名或密码不正确")
        issue_session(db, u, response)
        return user_view(u)


@router.post("/api/auth/logout")
async def logout(request: Request, response: Response, u: U):
    sid = digest(request.cookies[COOKIE])

    def revoke():
        with Session.begin() as db:
            db.execute(delete(LoginSession).where(LoginSession.id == sid))

    await run_blocking(revoke)
    await runtime.disconnect_session(sid)
    await run_blocking(runtime.record_departure, u.id)
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}
