"""Focused checks for Google staff sign-in (issues #3–#5)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import create_google_oauth_state, hash_password
from app.main import app
from app.models.user import User

STAFF_EMAIL = "google-staff@m2solution.com"
STAFF_PASSWORD = "staff-pass-1"
UNKNOWN_EMAIL = "google-unknown@m2solution.com"


@contextmanager
def _google_settings(
    *,
    client_id: str = "test-client-id",
    client_secret: str = "test-client-secret",
    redirect_uri: str = "http://localhost:5173/api/auth/google/callback",
    public_app_url: str = "http://localhost:5173",
) -> Iterator[None]:
    previous = (
        settings.google_client_id,
        settings.google_client_secret,
        settings.google_redirect_uri,
        settings.public_app_url,
    )
    settings.google_client_id = client_id
    settings.google_client_secret = client_secret
    settings.google_redirect_uri = redirect_uri
    settings.public_app_url = public_app_url
    try:
        yield
    finally:
        (
            settings.google_client_id,
            settings.google_client_secret,
            settings.google_redirect_uri,
            settings.public_app_url,
        ) = previous


def _ensure_user(db, email: str, password: str, full_name: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(password), full_name=full_name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    user.password_hash = hash_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _mock_httpx_client(*, email: str, email_verified: bool = True, token_ok: bool = True) -> MagicMock:
    token_res = MagicMock()
    token_res.status_code = 200 if token_ok else 400
    token_res.json.return_value = {"access_token": "ya29.test"} if token_ok else {"error": "invalid_grant"}

    userinfo_res = MagicMock()
    userinfo_res.status_code = 200
    userinfo_res.json.return_value = {"email": email, "email_verified": email_verified}

    client = MagicMock()
    client.__enter__.return_value = client
    client.__exit__.return_value = False
    client.post.return_value = token_res
    client.get.return_value = userinfo_res
    return client


def main() -> None:
    db = SessionLocal()
    try:
        staff = _ensure_user(db, STAFF_EMAIL, STAFF_PASSWORD, "Google Staff")
        staff_id = staff.id
        before_count = db.scalar(select(func.count()).select_from(User)) or 0
    finally:
        db.close()

    with TestClient(app, follow_redirects=False) as client:
        # Password login still works
        password_login = client.post(
            "/api/auth/login",
            json={"email": STAFF_EMAIL, "password": STAFF_PASSWORD},
        )
        assert password_login.status_code == 200, password_login.text
        assert "access_token" in password_login.json()

        # Missing Google config → 503
        with _google_settings(client_id="", client_secret="", redirect_uri=""):
            missing = client.get("/api/auth/google/start")
            assert missing.status_code == 503, missing.text

        with _google_settings():
            start = client.get("/api/auth/google/start")
            assert start.status_code == 302, start.text
            location = start.headers.get("location", "")
            assert location.startswith("https://accounts.google.com/o/oauth2/v2/auth"), location
            assert "client_id=test-client-id" in location
            assert "response_type=code" in location
            assert "scope=openid" in location

            state = create_google_oauth_state()

            with patch("app.api.auth.httpx.Client", return_value=_mock_httpx_client(email=STAFF_EMAIL)):
                matched = client.get(
                    "/api/auth/google/callback",
                    params={"code": "auth-code", "state": state},
                )
            assert matched.status_code == 302, matched.text
            matched_loc = matched.headers.get("location", "")
            assert matched_loc.startswith("http://localhost:5173/login?google_token="), matched_loc
            token = matched_loc.split("google_token=", 1)[1]
            me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert me.status_code == 200, me.text
            assert me.json()["email"] == STAFF_EMAIL
            assert me.json()["id"] == staff_id

            state_unknown = create_google_oauth_state()
            with patch("app.api.auth.httpx.Client", return_value=_mock_httpx_client(email=UNKNOWN_EMAIL)):
                unknown = client.get(
                    "/api/auth/google/callback",
                    params={"code": "auth-code", "state": state_unknown},
                )
            assert unknown.status_code == 302, unknown.text
            assert unknown.headers.get("location") == "http://localhost:5173/login?google_error=1"

            state_unverified = create_google_oauth_state()
            with patch(
                "app.api.auth.httpx.Client",
                return_value=_mock_httpx_client(email=STAFF_EMAIL, email_verified=False),
            ):
                unverified = client.get(
                    "/api/auth/google/callback",
                    params={"code": "auth-code", "state": state_unverified},
                )
            assert unverified.status_code == 302, unverified.text
            assert unverified.headers.get("location") == "http://localhost:5173/login?google_error=1"

            bad_state = client.get(
                "/api/auth/google/callback",
                params={"code": "auth-code", "state": "not-a-valid-state"},
            )
            assert bad_state.status_code == 302, bad_state.text
            assert bad_state.headers.get("location") == "http://localhost:5173/login?google_error=1"

    db = SessionLocal()
    try:
        after_count = db.scalar(select(func.count()).select_from(User)) or 0
        assert after_count == before_count, "Google unknown email must not insert users"
        unknown = db.scalar(select(User).where(User.email == UNKNOWN_EMAIL))
        assert unknown is None
        staff = db.scalar(select(User).where(User.email == STAFF_EMAIL))
        assert staff is not None
        db.delete(staff)
        db.commit()
    finally:
        db.close()

    print("google sign-in checks passed")


if __name__ == "__main__":
    main()
