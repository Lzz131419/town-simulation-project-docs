#!/usr/bin/env python3
"""Back up SQLite consistently, migrate a second copy, and verify all original rows.

Run with the project virtualenv. Never migrates the source database in place.
Backups contain private application data; keep the generated directory local.
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def quote(identifier):
    return '"' + identifier.replace('"', '""') + '"'


def copy_database(source, target):
    with (
        closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src,
        closing(sqlite3.connect(target)) as dst,
    ):
        src.backup(dst)
    target.chmod(0o600)


def fingerprint(path):
    result = {}
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        tables = db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version' ORDER BY name"
        ).fetchall()
        for (table,) in tables:
            columns = db.execute(f"PRAGMA table_info({quote(table)})").fetchall()
            primary = [c[1] for c in sorted(columns, key=lambda c: c[5]) if c[5]]
            order = ", ".join(map(quote, primary or [c[1] for c in columns]))
            digest, count = hashlib.sha256(), 0
            for row in db.execute(f"SELECT * FROM {quote(table)} ORDER BY {order}"):
                digest.update(repr(tuple(row)).encode("utf-8"))
                digest.update(b"\n")
                count += 1
            result[table] = {"rows": count, "sha256": digest.hexdigest()}
        if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise RuntimeError("SQLite integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("SQLite foreign key check failed")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=ROOT / ".local")
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    folder = Path(
        tempfile.mkdtemp(prefix="schema-rehearsal-", dir=args.output_dir)
    ).resolve()
    backup, migrated = folder / "backup.db", folder / "migrated.db"
    copy_database(source, backup)
    copy_database(backup, migrated)
    before = fingerprint(backup)
    # All application paths resolve consistently, regardless of the caller's cwd.
    os.chdir(ROOT)
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from app.database import Base
    from app.infrastructure.migrations import migrate
    from sqlalchemy import create_engine, text

    from app import models  # noqa: F401

    engine = create_engine("sqlite:///" + str(migrated))
    try:
        migrate(engine)
        after = fingerprint(migrated)
        if before != after:
            raise RuntimeError(
                "Migration changed original table rows; source untouched"
            )
        migrate(engine)
        if fingerprint(migrated) != after:
            raise RuntimeError("Repeated migration changed rows; source untouched")
        with engine.connect() as db:
            if compare_metadata(MigrationContext.configure(db), Base.metadata):
                raise RuntimeError("Migrated schema differs from application models")
            revision = db.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar()
    finally:
        engine.dispose()
    report = {
        "source": str(source),
        "backup": str(backup),
        "migrated_copy": str(migrated),
        "revision": revision,
        "original_rows_unchanged": True,
        "repeat_upgrade_unchanged": True,
        "schema_matches_models": True,
        "integrity_check": "ok",
        "foreign_key_check": "ok",
        "tables": before,
    }
    (folder / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
