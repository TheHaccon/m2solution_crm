#!/usr/bin/env python3
"""Copy CRM tables from SQLite into Postgres. Skip if the dest already has users."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _candidate in (_ROOT / "backend", Path("/app")):
    if (_candidate / "app").is_dir():
        sys.path.insert(0, str(_candidate))
        break

from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import Client, Invoice, InvoiceLineItem, InvoiceView, Meeting, User

TABLES: Sequence[type] = (User, Client, Invoice, InvoiceLineItem, InvoiceView, Meeting)


def _clone(model: type, obj: object) -> object:
    data = {col.name: getattr(obj, col.name) for col in model.__table__.columns}
    return model(**data)


def _count(session: Session, model: type) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def _reset_sequences(session: Session) -> None:
    for model in TABLES:
        table = model.__tablename__
        session.execute(
            text(
                f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                f"COALESCE((SELECT MAX(id) FROM {table}), 1), "
                f"(SELECT MAX(id) FROM {table}) IS NOT NULL)"
            )
        )


def main() -> int:
    source_url = os.environ.get("SOURCE_DATABASE_URL")
    dest_url = os.environ.get("DEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not source_url or not dest_url:
        print("Set SOURCE_DATABASE_URL and DATABASE_URL (or DEST_DATABASE_URL).", file=sys.stderr)
        return 1
    if source_url.startswith("postgresql") and dest_url.startswith("sqlite"):
        print("Refusing to copy Postgres into SQLite.", file=sys.stderr)
        return 1

    source_args = {"check_same_thread": False} if source_url.startswith("sqlite") else {}
    source_engine = create_engine(source_url, connect_args=source_args)
    dest_engine = create_engine(dest_url, pool_pre_ping=True)

    if not inspect(source_engine).has_table("users"):
        print(f"No users table in source ({source_url}); nothing to copy.")
        return 0

    Base.metadata.create_all(bind=dest_engine)
    SourceSession = sessionmaker(bind=source_engine, autoflush=False)
    DestSession = sessionmaker(bind=dest_engine, autoflush=False)

    with SourceSession() as source, DestSession() as dest:
        if _count(dest, User) > 0:
            print("Postgres already has users; skip copy.")
            return 0

        copied: dict[str, int] = {}
        for model in TABLES:
            rows = list(source.scalars(select(model)))
            for row in rows:
                dest.add(_clone(model, row))
            copied[model.__tablename__] = len(rows)

        dest.flush()
        _reset_sequences(dest)
        dest.commit()

    print("Copied: " + ", ".join(f"{name}={n}" for name, n in copied.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
