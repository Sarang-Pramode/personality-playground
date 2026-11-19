"""Demo lab cache hit/miss tests."""

import os

# Force open access for these API tests (override other modules' AUTH_ENABLED=true).
os.environ["AUTH_ENABLED"] = "false"
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-please-change-32b")
os.environ.setdefault("OPENAI_API_KEY", "")

import pytest
from fastapi.testclient import TestClient

from app.chat.service import ChatService
from app.config import get_settings
from app.db import reset_engine, run_migrations
from app.demo.cache import DemoCacheStore, make_cache_key, safe_metadata
from app.demo.service import DemoLabService


def _fresh_settings():
    os.environ["AUTH_ENABLED"] = "false"
    get_settings.cache_clear()
    reset_engine()
    settings = get_settings()
    run_migrations(settings)
    return settings


@pytest.fixture
def client():
    _fresh_settings()
    from app.main import app

    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()
    reset_engine()


@pytest.fixture
def store():
    settings = _fresh_settings()
    yield DemoCacheStore(settings)
    get_settings.cache_clear()
    reset_engine()


def test_make_cache_key_stable():
    a = make_cache_key(
        preset="balanced",
        customer_id="customer_A",
        scenario_id="balance_check",
        provider="demo",
        model_id="scripted-demo",
        prompt_version="personality-compiler-v1",
    )
    b = make_cache_key(
        preset="balanced",
        customer_id="customer_A",
        scenario_id="balance_check",
        provider="DEMO",
        model_id="scripted-demo",
        prompt_version="personality-compiler-v1",
    )
    assert a == b
    assert "balanced" in a
    assert "balance_check" in a


def test_safe_metadata_strips_tool_payloads():
    meta = safe_metadata(
        {
            "profile": {"exploration": 5},
            "preset": "balanced",
            "prompt_version": "personality-compiler-v1",
            "fixture_id": "customer_A",
            "scenario_id": "balance_check",
            "model_id": "scripted-demo",
            "provider": "demo",
            "mode": "scripted_demo",
            "tool_traces": [
                {
                    "tool": "get_rewards_balance",
                    "arguments": {"customer_id": "customer_A"},
                    "result": {"ok": True, "data": {"available": 42350}},
                }
            ],
            "system_prompt": "SECRET-ISH PROMPT",
            "run_id": "abc",
        }
    )
    assert "system_prompt" not in meta
    assert meta["tool_trace_summary"] == [
        {"tool": "get_rewards_balance", "ok": True, "error": None}
    ]
    assert "data" not in str(meta["tool_trace_summary"])


def test_cache_miss_then_hit(store: DemoCacheStore):
    assert (
        store.get(
            preset="balanced",
            customer_id="customer_A",
            scenario_id="balance_check",
            provider="demo",
            model_id="scripted-demo",
        )
        is None
    )
    stored = store.put(
        preset="balanced",
        customer_id="customer_A",
        scenario_id="balance_check",
        provider="demo",
        model_id="scripted-demo",
        reply="Hello cached",
        metadata={
            "profile": {"exploration": 5},
            "preset": "balanced",
            "prompt_version": "personality-compiler-v1",
            "fixture_id": "customer_A",
            "scenario_id": "balance_check",
            "model_id": "scripted-demo",
            "provider": "demo",
            "mode": "scripted_demo",
            "tool_traces": [],
            "run_id": "r1",
        },
    )
    assert stored["reply"] == "Hello cached"
    hit = store.get(
        preset="balanced",
        customer_id="customer_A",
        scenario_id="balance_check",
        provider="demo",
        model_id="scripted-demo",
    )
    assert hit is not None
    assert hit["reply"] == "Hello cached"
    assert hit["cached"] is True


@pytest.mark.asyncio
async def test_demo_lab_run_miss_then_hit():
    settings = _fresh_settings()
    service = DemoLabService(
        store=DemoCacheStore(settings),
        chat=ChatService(),
        settings=settings,
    )
    first = await service.run_all(
        preset="concise",
        customer_id="customer_B",
        provider="demo",
        model_id="scripted-demo",
        force=False,
        scenario_ids=["balance_check"],
    )
    assert first["cache_misses"] == 1
    assert first["cache_hits"] == 0
    assert "Scripted demo" in first["results"][0]["entry"]["reply"]

    second = await service.run_all(
        preset="concise",
        customer_id="customer_B",
        provider="demo",
        model_id="scripted-demo",
        force=False,
        scenario_ids=["balance_check"],
    )
    assert second["cache_hits"] == 1
    assert second["cache_misses"] == 0
    assert second["results"][0]["cache_hit"] is True
    assert second["results"][0]["entry"]["reply"] == first["results"][0]["entry"]["reply"]

    # force refresh counts as miss path (re-run + overwrite)
    third = await service.run_all(
        preset="concise",
        customer_id="customer_B",
        provider="demo",
        model_id="scripted-demo",
        force=True,
        scenario_ids=["balance_check"],
    )
    assert third["cache_hits"] == 0
    assert third["cache_misses"] == 1
    get_settings.cache_clear()
    reset_engine()


def test_demo_api_cache_and_run(client: TestClient):
    starters = [
        "balance_check",
        "redemption_options",
        "recent_activity",
        "card_earn_rates",
    ]
    empty = client.get(
        "/api/demo/cache",
        params={
            "preset": "explorer",
            "customer_id": "customer_A",
            "provider": "demo",
            "model_id": "scripted-demo",
        },
    )
    assert empty.status_code == 200
    body = empty.json()
    assert body["cached_count"] == 0
    assert body["total"] >= 4  # Phase 2 seeds additional eval-category scenarios

    run = client.post(
        "/api/demo/run",
        json={
            "preset": "explorer",
            "customer_id": "customer_A",
            "provider": "demo",
            "model_id": "scripted-demo",
            "force": False,
            "scenario_ids": starters,
            "auto_judge": True,
        },
    )
    assert run.status_code == 200
    run_body = run.json()
    assert run_body["cache_misses"] == 4
    assert all(r["entry"]["reply"] for r in run_body["results"])
    assert run_body["scored_count"] == 4

    cached = client.get(
        "/api/demo/cache",
        params={
            "preset": "explorer",
            "customer_id": "customer_A",
            "provider": "demo",
            "model_id": "scripted-demo",
        },
    )
    assert cached.json()["cached_count"] == 4

    # Second run should be all hits
    again = client.post(
        "/api/demo/run",
        json={
            "preset": "explorer",
            "customer_id": "customer_A",
            "provider": "demo",
            "model_id": "scripted-demo",
            "force": False,
            "scenario_ids": starters,
        },
    )
    assert again.json()["cache_hits"] == 4
    assert again.json()["cache_misses"] == 0


def test_demo_api_rejects_disallowed_openai_model(client: TestClient):
    r = client.post(
        "/api/demo/run",
        json={
            "preset": "balanced",
            "customer_id": "customer_A",
            "provider": "openai",
            "model_id": "o1",
            "force": True,
            "scenario_ids": ["balance_check"],
        },
    )
    assert r.status_code == 400
    assert "allowlisted" in r.json()["detail"].lower()
