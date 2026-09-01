from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.team import Team, TeamMember
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(creds.credentials, settings.secret_key, algorithms=[settings.algorithm])
        subject = payload.get("sub")
        exp = payload.get("exp")
        if subject is None:
            raise JWTError()
        if exp is not None and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise JWTError()
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user = db.get(User, int(subject))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def user_is_team_member(db: Session, user_id: int, team_id: int) -> bool:
    return (
        db.scalar(
            select(TeamMember.id).where(TeamMember.user_id == user_id, TeamMember.team_id == team_id)
        )
        is not None
    )


def require_team_member(db: Session, team_id: int, user_id: int) -> Team:
    team = db.get(Team, team_id)
    if team is None or not user_is_team_member(db, user_id, team.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this team")
    return team


def get_current_team(
    x_team_id: Annotated[int | None, Header()] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Team:
    if x_team_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-Team-Id header is required")
    return require_team_member(db, x_team_id, user.id)
