from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import seed_display_name, settings
from app.core.security import hash_password
from app.models.team import Team, TeamMember
from app.models.user import User
from app.seeds.context import DevSeedContext, SECOND_TEAM_NAME

DEFAULT_TEAM_NAME = "M2 Solution"


def seed_staff() -> None:
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        _ensure_staff(db, reset_passwords=False)
        db.commit()
    finally:
        db.close()


def seed_staff_dev(db: Session, ctx: DevSeedContext) -> None:
    users = _ensure_staff(db, reset_passwords=True)
    ctx.primary_user = users[0] if users else None
    ctx.secondary_user = users[1] if len(users) > 1 else None

    team = db.scalar(select(Team).where(Team.name == DEFAULT_TEAM_NAME).order_by(Team.id))
    if team is None:
        team = Team(name=DEFAULT_TEAM_NAME)
        db.add(team)
        db.flush()
    ctx.main_team = team

    second = db.scalar(select(Team).where(Team.name == SECOND_TEAM_NAME))
    if second is None:
        second = Team(name=SECOND_TEAM_NAME)
        db.add(second)
        db.flush()
    ctx.second_team = second

    if ctx.primary_user:
        _ensure_membership(db, team.id, ctx.primary_user.id)
        _ensure_membership(db, second.id, ctx.primary_user.id)
    if ctx.secondary_user:
        _ensure_membership(db, team.id, ctx.secondary_user.id)


def _ensure_staff(db: Session, *, reset_passwords: bool) -> list[User]:
    team = db.scalar(select(Team).where(Team.name == DEFAULT_TEAM_NAME).order_by(Team.id))
    if team is None:
        team = Team(name=DEFAULT_TEAM_NAME)
        db.add(team)
        db.flush()

    users: list[User] = []
    pwd_hash = hash_password(settings.seed_password)
    for email in settings.seed_email_list:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                password_hash=pwd_hash,
                full_name=seed_display_name(email),
            )
            db.add(user)
            db.flush()
        elif reset_passwords:
            user.password_hash = pwd_hash
            user.full_name = seed_display_name(email)
            db.add(user)
        users.append(user)
        _ensure_membership(db, team.id, user.id)
    return users


def _ensure_membership(db: Session, team_id: int, user_id: int) -> None:
    membership = db.scalar(
        select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
    )
    if membership is None:
        db.add(TeamMember(team_id=team_id, user_id=user_id))
