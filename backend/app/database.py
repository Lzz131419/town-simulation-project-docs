from datetime import datetime, timezone
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    connect_args=(
        {"check_same_thread": False, "timeout": settings.database_timeout}
        if settings.database_url.startswith("sqlite")
        else {"connect_timeout": settings.database_timeout}
    ),
    pool_pre_ping=True,
)
if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def sqlite_pragmas(connection, _):
        c = connection.cursor()
        c.execute("PRAGMA foreign_keys=ON")
        c.execute("PRAGMA journal_mode=WAL")
        c.close()


Session = sessionmaker(engine, expire_on_commit=False)


def utc():
    return datetime.now(timezone.utc).isoformat()
