from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user, require_team_member
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamDetailOut, TeamMemberAdd, TeamMemberOut, TeamOut, TeamUpdate

router = APIRouter(prefix="/api/teams", tags=["teams"])


def _team_detail(team: Team) -> TeamDetailOut:
    return TeamDetailOut(
        id=team.id,
        name=team.name,
        created_at=team.created_at,
        members=[
            TeamMemberOut(user_id=m.user_id, email=m.user.email, full_name=m.user.full_name)
            for m in team.members
        ],
    )


def _load_team(db: Session, team_id: int, user: User) -> Team:
    team = db.scalar(
        select(Team)
        .options(selectinload(Team.members).selectinload(TeamMember.user))
        .where(Team.id == team_id)
    )
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    require_team_member(db, team.id, user.id)
    return team


@router.get("", response_model=list[TeamOut])
def list_teams(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Team]:
    stmt = (
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user.id)
        .order_by(Team.name)
    )
    return list(db.scalars(stmt).all())


@router.post("", response_model=TeamDetailOut, status_code=status.HTTP_201_CREATED)
def create_team(
    body: TeamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TeamDetailOut:
    team = Team(name=body.name.strip())
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id))
    db.commit()
    return _team_detail(_load_team(db, team.id, user))


@router.get("/{team_id}", response_model=TeamDetailOut)
def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TeamDetailOut:
    return _team_detail(_load_team(db, team_id, user))


@router.patch("/{team_id}", response_model=TeamDetailOut)
def update_team(
    team_id: int,
    body: TeamUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TeamDetailOut:
    team = _load_team(db, team_id, user)
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        team.name = data["name"].strip()
    db.commit()
    return _team_detail(_load_team(db, team.id, user))


@router.post("/{team_id}/members", response_model=TeamDetailOut)
def add_member(
    team_id: int,
    body: TeamMemberAdd,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TeamDetailOut:
    team = _load_team(db, team_id, user)
    target = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    existing = db.scalar(
        select(TeamMember.id).where(TeamMember.team_id == team.id, TeamMember.user_id == target.id)
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Already a member")
    db.add(TeamMember(team_id=team.id, user_id=target.id))
    db.commit()
    return _team_detail(_load_team(db, team.id, user))


@router.delete("/{team_id}/members/{user_id}", response_model=TeamDetailOut)
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TeamDetailOut:
    team = _load_team(db, team_id, user)
    count = db.scalar(select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team.id)) or 0
    if count <= 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last member")
    member = db.scalar(select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == user_id))
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    db.delete(member)
    db.commit()
    return _team_detail(_load_team(db, team.id, user))
