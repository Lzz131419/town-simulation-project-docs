from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from cryptography.fernet import Fernet

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", env_prefix="TOWN_", extra="ignore")
    database_url: str = "sqlite:///.local/town.db"
    tick_seconds: float = Field(default=2, ge=0.05, le=3600)
    startup_timeout: float = Field(default=30, ge=1, le=120)
    database_timeout: int = Field(default=3, ge=1, le=30)
    health_timeout: float = Field(default=2, ge=0.1, le=10)
    cookie_secure: bool = False
    encryption_key: str = ""
    session_hours: int = Field(default=168, ge=1, le=720)


settings = Settings()
(ROOT / ".local").mkdir(exist_ok=True)


def encryption():
    if settings.encryption_key:
        return Fernet(settings.encryption_key.encode())
    path = ROOT / ".local/secret.key"
    if not path.exists():
        import os

        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(Fernet.generate_key())
    return Fernet(path.read_bytes().strip())
