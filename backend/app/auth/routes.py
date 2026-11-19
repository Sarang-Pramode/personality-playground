"""Auth + admin allowlist API routes."""

from __future__ import annotations

import hashlib
import re
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.deps import get_db, get_optional_user, require_admin, require_user
from app.auth.email_notify import notify_admin_pending_user
from app.auth.google_oauth import build_google_auth_url, exchange_google_code
from app.auth.passwords import hash_password, verify_password
from app.auth.schemas import (
    BootstrapAdminPasswordRequest,
    LoginRequest,
    SignupRequest,
    StatusUpdateRequest,
)
from app.auth.sessions import (
    clear_session_cookie,
    create_session_token,
    set_session_cookie,
)
from app.auth.users import (
    User,
    create_user,
    get_user_by_email,
    get_user_by_oauth,
    get_user_by_username,
    list_users,
    set_user_password,
    set_user_status,
)
from app.config import Settings, get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\-\.]{3,64}$")


def _issue_session(response: Response, user: User, settings: Settings) -> None:
    token = create_session_token(user.id, settings)
    set_session_cookie(response, token, settings)


def _bootstrap_token_ok(expected: str, provided: str) -> bool:
    """Constant-time compare via SHA-256 digests (handles unequal lengths)."""
    a = hashlib.sha256(expected.encode("utf-8")).digest()
    b = hashlib.sha256(provided.encode("utf-8")).digest()
    return secrets.compare_digest(a, b)


def _admin_needs_password_bootstrap(db: Session, settings: Settings) -> bool:
    if not settings.bootstrap_token.strip():
        return False
    admin = get_user_by_email(db, settings.admin_email.strip().lower(), settings)
    return admin is not None and not admin.password_hash


@router.get("/config")
def auth_config(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return {
        "auth_enabled": settings.auth_enabled,
        "google_oauth": settings.google_oauth_configured,
        "admin_email_domain_hint": settings.admin_email.split("@")[-1]
        if "@" in settings.admin_email
        else None,
        "bootstrap_admin": (
            settings.auth_enabled
            and _admin_needs_password_bootstrap(db, settings)
        ),
    }


@router.post("/bootstrap-admin-password")
def bootstrap_admin_password(
    body: BootstrapAdminPasswordRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """One-time: set password for seeded ADMIN_EMAIL when password_hash is null.

    Requires BOOTSTRAP_TOKEN env. After success, remove BOOTSTRAP_TOKEN from Vercel
    (endpoint also refuses once a password_hash exists).
    """
    expected = settings.bootstrap_token.strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Admin password bootstrap is not enabled",
        )
    if not _bootstrap_token_ok(expected, body.bootstrap_token.strip()):
        raise HTTPException(status_code=401, detail="Invalid bootstrap token")

    email = str(body.email).strip().lower()
    if email != settings.admin_email.strip().lower():
        raise HTTPException(status_code=403, detail="Email is not the admin account")

    user = get_user_by_email(db, email, settings)
    if user is None:
        raise HTTPException(status_code=404, detail="Admin user not found")
    if user.password_hash:
        raise HTTPException(
            status_code=409,
            detail="Admin password already set; bootstrap disabled",
        )
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not an admin account")

    updated = set_user_password(
        db, user.id, hash_password(body.password), settings
    )
    assert updated is not None
    _issue_session(response, updated, settings)
    return {
        "user": updated.public_dict(),
        "bootstrap_complete": True,
        "next_step": "Remove BOOTSTRAP_TOKEN from Vercel env and redeploy",
    }


@router.get("/me")
def me(user: User | None = Depends(get_optional_user)) -> dict:
    if user is None:
        return {"authenticated": False, "user": None}
    return {"authenticated": True, "user": user.public_dict()}


@router.post("/signup")
def signup(
    body: SignupRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    email = str(body.email).strip().lower()
    username = body.username.strip()
    if not _USERNAME_RE.match(username):
        raise HTTPException(
            status_code=400,
            detail="Username must be 3–64 chars: letters, numbers, _ - .",
        )
    if get_user_by_email(db, email, settings):
        raise HTTPException(status_code=409, detail="Email already registered")
    if get_user_by_username(db, username, settings):
        raise HTTPException(status_code=409, detail="Username already taken")

    is_admin_email = email == settings.admin_email.strip().lower()
    user = create_user(
        db,
        email=email,
        username=username,
        password_hash=hash_password(body.password),
        status="approved" if is_admin_email else "pending",
        role="admin" if is_admin_email else "user",
        settings=settings,
    )
    notify = None
    if user.status == "pending":
        notify = notify_admin_pending_user(
            username=user.username, email=user.email, settings=settings
        )
    _issue_session(response, user, settings)
    return {
        "user": user.public_dict(),
        "admin_notified": notify,
    }


@router.post("/login")
def login(
    body: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    login_id = body.login.strip()
    user = (
        get_user_by_email(db, login_id, settings)
        if "@" in login_id
        else get_user_by_username(db, login_id, settings)
    )
    if user is None or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(user.password_hash, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.status in ("denied", "revoked"):
        raise HTTPException(status_code=403, detail=f"Account {user.status}")
    _issue_session(response, user, settings)
    return {"user": user.public_dict()}


@router.post("/logout")
def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
    _user: User | None = Depends(require_user),
) -> dict:
    clear_session_cookie(response, settings)
    return {"ok": True}


@router.get("/google/start")
def google_start(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    if not settings.google_oauth_configured:
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    state = secrets.token_urlsafe(24)
    redirect = RedirectResponse(
        url=build_google_auth_url(state, settings), status_code=302
    )
    redirect.set_cookie(
        key="pp_oauth_state",
        value=state,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,  # type: ignore[arg-type]
        max_age=600,
        path="/",
    )
    return redirect


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    frontend = settings.app_base_url.rstrip("/")
    if error:
        return RedirectResponse(f"{frontend}/?auth_error={error}", status_code=302)
    if not code or not state:
        return RedirectResponse(f"{frontend}/?auth_error=missing_code", status_code=302)
    cookie_state = request.cookies.get("pp_oauth_state")
    if not cookie_state or cookie_state != state:
        return RedirectResponse(f"{frontend}/?auth_error=state_mismatch", status_code=302)

    try:
        info = await exchange_google_code(code, settings)
    except Exception:  # noqa: BLE001
        return RedirectResponse(f"{frontend}/?auth_error=token_exchange", status_code=302)

    email = (info.get("email") or "").strip().lower()
    sub = info.get("sub")
    if not email or not sub:
        return RedirectResponse(f"{frontend}/?auth_error=no_email", status_code=302)

    user = get_user_by_oauth(db, "google", sub, settings) or get_user_by_email(
        db, email, settings
    )
    if user is None:
        base = (info.get("name") or email.split("@")[0] or "user").replace(" ", "")
        base = re.sub(r"[^a-zA-Z0-9_\-\.]", "", base)[:48] or "user"
        username = base
        n = 0
        while get_user_by_username(db, username, settings):
            n += 1
            username = f"{base}{n}"
        is_admin_email = email == settings.admin_email.strip().lower()
        user = create_user(
            db,
            email=email,
            username=username,
            oauth_provider="google",
            oauth_sub=sub,
            status="approved" if is_admin_email else "pending",
            role="admin" if is_admin_email else "user",
            settings=settings,
        )
        if user.status == "pending":
            notify_admin_pending_user(
                username=user.username, email=user.email, settings=settings
            )
    elif not user.oauth_sub:
        # Link Google to existing email account
        from datetime import datetime, timezone
        from sqlalchemy import text

        db.execute(
            text(
                "UPDATE users SET oauth_provider = 'google', oauth_sub = :s, updated_at = :t WHERE id = :id"
            ),
            {
                "s": sub,
                "t": datetime.now(timezone.utc).isoformat(),
                "id": user.id,
            },
        )
        db.commit()
        user = get_user_by_oauth(db, "google", sub, settings) or user

    if user.status in ("denied", "revoked"):
        return RedirectResponse(
            f"{frontend}/?auth_error=account_{user.status}", status_code=302
        )

    redirect = RedirectResponse(f"{frontend}/", status_code=302)
    _issue_session(redirect, user, settings)
    redirect.delete_cookie("pp_oauth_state", path="/")
    return redirect


@admin_router.get("/users")
def admin_list_users(
    status: str | None = None,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    allowed = {None, "pending", "approved", "denied", "revoked"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail="Invalid status filter")
    users = list_users(db, status=status, settings=settings)  # type: ignore[arg-type]
    return {"users": [u.public_dict() for u in users]}


@admin_router.post("/users/{user_id}/status")
def admin_set_status(
    user_id: str,
    body: StatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> dict:
    if user_id == admin.id and body.status in ("denied", "revoked"):
        raise HTTPException(status_code=400, detail="Cannot revoke yourself")
    updated = set_user_status(db, user_id, body.status, settings)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user": updated.public_dict()}
