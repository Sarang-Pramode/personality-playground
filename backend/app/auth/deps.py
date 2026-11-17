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


def require_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_approved(user: User = Depends(require_user)) -> User:
    if user.status == "pending":
        raise HTTPException(status_code=403, detail="Account pending admin approval")
    if user.status in ("denied", "revoked"):
        raise HTTPException(status_code=403, detail=f"Account {user.status}")
    if user.status != "approved":
        raise HTTPException(status_code=403, detail="Account not approved")
    return user


def require_admin(user: User = Depends(require_approved)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user
