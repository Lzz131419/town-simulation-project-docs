"""Initial schema; adopt compatible pre-Alembic tables without rewriting data."""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _create_table(name, *parts):
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table(name):
        actual = {c["name"] for c in inspector.get_columns(name)}
        required = {c.name for c in parts if isinstance(c, sa.Column)}
        pk = (
            "tick"
            if name == "world_samples"
            else "user_id"
            if name in {"departures", "model_configs"}
            else "id"
        )
        if not required <= actual or inspector.get_pk_constraint(name)["constrained_columns"] != [
            pk
        ]:
            raise RuntimeError(
                f"Legacy schema mismatch in {name}; migration stopped without replacing the table"
            )
        return
    op.create_table(name, *parts)


def upgrade():
    _create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tick", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.String(length=40), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table(
        "users",
        sa.Column("id", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=40), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    _create_table(
        "world_samples",
        sa.Column("tick", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("tick"),
    )
    _create_table(
        "worlds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table(
        "archives",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table(
        "departures",
        sa.Column("user_id", sa.String(length=40), nullable=False),
        sa.Column("checkpoint", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    _create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sender_id", sa.String(length=40), nullable=False),
        sa.Column("recipient_id", sa.String(length=40), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["sender_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table(
        "model_calls",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.String(length=40), nullable=False),
        sa.Column("purpose", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("usage_reported", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    _create_table(
        "model_configs",
        sa.Column("user_id", sa.String(length=40), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column("last_call", sa.Double(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )
    _create_table(
        "sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=40), nullable=False),
        sa.Column("expires", sa.Double(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    raise RuntimeError(
        "The initial data schema is not destructively downgraded; restore a verified backup"
    )
