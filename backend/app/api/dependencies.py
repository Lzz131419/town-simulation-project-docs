from typing import Annotated
from fastapi import Depends
from ..security import current_user
from ..models import User

U = Annotated[User, Depends(current_user)]


def user_view(u):
    return {"id": u.id, "name": u.name, "bio": u.bio, "goal": u.goal}
