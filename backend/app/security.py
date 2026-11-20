import hashlib
import secrets
import time
from fastapi import HTTPException, Request
from pwdlib import PasswordHash
from .database import Session
from .models import LoginSession, User
from .config import settings

passwords = PasswordHash.recommended()
COOKIE = "town_session"


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def find_user(token):
    if not token:
        return None
    with Session() as db:
        s = db.get(LoginSession, digest(token))
        return db.get(User, s.user_id) if s and s.expires > time.time() else None


def current_user(request: Request):
    u = find_user(request.cookies.get(COOKIE))
    if not u:
        raise HTTPException(401, "请先登录")
    return u


def issue_session(db, user, response):
    token = secrets.token_urlsafe(40)
    db.add(
        LoginSession(
            id=digest(token), user_id=user.id, expires=time.time() + settings.session_hours * 3600
        )
    )
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.session_hours * 3600,
        path="/",
    )
    return token
