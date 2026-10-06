from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel


def _strip_project_name(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("name must not be blank")
    if len(stripped) > 255:
        raise ValueError("name must be at most 255 characters")
    return stripped


def _positive_seconds(value: int) -> int:
    if value <= 0:
        raise ValueError("duration must be greater than zero")
    return value


def _empty_note(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


ProjectName = Annotated[str, AfterValidator(_strip_project_name)]
DurationSeconds = Annotated[int, AfterValidator(_positive_seconds)]
OptionalNote = Annotated[str | None, AfterValidator(_empty_note)]


class ProjectCreate(BaseModel):
    name: ProjectName


class ProjectUpdate(BaseModel):
    name: ProjectName


class EntryCreate(BaseModel):
    work_date: date | None = None
    duration_seconds: DurationSeconds
    note: OptionalNote = None


class TimerStop(BaseModel):
    note: OptionalNote = None


class SessionOut(BaseModel):
    id: int
    project_id: int
    status: Literal["running", "paused"]
    accumulated_seconds: int
    segment_started_at: datetime | None
    server_now: datetime


class ProjectOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    my_finished_seconds: int
    server_now: datetime
    server_today: date
    my_session: SessionOut | None


class TimeEntryOut(BaseModel):
    id: int
    project_id: int
    source: Literal["manual", "timer"]
    work_date: date
    duration_seconds: int
    note: str | None
    ended_at: datetime
