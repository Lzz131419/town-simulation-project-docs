from sqlalchemy import String, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base, utc


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    bio: Mapped[str] = mapped_column(Text, default="")
    goal: Mapped[str] = mapped_column(Text, default="准备自己的摊位，和邻居一起办好河畔集市。")


class LoginSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_expires", "expires"),
        Index("ix_sessions_user_id", "user_id"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    expires: Mapped[float]


class World(Base):
    __tablename__ = "worlds"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    revision: Mapped[int] = mapped_column(default=0)
    data: Mapped[dict] = mapped_column(JSON)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_actor_id_id", "actor_id", "id"),
        Index("ix_events_type_id", "type", "id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tick: Mapped[int]
    actor_id: Mapped[str] = mapped_column(String(40))
    type: Mapped[str] = mapped_column(String(40))
    text: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(default=utc)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_sender_id_id", "sender_id", "id"),
        Index("ix_messages_recipient_id_id", "recipient_id", "id"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    recipient_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(default=utc)


class ModelConfig(Base):
    __tablename__ = "model_configs"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    base_url: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(160))
    encrypted_key: Mapped[str] = mapped_column(Text)
    last_call: Mapped[float] = mapped_column(default=0)


class ModelCall(Base):
    __tablename__ = "model_calls"
    __table_args__ = (
        Index("ix_model_calls_user_id_id", "user_id", "id"),
        Index("ix_model_calls_status", "status"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    purpose: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24))
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    usage_reported: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[str] = mapped_column(default=utc)


class Archive(Base):
    __tablename__ = "archives"
    __table_args__ = (Index("ix_archives_user_id_id", "user_id", "id"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(80))
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(default=utc)


class Departure(Base):
    __tablename__ = "departures"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    checkpoint: Mapped[dict] = mapped_column(JSON)


class WorldSample(Base):
    __tablename__ = "world_samples"
    tick: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)
