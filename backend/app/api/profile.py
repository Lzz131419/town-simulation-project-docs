from fastapi import APIRouter
from ..database import Session
from ..models import User
from ..schemas import Profile
from .dependencies import U, user_view

router = APIRouter()


@router.get("/api/me")
def me(u: U):
    return user_view(u)


@router.put("/api/me")
def profile(data: Profile, u: U):
    with Session.begin() as db:
        stored = db.get(User, u.id)
        stored.bio = data.bio
        stored.goal = data.goal
    return {"ok": True}
