"""FastAPI dependencies for session + allowlist gates."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.sessions import read_session_token
from app.auth.users import User, get_user_by_id
from app.config import Settings, get_settings
from app.db import get_session_factory


def get_db(settings: Settings = Depends(get_settings)) -> Generator[Session, None, None]:
    factory = get_session_factory(settings)
    session = factory()
    try:
        yield session
    finally:
        session.close()


def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User | None:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    user_id = read_session_token(token, settings)
    if not user_id:
        return None
    return get_user_by_id(db, user_id, settings)


def require_user(
    user: User | None = Depends(get_optional_user),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """Require a session when AUTH_ENABLED; otherwise allow anonymous."""
    if not settings.auth_enabled:
        return user
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_approved(
    user: User | None = Depends(get_optional_user),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """Gate playground APIs when AUTH_ENABLED; open access when disabled."""
    if not settings.auth_enabled:
        return None
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="Account pending admin approval")
    if user.status in ("denied", "revoked"):
        raise HTTPException(status_code=403, detail=f"Account {user.status}")
    if user.status != "approved":
        raise HTTPException(status_code=403, detail="Account not approved")
    return user


def require_admin(
    user: User | None = Depends(get_optional_user),
    settings: Settings = Depends(get_settings),
) -> User:
    """Admin routes always require an approved admin session (even if playground is open)."""
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=503,
            detail="Admin API unavailable while AUTH_ENABLED=false",
        )
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if user.status != "approved":
        raise HTTPException(status_code=403, detail="Account not approved")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
