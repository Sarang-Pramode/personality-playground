"""Security tests: unauthenticated / pending / revoked cannot access playground APIs."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Isolate settings before importing app
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["SESSION_SECRET"] = "test-session-secret-please-change-32b"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["APP_BASE_URL"] = "http://testserver"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["COOKIE_SECURE"] = "false"
os.environ.pop("GOOGLE_CLIENT_ID", None)
os.environ.pop("GOOGLE_CLIENT_SECRET", None)
os.environ.pop("DATA_ENCRYPTION_KEY", None)

from app.config import get_settings  # noqa: E402
from app.db import reset_engine, run_migrations  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    get_settings.cache_clear()
    reset_engine()
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("SESSION_SECRET", "test-session-secret-please-change-32b")
    monkeypatch.setenv("ADMIN_EMAIL", "admin@example.com")
    get_settings.cache_clear()
    reset_engine()
    run_migrations(get_settings())

    from app.main import app
    from app.auth.users import ensure_admin_seed
    from app.db import get_session_factory

    factory = get_session_factory(get_settings())
    session = factory()
    try:
        ensure_admin_seed(session, get_settings())
    finally:
        session.close()

    with TestClient(app) as c:
        yield c

    get_settings.cache_clear()
    reset_engine()


def test_health_public(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_unauthenticated_chat_401(client):
    r = client.post(
        "/api/chat",
        json={"message": "hi", "customer_id": "customer_A", "provider": "demo"},
    )
    assert r.status_code == 401


def test_unauthenticated_fixtures_401(client):
    assert client.get("/api/fixtures").status_code == 401


def test_signup_pending_cannot_chat(client):
    r = client.post(
        "/api/auth/signup",
        json={
            "email": "pending@example.com",
            "username": "pendinguser",
            "password": "password123",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["user"]["status"] == "pending"
    assert client.cookies.get("pp_session")

    chat = client.post(
        "/api/chat",
        json={"message": "hi", "customer_id": "customer_A", "provider": "demo"},
    )
    assert chat.status_code == 403
    assert "pending" in chat.json()["detail"].lower()


def test_approved_user_can_chat(client):
    client.post(
        "/api/auth/signup",
        json={
            "email": "ok@example.com",
            "username": "okuser",
            "password": "password123",
        },
    )
    # Promote via admin login — set password for seeded admin first
    from app.auth.passwords import hash_password
    from app.auth.users import get_user_by_email
    from app.db import get_session_factory
    from sqlalchemy import text

    settings = get_settings()
    factory = get_session_factory(settings)
    session = factory()
    try:
        admin = get_user_by_email(session, "admin@example.com", settings)
        assert admin
        session.execute(
            text("UPDATE users SET password_hash = :h WHERE id = :id"),
            {"h": hash_password("adminpass12"), "id": admin.id},
        )
        pending = get_user_by_email(session, "ok@example.com", settings)
        assert pending
        session.execute(
            text("UPDATE users SET status = 'approved' WHERE id = :id"),
            {"id": pending.id},
        )
        session.commit()
    finally:
        session.close()

    # Re-login as approved user
    client.post("/api/auth/logout")
    login = client.post(
        "/api/auth/login",
        json={"login": "okuser", "password": "password123"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["status"] == "approved"

    chat = client.post(
        "/api/chat",
        json={
            "message": "How many rewards do I have?",
            "customer_id": "customer_A",
            "provider": "demo",
        },
    )
    assert chat.status_code == 200
    assert chat.json()["metadata"]["mode"] == "scripted_demo"


def test_revoked_user_blocked(client):
    client.post(
        "/api/auth/signup",
        json={
            "email": "rev@example.com",
            "username": "revuser",
            "password": "password123",
        },
    )
    from app.auth.users import get_user_by_email
    from app.db import get_session_factory
    from sqlalchemy import text

    settings = get_settings()
    factory = get_session_factory(settings)
    session = factory()
    try:
        u = get_user_by_email(session, "rev@example.com", settings)
        session.execute(
            text("UPDATE users SET status = 'revoked' WHERE id = :id"),
            {"id": u.id},
        )
        session.commit()
    finally:
        session.close()

    chat = client.post(
        "/api/chat",
        json={"message": "hi", "customer_id": "customer_A", "provider": "demo"},
    )
    assert chat.status_code == 403


def test_admin_only_list_users(client):
    client.post(
        "/api/auth/signup",
        json={
            "email": "norm@example.com",
            "username": "normuser",
            "password": "password123",
        },
    )
    # Approve so they can hit require_approved before admin check
    from app.auth.users import get_user_by_email
    from app.db import get_session_factory
    from sqlalchemy import text

    settings = get_settings()
    factory = get_session_factory(settings)
    session = factory()
    try:
        u = get_user_by_email(session, "norm@example.com", settings)
        session.execute(
            text("UPDATE users SET status = 'approved' WHERE id = :id"),
            {"id": u.id},
        )
        session.commit()
    finally:
        session.close()

    r = client.get("/api/admin/users")
    assert r.status_code == 403


def test_admin_can_approve(client):
    from app.auth.passwords import hash_password
    from app.auth.users import get_user_by_email
    from app.db import get_session_factory
    from sqlalchemy import text

    settings = get_settings()
    factory = get_session_factory(settings)
    session = factory()
    try:
        admin = get_user_by_email(session, "admin@example.com", settings)
        session.execute(
            text("UPDATE users SET password_hash = :h WHERE id = :id"),
            {"h": hash_password("adminpass12"), "id": admin.id},
        )
        session.commit()
    finally:
        session.close()

    client.post(
        "/api/auth/signup",
        json={
            "email": "wait@example.com",
            "username": "waituser",
            "password": "password123",
        },
    )
    client.post("/api/auth/logout")
    client.post(
        "/api/auth/login",
        json={"login": "admin@example.com", "password": "adminpass12"},
    )
    users = client.get("/api/admin/users?status=pending").json()["users"]
    target = next(u for u in users if u["username"] == "waituser")
    upd = client.post(
        f"/api/admin/users/{target['id']}/status",
        json={"status": "approved"},
    )
    assert upd.status_code == 200
    assert upd.json()["user"]["status"] == "approved"


def test_login_wrong_password_401(client):
    client.post(
        "/api/auth/signup",
        json={
            "email": "x@example.com",
            "username": "xuser",
            "password": "password123",
        },
    )
    client.post("/api/auth/logout")
    r = client.post(
        "/api/auth/login",
        json={"login": "xuser", "password": "wrong-password"},
    )
    assert r.status_code == 401
