import os
from pathlib import Path
import subprocess
from unittest.mock import AsyncMock

import httpx
import pytest
from sqlalchemy import select
from app.ai.planner import Planner
from app.config import encryption
from app.database import Session
from app.models import ModelConfig, ModelCall, World
from app.main import runtime


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body", [b"broken json", b'{"choices":[]}', b'{"choices":[{"message":{"content":"[1,2]"}}]}']
)
async def test_bad_provider_payload_records_failure_and_preserves_plan(auth, monkeypatch, body):
    import app.ai.provider as provider

    with Session.begin() as db:
        db.add(
            ModelConfig(
                user_id="wangjue",
                base_url="https://provider.example/v1",
                model="test",
                encrypted_key=encryption().encrypt(b"test-only").decode(),
            )
        )
    monkeypatch.setattr(runtime, "online", lambda _: True)
    monkeypatch.setattr(provider, "validate_base_url", AsyncMock())
    original = httpx.AsyncClient
    monkeypatch.setattr(
        provider.httpx,
        "AsyncClient",
        lambda **kw: original(
            transport=httpx.MockTransport(lambda r: httpx.Response(200, content=body)), **kw
        ),
    )
    with pytest.raises(ValueError, match="模型返回格式不正确"):
        await Planner(runtime).run("wangjue", "计划")
    with Session() as db:
        assert db.scalar(select(ModelCall)).status == "failed"
        assert db.get(World, 1).data["agents"]["wangjue"]["plan"] == []
    assert 'town_llm_calls{status="failed"} 1' in auth.get("/metrics").text


def test_profile_roundtrip_and_input_validation(auth):
    value = {"bio": "我喜欢园艺", "goal": "经营农场，帮助邻居"}
    assert auth.put("/api/me", json=value).status_code == 200
    me = auth.get("/api/me").json()
    assert all(me[k] == v for k, v in value.items())
    assert auth.put("/api/me", json={"bio": "x" * 501, "goal": "a"}).status_code == 422
    assert auth.put("/api/me/policy", json={"reserve": -1, "daily_budget": 10}).status_code == 422
    assert auth.post("/api/me/action", json={"type": "eat", "quantity": 99}).status_code == 422
    assert (
        auth.post("/api/me/action", json={"type": "eat", "user_id": "zhangguo"}).status_code == 422
    )
    assert auth.get("/api/catalog").json()["rules"]["fiscal"]["daily_surplus_rate"] == 0.05
    assert isinstance(auth.get("/api/events?kind=levy").json(), list)


def test_backup_script_success_and_failed_dump_preserves_previous(tmp_path):
    # Exercises orchestration with stub executables, not PostgreSQL restore validity.
    bin_dir, backup = tmp_path / "bin", tmp_path / "backup"
    bin_dir.mkdir()
    backup.mkdir()
    dump = bin_dir / "pg_dump"
    dump.write_text(
        '#!/bin/sh\nfor arg do case "$arg" in --file=*) printf test > "${arg#--file=}";; esac; done\n'
    )
    restore = bin_dir / "pg_restore"
    restore.write_text("#!/bin/sh\nexit 0\n")
    for file in [dump, restore]:
        file.chmod(0o755)
    env = {
        **os.environ,
        "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"],
        "BACKUP_DIR": str(backup),
        "BACKUP_ONCE": "1",
    }
    script = Path(__file__).resolve().parents[2] / "scripts/backup/postgres.sh"
    subprocess.run(["sh", str(script)], env=env, check=True, capture_output=True)
    saved = list(backup.glob("*.dump"))
    assert len(saved) == 1 and (backup / "last-success").exists()
    marker = (backup / "last-success").read_bytes()
    dump.write_text("#!/bin/sh\nexit 1\n")
    result = subprocess.run(["sh", str(script)], env=env, capture_output=True)
    assert result.returncode == 1
    assert saved[0].read_text() == "test" and not list(backup.glob("*.partial"))
    assert (backup / "last-success").read_bytes() == marker
