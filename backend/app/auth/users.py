"""User persistence for allowlist auth."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth.crypto import decrypt_field, email_lookup_hash, encrypt_field
from app.config import Settings, get_settings

Status = Literal["pending", "approved", "denied", "revoked"]
Role = Literal["user", "admin"]


@dataclass
class User:
    id: str
    email: str
    username: str
    password_hash: str | None
    oauth_provider: str | None
    oauth_sub: str | None
    status: Status
    role: Role
    created_at: str
    updated_at: str

    def public_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "status": self.status,
            "role": self.role,
            "oauth_provider": self.oauth_provider,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_user(row, settings: Settings) -> User:
    mapping = row._mapping if hasattr(row, "_mapping") else row
    return User(
        id=mapping["id"],
        email=decrypt_field(mapping["email_enc"], settings),
        username=mapping["username"],
        password_hash=mapping["password_hash"],
        oauth_provider=mapping["oauth_provider"],
        oauth_sub=mapping["oauth_sub"],
        status=mapping["status"],
        role=mapping["role"],
        created_at=mapping["created_at"],
        updated_at=mapping["updated_at"],
    )


def get_user_by_id(session: Session, user_id: str, settings: Settings | None = None) -> User | None:
    settings = settings or get_settings()
    row = session.execute(
        text("SELECT * FROM users WHERE id = :id"), {"id": user_id}
    ).fetchone()
    return _row_to_user(row, settings) if row else None


def get_user_by_email(session: Session, email: str, settings: Settings | None = None) -> User | None:
    settings = settings or get_settings()
    row = session.execute(
        text("SELECT * FROM users WHERE email_hash = :h"),
        {"h": email_lookup_hash(email)},
    ).fetchone()
    return _row_to_user(row, settings) if row else None


def get_user_by_username(session: Session, username: str, settings: Settings | None = None) -> User | None:
    settings = settings or get_settings()
    row = session.execute(
        text("SELECT * FROM users WHERE lower(username) = lower(:u)"),
        {"u": username.strip()},
    ).fetchone()
    return _row_to_user(row, settings) if row else None


def get_user_by_oauth(
    session: Session, provider: str, sub: str, settings: Settings | None = None
) -> User | None:
    settings = settings or get_settings()
    row = session.execute(
        text(
            "SELECT * FROM users WHERE oauth_provider = :p AND oauth_sub = :s"
        ),
        {"p": provider, "s": sub},
    ).fetchone()
    return _row_to_user(row, settings) if row else None


def create_user(
    session: Session,
    *,
    email: str,
    username: str,
    password_hash: str | None = None,
    oauth_provider: str | None = None,
    oauth_sub: str | None = None,
    status: Status = "pending",
    role: Role = "user",
    settings: Settings | None = None,
) -> User:
    settings = settings or get_settings()
    now = _utcnow()
    user_id = str(uuid.uuid4())
    session.execute(
        text(
            """
            INSERT INTO users (
                id, email_hash, email_enc, username, password_hash,
                oauth_provider, oauth_sub, status, role, created_at, updated_at
            ) VALUES (
                :id, :email_hash, :email_enc, :username, :password_hash,
                :oauth_provider, :oauth_sub, :status, :role, :created_at, :updated_at
            )
            """
        ),
        {
            "id": user_id,
            "email_hash": email_lookup_hash(email),
            "email_enc": encrypt_field(email.strip().lower(), settings),
            "username": username.strip(),
            "password_hash": password_hash,
            "oauth_provider": oauth_provider,
            "oauth_sub": oauth_sub,
            "status": status,
            "role": role,
            "created_at": now,
            "updated_at": now,
        },
    )
    session.commit()
    user = get_user_by_id(session, user_id, settings)
    assert user is not None
    return user


def set_user_status(
    session: Session, user_id: str, status: Status, settings: Settings | None = None
) -> User | None:
    settings = settings or get_settings()
    session.execute(
        text(
            "UPDATE users SET status = :s, updated_at = :t WHERE id = :id"
        ),
        {"s": status, "t": _utcnow(), "id": user_id},
    )
    session.commit()
    return get_user_by_id(session, user_id, settings)


def set_user_password(
    session: Session,
    user_id: str,
    password_hash: str,
    settings: Settings | None = None,
) -> User | None:
    settings = settings or get_settings()
    session.execute(
        text(
            "UPDATE users SET password_hash = :h, updated_at = :t WHERE id = :id"
        ),
        {"h": password_hash, "t": _utcnow(), "id": user_id},
    )
    session.commit()
    return get_user_by_id(session, user_id, settings)


def list_users(
    session: Session,
    *,
    status: Status | None = None,
    settings: Settings | None = None,
) -> list[User]:
    settings = settings or get_settings()
    if status:
        rows = session.execute(
            text("SELECT * FROM users WHERE status = :s ORDER BY created_at DESC"),
            {"s": status},
        ).fetchall()
    else:
        rows = session.execute(
            text("SELECT * FROM users ORDER BY created_at DESC")
        ).fetchall()
    return [_row_to_user(r, settings) for r in rows]


def ensure_admin_seed(session: Session, settings: Settings | None = None) -> User | None:
    """Ensure ADMIN_EMAIL exists as approved admin (passwordless until set)."""
    settings = settings or get_settings()
    email = settings.admin_email.strip().lower()
    if not email:
        return None
    existing = get_user_by_email(session, email, settings)
    if existing:
        if existing.role != "admin" or existing.status != "approved":
            session.execute(
                text(
                    "UPDATE users SET role = 'admin', status = 'approved', updated_at = :t WHERE id = :id"
                ),
                {"t": _utcnow(), "id": existing.id},
            )
            session.commit()
            return get_user_by_id(session, existing.id, settings)
        return existing
    username = email.split("@")[0] or "admin"
    # Avoid username collision
    base = username
    n = 0
    while get_user_by_username(session, username, settings):
        n += 1
        username = f"{base}{n}"
    return create_user(
        session,
        email=email,
        username=username,
        password_hash=None,
        status="approved",
        role="admin",
        settings=settings,
    )
