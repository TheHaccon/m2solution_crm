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
from app.models import Client, Invoice, InvoiceLineItem, InvoiceView, Meeting, Team, TeamMember, User
from app.models.user import utcnow

TABLES: Sequence[type] = (User, Team, TeamMember, Client, Invoice, InvoiceLineItem, InvoiceView, Meeting)


def _clone(model: type, obj: object, extra: dict | None = None) -> object:
    extra = extra or {}
    data = {}
    for col in model.__table__.columns:
        if col.name in extra:
            data[col.name] = extra[col.name]
        elif hasattr(obj, col.name):
            data[col.name] = getattr(obj, col.name)
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
    source_has_teams = inspect(source_engine).has_table("teams")

    with SourceSession() as source, DestSession() as dest:
        if _count(dest, User) > 0:
            print("Postgres already has users; skip copy.")
            return 0

        copied: dict[str, int] = {}

        for row in source.scalars(select(User)):
            dest.add(_clone(User, row))
        copied["users"] = _count(source, User)
        dest.flush()

        default_team_id: int | None = None
        if source_has_teams:
            for row in source.scalars(select(Team)):
                dest.add(_clone(Team, row))
            copied["teams"] = _count(source, Team)
            dest.flush()
            for row in source.scalars(select(TeamMember)):
                dest.add(_clone(TeamMember, row))
            copied["team_members"] = _count(source, TeamMember)
        else:
            team = Team(name="M2 Solution")
            dest.add(team)
            dest.flush()
            default_team_id = team.id
            for user in dest.scalars(select(User)):
                dest.add(TeamMember(team_id=team.id, user_id=user.id, created_at=utcnow()))
            copied["teams"] = 1
            copied["team_members"] = _count(dest, User)

        dest.flush()
        first_user_id = dest.scalar(select(User.id).order_by(User.id))

        for row in source.scalars(select(Client)):
            extra = {}
            if default_team_id is not None:
                extra["team_id"] = default_team_id
            dest.add(_clone(Client, row, extra))
        copied["clients"] = _count(source, Client)
        dest.flush()

        for row in source.scalars(select(Invoice)):
            extra = {}
            if not hasattr(row, "created_by_id") or getattr(row, "created_by_id", None) is None:
                extra["created_by_id"] = first_user_id
            dest.add(_clone(Invoice, row, extra))
        copied["invoices"] = _count(source, Invoice)

        for model in (InvoiceLineItem, InvoiceView, Meeting):
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
