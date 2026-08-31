from datetime import datetime

from pydantic import BaseModel, Field


class MeetingCreate(BaseModel):
    client_id: int
    title: str = Field(min_length=1, max_length=255)
    scheduled_at: datetime
    attendees: str | None = None
    body: str | None = None


class MeetingUpdate(BaseModel):
    client_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    scheduled_at: datetime | None = None
    attendees: str | None = None
    body: str | None = None


class MeetingOut(BaseModel):
    id: int
    client_id: int
    client_name: str
    title: str
    scheduled_at: datetime
    attendees: str | None
    body: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
