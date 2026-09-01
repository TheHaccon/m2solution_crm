from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_team, get_current_user
from app.models.client import Client
from app.models.invoice import Invoice
from app.models.team import Team
from app.models.user import User
from app.schemas.client import ClientCreate, ClientOut, ClientUpdate

router = APIRouter(prefix="/api/clients", tags=["clients"])


def _get_team_client(db: Session, client_id: int, team: Team) -> Client:
    client = db.get(Client, client_id)
    if client is None or client.team_id != team.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    return client


@router.get("", response_model=list[ClientOut])
def list_clients(
    q: str | None = None,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    _: User = Depends(get_current_user),
) -> list[Client]:
    stmt = select(Client).where(Client.team_id == team.id).order_by(Client.name)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Client.name.ilike(like), Client.email.ilike(like)))
    return list(db.scalars(stmt).all())


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    body: ClientCreate,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    _: User = Depends(get_current_user),
) -> Client:
    client = Client(
        team_id=team.id,
        name=body.name.strip(),
        email=str(body.email) if body.email else None,
        phone=body.phone,
        address=body.address,
        notes=body.notes,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    _: User = Depends(get_current_user),
) -> Client:
    return _get_team_client(db, client_id, team)


@router.patch("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: int,
    body: ClientUpdate,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    _: User = Depends(get_current_user),
) -> Client:
    client = _get_team_client(db, client_id, team)
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"])
    if "name" in data and data["name"]:
        data["name"] = data["name"].strip()
    for key, value in data.items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    team: Team = Depends(get_current_team),
    user: User = Depends(get_current_user),
) -> None:
    client = _get_team_client(db, client_id, team)
    other = db.scalar(
        select(Invoice.id)
        .where(Invoice.client_id == client.id, Invoice.created_by_id != user.id)
        .limit(1)
    )
    if other is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete this client while teammates have invoices for it",
        )
    db.delete(client)
    db.commit()
