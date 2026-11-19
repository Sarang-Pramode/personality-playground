"""Signed httpOnly session cookies."""

from __future__ import annotations

from datetime import timedelta

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from starlette.responses import Response

from app.config import Settings, get_settings


def _serializer(settings: Settings) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        settings.session_secret, salt="personality-playground-session"
    )


def create_session_token(user_id: str, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    return _serializer(settings).dumps({"uid": user_id})


def read_session_token(token: str, settings: Settings | None = None) -> str | None:
    settings = settings or get_settings()
    max_age = int(timedelta(hours=settings.session_ttl_hours).total_seconds())
    try:
        data = _serializer(settings).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    uid = data.get("uid")
    return uid if isinstance(uid, str) else None


def set_session_cookie(response: Response, token: str, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        max_age=int(timedelta(hours=settings.session_ttl_hours).total_seconds()),
        path="/",
    )


def clear_session_cookie(response: Response, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
    )
