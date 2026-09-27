from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

GOOGLE_OAUTH_STATE_PURPOSE = "google_oauth_state"
GOOGLE_OAUTH_STATE_MINUTES = 10


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": subject, "exp": expire}, settings.secret_key, algorithm=settings.algorithm)


def create_google_oauth_state() -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=GOOGLE_OAUTH_STATE_MINUTES)
    return jwt.encode(
        {
            "purpose": GOOGLE_OAUTH_STATE_PURPOSE,
            "nonce": str(uuid4()),
            "exp": expire,
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def verify_google_oauth_state(state: str) -> bool:
    try:
        payload = jwt.decode(state, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return False
    return payload.get("purpose") == GOOGLE_OAUTH_STATE_PURPOSE
