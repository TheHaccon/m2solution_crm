from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.client import Client
from app.models.meeting import Meeting
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingOut, MeetingUpdate
from app.services.invoices import meeting_to_out

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


def _load_meeting(db: Session, meeting_id: int) -> Meeting:
    meeting = db.scalar(
        select(Meeting).options(selectinload(Meeting.client)).where(Meeting.id == meeting_id)
    )
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


@router.get("", response_model=list[MeetingOut])
def list_meetings(
    client_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[MeetingOut]:
    stmt = select(Meeting).options(selectinload(Meeting.client)).order_by(Meeting.scheduled_at.desc())
    if client_id is not None:
        stmt = stmt.where(Meeting.client_id == client_id)
    return [meeting_to_out(m) for m in db.scalars(stmt).all()]


@router.post("", response_model=MeetingOut, status_code=status.HTTP_201_CREATED)
def create_meeting(
    body: MeetingCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MeetingOut:
    client = db.get(Client, body.client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    meeting = Meeting(
        client_id=body.client_id,
        title=body.title.strip(),
        scheduled_at=body.scheduled_at,
        attendees=body.attendees,
        body=body.body,
    )
    db.add(meeting)
    db.commit()
    return meeting_to_out(_load_meeting(db, meeting.id))


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MeetingOut:
    return meeting_to_out(_load_meeting(db, meeting_id))


@router.patch("/{meeting_id}", response_model=MeetingOut)
def update_meeting(
    meeting_id: int,
    body: MeetingUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MeetingOut:
    meeting = _load_meeting(db, meeting_id)
    data = body.model_dump(exclude_unset=True)
    if "client_id" in data:
        client = db.get(Client, data["client_id"])
        if client is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    if "title" in data and data["title"]:
        data["title"] = data["title"].strip()
    for key, value in data.items():
        setattr(meeting, key, value)
    db.commit()
    return meeting_to_out(_load_meeting(db, meeting.id))


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    meeting = _load_meeting(db, meeting_id)
    db.delete(meeting)
    db.commit()
