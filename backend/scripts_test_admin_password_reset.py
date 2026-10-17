"""Focused checks for POST /api/auth/admin/password-reset."""
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password, verify_password
from app.main import app
from app.models.user import User

TARGET_EMAIL = "apr-target@m2solution.com"


def _ensure_user(db, email: str, password: str, full_name: str) -> tuple[User, str | None]:
    """Return (user, previous_hash_or_None_if_created)."""
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(password), full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user, None
    previous = user.password_hash
    user.password_hash = hash_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, previous


def _auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    login = client.post("/api/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def main() -> None:
    actor_email = settings.seed_email_list[0]
    actor_previous: str | None = None
    actor_created = False

    db = SessionLocal()
    try:
        _, actor_previous = _ensure_user(db, actor_email, "staff-pass-1", "Seed Actor")
        actor_created = actor_previous is None
        _ensure_user(db, TARGET_EMAIL, "target-pass-1", "Target")
    finally:
        db.close()

    with TestClient(app) as client:
        actor_headers = _auth_headers(client, actor_email, "staff-pass-1")

        missing = client.post(
            "/api/auth/admin/password-reset",
            headers=actor_headers,
            json={"email": "nobody@m2solution.com", "new_password": "whatever12"},
        )
        assert missing.status_code == 404, missing.text

        same = client.post(
            "/api/auth/admin/password-reset",
            headers=actor_headers,
            json={"email": TARGET_EMAIL, "new_password": "target-pass-1"},
        )
        assert same.status_code == 400, same.text

        ok = client.post(
            "/api/auth/admin/password-reset",
            headers=actor_headers,
            json={"email": TARGET_EMAIL, "new_password": "target-pass-2"},
        )
        assert ok.status_code == 204, ok.text

        self_ok = client.post(
            "/api/auth/admin/password-reset",
            headers=actor_headers,
            json={"email": actor_email, "new_password": "staff-pass-2"},
        )
        assert self_ok.status_code == 204, self_ok.text

        login_target = client.post(
            "/api/auth/login",
            json={"email": TARGET_EMAIL, "password": "target-pass-2"},
        )
        assert login_target.status_code == 200, login_target.text

        login_actor = client.post(
            "/api/auth/login",
            json={"email": actor_email, "password": "staff-pass-2"},
        )
        assert login_actor.status_code == 200, login_actor.text

    db = SessionLocal()
    try:
        target = db.scalar(select(User).where(User.email == TARGET_EMAIL))
        assert target is not None
        assert verify_password("target-pass-2", target.password_hash)
        db.delete(target)

        actor = db.scalar(select(User).where(User.email == actor_email))
        assert actor is not None
        if actor_created:
            db.delete(actor)
        elif actor_previous is not None:
            actor.password_hash = actor_previous
            db.add(actor)
        db.commit()
    finally:
        db.close()

    print("staff password reset checks passed")


if __name__ == "__main__":
    main()
