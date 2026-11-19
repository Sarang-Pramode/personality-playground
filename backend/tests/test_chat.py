"""Tests for chat orchestration and API contracts (with approved session)."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

os.environ.setdefault("AUTH_ENABLED", "true")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-please-change-32b")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("APP_BASE_URL", "http://testserver")
os.environ.setdefault("CORS_ORIGINS", "http://testserver")

from app.auth.passwords import hash_password
from app.auth.users import ensure_admin_seed, get_user_by_email
from app.chat.service import ChatService
from app.config import get_settings
from app.db import get_session_factory, reset_engine, run_migrations


@pytest.fixture
def client():
    get_settings.cache_clear()
    reset_engine()
    settings = get_settings()
    run_migrations(settings)
    factory = get_session_factory(settings)
    session = factory()
    try:
        ensure_admin_seed(session, settings)
        admin = get_user_by_email(session, settings.admin_email, settings)
        assert admin
        session.execute(
            text("UPDATE users SET password_hash = :h WHERE id = :id"),
            {"h": hash_password("adminpass12"), "id": admin.id},
        )
        session.commit()
    finally:
        session.close()

    from app.main import app

    with TestClient(app) as c:
        login = c.post(
            "/api/auth/login",
            json={"login": settings.admin_email, "password": "adminpass12"},
        )
        assert login.status_code == 200
        yield c
    get_settings.cache_clear()
    reset_engine()


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "models" in body


def test_fixtures(client):
    r = client.get("/api/fixtures")
    assert r.status_code == 200
    body = r.json()
    ids = {c["customer_id"] for c in body["customers"]}
    assert ids == {"customer_A", "customer_B"}
    assert len(body["scenarios"]) >= 3


def test_preview(client):
    r = client.post("/api/personality/preview", json={"preset": "explorer"})
    assert r.status_code == 200
    body = r.json()
    assert body["profile"]["exploration"] == 9
    assert body["map_position"]["x"] == 9


@pytest.mark.asyncio
async def test_scripted_chat_balance():
    service = ChatService()
    result = await service.chat(
        message="How many rewards do I have?",
        customer_id="customer_A",
        personality=None,
        preset="balanced",
        provider="demo",
        model_id=None,
        session_id=None,
        scenario_id="balance_check",
    )
    assert result["metadata"]["mode"] == "scripted_demo"
    assert "42350" in result["reply"]
    assert result["metadata"]["tool_traces"]
    assert result["run_id"]
    assert "Scripted demo mode" in result["reply"]


@pytest.mark.asyncio
async def test_openai_unavailable_visible_error():
    service = ChatService()
    result = await service.chat(
        message="Hello",
        customer_id="customer_B",
        personality=None,
        preset="concise",
        provider="openai",
        model_id="gpt-4o-mini",
        session_id=None,
        scenario_id=None,
    )
    assert result["metadata"]["mode"] == "error"
    assert result["error"]
    assert "OPENAI_API_KEY" in result["reply"] or "not configured" in result["reply"]


def test_chat_endpoint_scripted(client):
    r = client.post(
        "/api/chat",
        json={
            "message": "What are my redemption options?",
            "customer_id": "customer_A",
            "provider": "demo",
            "preset": "explorer",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["metadata"]["mode"] == "scripted_demo"
    assert body["metadata"]["fixture_id"] == "customer_A"
    assert any(
        t["tool"] == "get_redemption_options" for t in body["metadata"]["tool_traces"]
    )
