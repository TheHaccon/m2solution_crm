from datetime import datetime, timezone
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project, TimeEntry
from app.models.user import User, utcnow
from app.schemas.project import EntryCreate, ProjectOut, SessionOut, TimeEntryOut

SOURCE_MANUAL = "manual"
SOURCE_TIMER = "timer"


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def server_now() -> datetime:
    return as_utc(utcnow())


def _as_utc_optional(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return as_utc(value)


def _close_segment(entry: TimeEntry, now: datetime) -> None:
    started = entry.segment_started_at
    if started is None:
        return
    elapsed = int((as_utc(now) - as_utc(started)).total_seconds())
    if elapsed < 0:
        elapsed = 0
    entry.duration_seconds = entry.duration_seconds + elapsed
    entry.segment_started_at = None


def _open_rows(db: Session, user_id: int) -> list[TimeEntry]:
    stmt = (
        select(TimeEntry)
        .where(TimeEntry.user_id == user_id, TimeEntry.ended_at.is_(None))
        .order_by(TimeEntry.id)
    )
    if db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update()
    return list(db.scalars(stmt).all())


def open_session(db: Session, user_id: int, project_id: int) -> TimeEntry | None:
    return db.scalar(
        select(TimeEntry).where(
            TimeEntry.user_id == user_id,
            TimeEntry.project_id == project_id,
            TimeEntry.ended_at.is_(None),
        )
    )


def require_open_session(db: Session, user_id: int, project_id: int) -> TimeEntry:
    row = open_session(db, user_id, project_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No open session")
    return row


def _session_status(entry: TimeEntry) -> Literal["running", "paused"]:
    if entry.segment_started_at is not None:
        return "running"
    return "paused"


def _entry_source(entry: TimeEntry) -> Literal["manual", "timer"]:
    if entry.source == SOURCE_MANUAL:
        return "manual"
    if entry.source == SOURCE_TIMER:
        return "timer"
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")


def session_out(entry: TimeEntry, now: datetime) -> SessionOut:
    return SessionOut(
        id=entry.id,
        project_id=entry.project_id,
        status=_session_status(entry),
        accumulated_seconds=entry.duration_seconds,
        segment_started_at=_as_utc_optional(entry.segment_started_at),
        server_now=as_utc(now),
    )


def entry_out(entry: TimeEntry) -> TimeEntryOut:
    if entry.ended_at is None or entry.work_date is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return TimeEntryOut(
        id=entry.id,
        project_id=entry.project_id,
        source=_entry_source(entry),
        work_date=entry.work_date,
        duration_seconds=entry.duration_seconds,
        note=entry.note,
        ended_at=as_utc(entry.ended_at),
    )


def project_views(db: Session, projects: list[Project], user: User) -> list[ProjectOut]:
    now = as_utc(utcnow())
    today = now.date()
    if not projects:
        return []
    ids = [project.id for project in projects]
    totals = {
        project_id: int(total or 0)
        for project_id, total in db.execute(
            select(TimeEntry.project_id, func.sum(TimeEntry.duration_seconds))
            .where(
                TimeEntry.user_id == user.id,
                TimeEntry.project_id.in_(ids),
                TimeEntry.ended_at.is_not(None),
            )
            .group_by(TimeEntry.project_id)
        ).all()
    }
    sessions = {
        row.project_id: row
        for row in db.scalars(
            select(TimeEntry).where(
                TimeEntry.user_id == user.id,
                TimeEntry.project_id.in_(ids),
                TimeEntry.ended_at.is_(None),
            )
        ).all()
    }
    views: list[ProjectOut] = []
    for project in projects:
        session = sessions.get(project.id)
        views.append(
            ProjectOut(
                id=project.id,
                name=project.name,
                created_at=as_utc(project.created_at),
                updated_at=as_utc(project.updated_at),
                my_finished_seconds=totals.get(project.id, 0),
                server_now=now,
                server_today=today,
                my_session=session_out(session, now) if session is not None else None,
            )
        )
    return views


def project_view(db: Session, project: Project, user: User) -> ProjectOut:
    return project_views(db, [project], user)[0]


def list_team_projects(db: Session, team_id: int, user: User) -> list[ProjectOut]:
    projects = list(
        db.scalars(select(Project).where(Project.team_id == team_id).order_by(Project.name, Project.id)).all()
    )
    return project_views(db, projects, user)


def add_manual_entry(db: Session, user: User, project: Project, body: EntryCreate) -> TimeEntry:
    now = as_utc(utcnow())
    entry = TimeEntry(
        user_id=user.id,
        project_id=project.id,
        source=SOURCE_MANUAL,
        work_date=body.work_date or now.date(),
        duration_seconds=body.duration_seconds,
        segment_started_at=None,
        ended_at=now,
        note=body.note,
    )
    db.add(entry)
    db.flush()
    return entry


def list_finished_entries(db: Session, user: User, project: Project) -> list[TimeEntry]:
    return list(
        db.scalars(
            select(TimeEntry)
            .where(
                TimeEntry.user_id == user.id,
                TimeEntry.project_id == project.id,
                TimeEntry.ended_at.is_not(None),
            )
            .order_by(TimeEntry.ended_at.desc(), TimeEntry.id.desc())
        ).all()
    )


def begin_timer(db: Session, user: User, project: Project) -> TimeEntry:
    """Pause any other running session for this user, then start or resume this project.

    The pause update is flushed before a new running row is inserted so the partial
    unique index never sees two running rows. Callers commit this as one transaction.
    """
    now = as_utc(utcnow())
    open_rows = _open_rows(db, user.id)
    others_running = [
        row for row in open_rows if row.project_id != project.id and row.segment_started_at is not None
    ]
    for row in others_running:
        _close_segment(row, now)
    if others_running:
        db.flush()

    mine = next((row for row in open_rows if row.project_id == project.id), None)
    if mine is not None:
        if mine.segment_started_at is None:
            mine.segment_started_at = now
        return mine

    created = TimeEntry(
        user_id=user.id,
        project_id=project.id,
        source=SOURCE_TIMER,
        work_date=None,
        duration_seconds=0,
        segment_started_at=now,
        ended_at=None,
        note=None,
    )
    db.add(created)
    db.flush()
    return created


def pause_timer(db: Session, user: User, project: Project) -> TimeEntry:
    row = require_open_session(db, user.id, project.id)
    if row.segment_started_at is not None:
        _close_segment(row, as_utc(utcnow()))
    return row


def stop_timer(db: Session, user: User, project: Project) -> TimeEntry:
    row = require_open_session(db, user.id, project.id)
    now = as_utc(utcnow())
    if row.segment_started_at is not None:
        _close_segment(row, now)
    row.ended_at = now
    row.segment_started_at = None
    row.work_date = now.date()
    return row
