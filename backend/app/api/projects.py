from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_team, get_current_user
from app.models.project import Project, TimeEntry
from app.models.team import Team
from app.models.user import User
from app.schemas.project import (
    EntryCreate,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
    SessionOut,
    TimeEntryOut,
    TimerStop,
)
from app.services.project_time import (
    add_manual_entry,
    begin_timer,
    entry_out,
    list_finished_entries,
    list_team_projects,
    pause_timer,
    project_view,
    require_open_session,
    server_now,
    session_out,
    stop_timer,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _get_team_project(db: Session, project_id: int, team: Team) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _commit_timer(
    db: Session,
    user: User,
    project: Project,
    action: Callable[[Session, User, Project], TimeEntry],
) -> TimeEntry:
    project_id = project.id
    team_id = project.team_id
    try:
        entry = action(db, user, project)
        db.commit()
    except IntegrityError:
        db.rollback()
        team = db.get(Team, team_id)
        if team is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found") from None
        entry = action(db, user, _get_team_project(db, project_id, team))
        db.commit()
    db.refresh(entry)
    return entry


@router.get("", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> list[ProjectOut]:
    return list_team_projects(db, team.id, user)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    project = Project(team_id=team.id, name=body.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_view(db, project, user)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    return project_view(db, _get_team_project(db, project_id, team), user)


@router.patch("/{project_id}", response_model=ProjectOut)
def rename_project(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> ProjectOut:
    project = _get_team_project(db, project_id, team)
    project.name = body.name
    db.commit()
    db.refresh(project)
    return project_view(db, project, user)


@router.get("/{project_id}/entries", response_model=list[TimeEntryOut])
def list_entries(
    project_id: int,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> list[TimeEntryOut]:
    project = _get_team_project(db, project_id, team)
    return [entry_out(entry) for entry in list_finished_entries(db, user, project)]


@router.post("/{project_id}/entries", response_model=TimeEntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    project_id: int,
    body: EntryCreate,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> TimeEntryOut:
    project = _get_team_project(db, project_id, team)
    entry = add_manual_entry(db, user, project, body)
    db.commit()
    db.refresh(entry)
    return entry_out(entry)


@router.delete("/{project_id}/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    project_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> None:
    project = _get_team_project(db, project_id, team)
    entry = db.get(TimeEntry, entry_id)
    if entry is None or entry.user_id != user.id or entry.project_id != project.id or entry.ended_at is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    db.delete(entry)
    db.commit()


@router.get("/{project_id}/timer", response_model=SessionOut)
def get_timer(
    project_id: int,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> SessionOut:
    project = _get_team_project(db, project_id, team)
    return session_out(require_open_session(db, user.id, project.id), server_now())


@router.post("/{project_id}/timer/start", response_model=SessionOut)
def start_timer(
    project_id: int,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> SessionOut:
    project = _get_team_project(db, project_id, team)
    entry = _commit_timer(db, user, project, begin_timer)
    return session_out(entry, server_now())


@router.post("/{project_id}/timer/pause", response_model=SessionOut)
def pause_timer_route(
    project_id: int,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> SessionOut:
    project = _get_team_project(db, project_id, team)
    entry = pause_timer(db, user, project)
    db.commit()
    db.refresh(entry)
    return session_out(entry, server_now())


@router.post("/{project_id}/timer/stop", response_model=TimeEntryOut)
def stop_timer_route(
    project_id: int,
    body: TimerStop | None = None,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> TimeEntryOut:
    project = _get_team_project(db, project_id, team)
    note = body.note if body is not None else None
    entry = stop_timer(db, user, project, note)
    db.commit()
    db.refresh(entry)
    return entry_out(entry)
