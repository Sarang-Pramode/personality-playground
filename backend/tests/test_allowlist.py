"""OpenAI model allowlist enforcement."""

import os

os.environ["AUTH_ENABLED"] = "false"
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-please-change-32b")
os.environ.setdefault("OPENAI_API_KEY", "")
os.environ.setdefault("OPENAI_MODEL", "gpt-4o-mini")

import pytest

from app.config import get_settings
from app.db import reset_engine, run_migrations
from app.llm.adapters import ModelNotAllowedError, complete_chat, list_models
from app.llm.allowlist import (
    OPENAI_ALLOWED_MODELS,
    is_openai_model_allowed,
    resolve_openai_model,
)


@pytest.fixture(autouse=True)
def _reset():
    os.environ["AUTH_ENABLED"] = "false"
    get_settings.cache_clear()
    reset_engine()
    run_migrations(get_settings())
    yield
    get_settings.cache_clear()
    reset_engine()


def test_allowlist_contains_experiment_models():
    assert "gpt-4o-mini" in OPENAI_ALLOWED_MODELS
    assert "gpt-4.1-mini" in OPENAI_ALLOWED_MODELS
    assert "gpt-4o" in OPENAI_ALLOWED_MODELS
    assert "gpt-5.4-nano" in OPENAI_ALLOWED_MODELS
    assert "gpt-5.4-mini" in OPENAI_ALLOWED_MODELS
    # Shut down / expensive flagships stay excluded
    assert "gpt-4.1-nano" not in OPENAI_ALLOWED_MODELS
    assert "o4-mini" not in OPENAI_ALLOWED_MODELS
    assert "gpt-4.1" not in OPENAI_ALLOWED_MODELS
    assert "o1" not in OPENAI_ALLOWED_MODELS
    assert "o1-preview" not in OPENAI_ALLOWED_MODELS
    assert "o3" not in OPENAI_ALLOWED_MODELS


def test_is_openai_model_allowed():
    assert is_openai_model_allowed("gpt-4o-mini")
    assert is_openai_model_allowed("gpt-4.1-mini")
    assert is_openai_model_allowed("gpt-4o")
    assert is_openai_model_allowed("gpt-5.4-nano")
    assert not is_openai_model_allowed("gpt-4.1")
    assert not is_openai_model_allowed("o1")
    assert not is_openai_model_allowed(None)


def test_resolve_openai_model_falls_back():
    assert resolve_openai_model("o1", "gpt-4o-mini") == "gpt-4o-mini"
    assert resolve_openai_model("gpt-4o", "gpt-4o-mini") == "gpt-4o"
    assert resolve_openai_model("gpt-4.1-mini", "gpt-4o-mini") == "gpt-4.1-mini"


def test_list_models_only_allowlisted_openai():
    models = list_models(get_settings())
    openai_ids = [m["model_id"] for m in models if m["provider"] == "openai"]
    assert openai_ids == list(OPENAI_ALLOWED_MODELS)
    assert all(m["model_id"] in OPENAI_ALLOWED_MODELS for m in models if m["provider"] == "openai")


@pytest.mark.asyncio
async def test_complete_chat_rejects_disallowed_openai_model():
    # Key present so we hit allowlist before network
    os.environ["OPENAI_API_KEY"] = "sk-test-not-real"
    get_settings.cache_clear()
    settings = get_settings()
    with pytest.raises(ModelNotAllowedError) as exc:
        await complete_chat(
            provider="openai",
            model_id="o1",
            system_prompt="test",
            messages=[{"role": "user", "content": "hi"}],
            customer_id="customer_A",
            settings=settings,
        )
    assert "not allowlisted" in str(exc.value)
    os.environ["OPENAI_API_KEY"] = ""
    get_settings.cache_clear()


def test_health_exposes_allowlist_and_expiry():
    os.environ["OPENAI_KEY_EXPIRES_AT"] = "2099-01-15"
    get_settings.cache_clear()
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["openai_allowed_models"] == list(OPENAI_ALLOWED_MODELS)
        assert body["openai_key_expiry"]["expires_at"] == "2099-01-15"
        assert body["openai_key_expiry"]["days_remaining"] > 0
        assert body["openai_key_expiry"]["warn"] is False
    os.environ.pop("OPENAI_KEY_EXPIRES_AT", None)
    get_settings.cache_clear()
