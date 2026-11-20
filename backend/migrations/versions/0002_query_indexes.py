"""Indexes for bounded per-user and event-history queries."""

from alembic import op
from sqlalchemy import inspect

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _create_index(name, table, columns):
    # SQLite DDL may survive an interrupted revision. Adopt only matching indexes.
    indexes = {index["name"]: index for index in inspect(op.get_bind()).get_indexes(table)}
    existing = indexes.get(name)
    if existing:
        if (
            existing["column_names"] != columns
            or existing["unique"]
            or any(value is not None for value in existing.get("dialect_options", {}).values())
        ):
            raise RuntimeError(f"Index definition mismatch: {name}")
        return
    op.create_index(name, table, columns)


def upgrade():
    _create_index("ix_events_actor_id_id", "events", ["actor_id", "id"])
    _create_index("ix_events_type_id", "events", ["type", "id"])
    _create_index("ix_messages_sender_id_id", "messages", ["sender_id", "id"])
    _create_index("ix_messages_recipient_id_id", "messages", ["recipient_id", "id"])
    _create_index("ix_archives_user_id_id", "archives", ["user_id", "id"])
    _create_index("ix_model_calls_user_id_id", "model_calls", ["user_id", "id"])
    _create_index("ix_model_calls_status", "model_calls", ["status"])
    _create_index("ix_sessions_expires", "sessions", ["expires"])
    _create_index("ix_sessions_user_id", "sessions", ["user_id"])


def downgrade():
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_index("ix_sessions_expires", table_name="sessions")
    op.drop_index("ix_model_calls_status", table_name="model_calls")
    op.drop_index("ix_model_calls_user_id_id", table_name="model_calls")
    op.drop_index("ix_archives_user_id_id", table_name="archives")
    op.drop_index("ix_messages_recipient_id_id", table_name="messages")
    op.drop_index("ix_messages_sender_id_id", table_name="messages")
    op.drop_index("ix_events_type_id", table_name="events")
    op.drop_index("ix_events_actor_id_id", table_name="events")
