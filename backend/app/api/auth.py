import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_google_oauth_state,
    hash_password,
    verify_google_oauth_state,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    AdminPasswordResetRequest,
    LoginRequest,
    PasswordChangeRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)

ADMIN_EMAIL = "admin@m2solution.com"
GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user



@router.post("/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: PasswordChangeRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    if body.new_password == body.current_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")
    user.password_hash = hash_password(body.new_password)
    db.add(user)
    db.commit()


@router.post("/admin/password-reset", status_code=status.HTTP_204_NO_CONTENT)
def admin_password_reset(
    body: AdminPasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    if current_user.email.lower() != ADMIN_EMAIL:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    target = db.scalar(select(User).where(User.email == body.email.lower()))
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if verify_password(body.new_password, target.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different")
    target.password_hash = hash_password(body.new_password)
    db.add(target)
    db.commit()


def _google_login_redirect(
    *,
    token: str | None = None,
    error: bool = False,
    reason: str | None = None,
) -> RedirectResponse:
    base = settings.public_app_url.rstrip("/")
    if token:
        return RedirectResponse(url=f"{base}/login?google_token={token}", status_code=status.HTTP_302_FOUND)
    if error:
        query = urlencode({"google_error": "1", **({"google_reason": reason} if reason else {})})
        logger.warning("google sign-in failed: %s", reason or "unspecified")
        return RedirectResponse(url=f"{base}/login?{query}", status_code=status.HTTP_302_FOUND)
    return RedirectResponse(url=f"{base}/login", status_code=status.HTTP_302_FOUND)


@router.get("/google/start")
def google_start() -> RedirectResponse:
    if not settings.google_oauth_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured",
        )
    state = create_google_oauth_state()
    params = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "online",
            "include_granted_scopes": "true",
            "state": state,
            "prompt": "select_account",
        }
    )
    return RedirectResponse(url=f"{GOOGLE_AUTHORIZE_URL}?{params}", status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
def google_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if not settings.google_oauth_configured:
        return _google_login_redirect(error=True, reason="not_configured")
    if not code or not state or not verify_google_oauth_state(state):
        return _google_login_redirect(error=True, reason="bad_state")

    try:
        with httpx.Client(timeout=15.0) as client:
            token_res = client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_res.status_code != 200:
                detail = ""
                try:
                    detail = str(token_res.json().get("error") or "")
                except ValueError:
                    detail = ""
                return _google_login_redirect(error=True, reason=f"token_{detail or token_res.status_code}")
            token_payload = token_res.json()
            access_token = token_payload.get("access_token")
            if not access_token:
                return _google_login_redirect(error=True, reason="no_access_token")
            userinfo_res = client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_res.status_code != 200:
                return _google_login_redirect(error=True, reason="userinfo")
            userinfo = userinfo_res.json()
    except httpx.HTTPError:
        return _google_login_redirect(error=True, reason="network")

    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified")
    verified = email_verified is True or email_verified == "true"
    if not email or not verified:
        return _google_login_redirect(error=True, reason="unverified")

    normalized = str(email).strip().lower()
    user = db.scalar(select(User).where(User.email == normalized))
    if user is None:
        logger.warning("google sign-in email not in staff list: %s", normalized)
        return _google_login_redirect(error=True, reason="not_staff")

    return _google_login_redirect(token=create_access_token(str(user.id)))
