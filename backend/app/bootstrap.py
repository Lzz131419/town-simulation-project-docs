"""Schema migrations and additive world initialization run before readiness."""

from copy import deepcopy
from .database import Session, engine
from .models import User, World, Event
from .catalog import MEMBERS, initial_world
from .domain.migration import upgrade_world
from .security import passwords
from .infrastructure.migrations import migrate


def initialize():
    migrate(engine)
    with Session.begin() as db:
        for uid, name in MEMBERS:
            if not db.get(User, uid):
                db.add(User(id=uid, name=name, password_hash=passwords.hash(uid)))
        if not db.get(World, 1):
            db.add(World(id=1, revision=0, data=initial_world()))
            db.add(
                Event(
                    tick=0,
                    actor_id="town",
                    type="welcome",
                    text="六位新邻居来到雾河镇。河畔集市正在筹备。",
                    details={},
                )
            )
        # Additive migration preserves every existing asset, plan and world tick.
        row = db.get(World, 1)
        data = deepcopy(row.data)
        if upgrade_world(data):
            row.data = data
            row.revision += 1
