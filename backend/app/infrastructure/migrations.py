"""Schema upgrades are explicit Alembic revisions, separate from world JSON upgrades."""

from alembic import command
from alembic.config import Config
from ..config import ROOT


def configuration():
    return Config(str(ROOT / "backend/alembic.ini"))


def migrate(engine):
    config = configuration()
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
