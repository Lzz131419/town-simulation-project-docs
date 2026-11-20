"""Use the application connection, or the configured engine for explicit CLI runs."""

from alembic import context
from app.database import Base, engine
from app import models  # noqa: F401


def run(connection):
    context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise RuntimeError(
        "Run migrations against a database or a verified copy; offline SQL is unsupported"
    )
connection = context.config.attributes.get("connection")
if connection is not None:
    run(connection)
else:
    with engine.begin() as connection:
        run(connection)
