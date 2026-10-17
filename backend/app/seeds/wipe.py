from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.core.database import Base, engine

ALLOWED_DEV_DATABASE = "crm_dev"


def database_name_from_url(url: str) -> str:
    return make_url(url).database or ""


def assert_dev_database() -> None:
    name = database_name_from_url(settings.database_url)
    if name == ALLOWED_DEV_DATABASE:
        return
    raise SystemExit(
        f"Refusing reseed: DATABASE_URL must target database {ALLOWED_DEV_DATABASE!r}, got {name!r}."
    )


def wipe_database_tables() -> None:
    tables = [
        t.name
        for t in Base.metadata.sorted_tables
        if t.name != "alembic_version"
    ]
    if not tables:
        return
    quoted = ", ".join(f'"{t}"' for t in tables)
    sql = f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"
    with engine.begin() as conn:
        conn.execute(text(sql))


def wipe_files_root(*, skip: bool = False) -> None:
    if skip:
        return
    root = Path(settings.files_root)
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
        return
    for child in root.iterdir():
        if child.is_file():
            child.unlink(missing_ok=True)
        elif child.is_dir():
            shutil.rmtree(child)
