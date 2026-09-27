"""Focused checks for POST /api/auth/admin/password-reset (issue #1)."""
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password, verify_password
from app.main import app
from app.models.user import User

ADMIN_EMAIL = "admin@m2solution.com"
TARGET_EMAIL = "apr-target@m2solution.com"
OTHER_EMAIL = "apr-other@m2solution.com"


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
    admin_previous: str | None = None
    admin_created = False

    db = SessionLocal()
    try:
        _, admin_previous = _ensure_user(db, ADMIN_EMAIL, "admin-pass-1", "Admin")
        admin_created = admin_previous is None
        _ensure_user(db, TARGET_EMAIL, "target-pass-1", "Target")
        _ensure_user(db, OTHER_EMAIL, "other-pass-1", "Other")
    finally:
        db.close()

    with TestClient(app) as client:
        admin_headers = _auth_headers(client, ADMIN_EMAIL, "admin-pass-1")
        other_headers = _auth_headers(client, OTHER_EMAIL, "other-pass-1")

        forbidden = client.post(
            "/api/auth/admin/password-reset",
            headers=other_headers,
            json={"email": TARGET_EMAIL, "new_password": "target-pass-2"},
        )
        assert forbidden.status_code == 403, forbidden.text

        missing = client.post(
            "/api/auth/admin/password-reset",
            headers=admin_headers,
            json={"email": "nobody@m2solution.com", "new_password": "whatever12"},
        )
        assert missing.status_code == 404, missing.text

        same = client.post(
            "/api/auth/admin/password-reset",
            headers=admin_headers,
            json={"email": TARGET_EMAIL, "new_password": "target-pass-1"},
        )
        assert same.status_code == 400, same.text

        ok = client.post(
            "/api/auth/admin/password-reset",
            headers=admin_headers,
            json={"email": TARGET_EMAIL, "new_password": "target-pass-2"},
        )
        assert ok.status_code == 204, ok.text

        self_ok = client.post(
            "/api/auth/admin/password-reset",
            headers=admin_headers,
            json={"email": ADMIN_EMAIL, "new_password": "admin-pass-2"},
        )
        assert self_ok.status_code == 204, self_ok.text

        login_target = client.post(
            "/api/auth/login",
            json={"email": TARGET_EMAIL, "password": "target-pass-2"},
        )
        assert login_target.status_code == 200, login_target.text

        login_admin = client.post(
            "/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "admin-pass-2"},
        )
        assert login_admin.status_code == 200, login_admin.text

    db = SessionLocal()
    try:
        target = db.scalar(select(User).where(User.email == TARGET_EMAIL))
        assert target is not None
        assert verify_password("target-pass-2", target.password_hash)
        other = db.scalar(select(User).where(User.email == OTHER_EMAIL))
        if other is not None:
            db.delete(other)
        db.delete(target)

        admin = db.scalar(select(User).where(User.email == ADMIN_EMAIL))
        assert admin is not None
        if admin_created:
            db.delete(admin)
        elif admin_previous is not None:
            admin.password_hash = admin_previous
            db.add(admin)
        db.commit()
    finally:
        db.close()

    print("admin password reset checks passed")


if __name__ == "__main__":
    main()
