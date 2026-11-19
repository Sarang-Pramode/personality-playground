"""Demo lab auto-judge + banking scores (no fabricated personality scores)."""

import os

os.environ["AUTH_ENABLED"] = "false"
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SESSION_SECRET", "test-session-secret-please-change-32b")
os.environ["OPENAI_API_KEY"] = ""

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import reset_engine, run_migrations


def _fresh():
    os.environ["AUTH_ENABLED"] = "false"
    os.environ["OPENAI_API_KEY"] = ""
    get_settings.cache_clear()
    reset_engine()
    settings = get_settings()
    run_migrations(settings)
    return settings


@pytest.fixture
def client():
    _fresh()
    from app.main import app

    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()
    reset_engine()


def test_evaluation_status_implemented(client):
    res = client.get("/api/evaluation/status")
    assert res.status_code == 200
    body = res.json()
    assert body["implemented"] is True
    assert body["judge_available"] is False
    assert "independent-judge" in body["judge_prompt_version"]


def test_demo_run_auto_scores_banking_without_openai(client):
    res = client.post(
        "/api/demo/run",
        json={
            "preset": "balanced",
            "customer_id": "customer_A",
            "provider": "demo",
            "model_id": "scripted-demo",
            "scenario_ids": ["balance_check", "hallucination_pressure"],
            "auto_judge": True,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total"] == 2
    assert body["scored_count"] == 2
    for row in body["results"]:
        score = row["score"]
        assert score is not None
        assert score["judged"] is False  # no OpenAI → no personality scores
        assert score["banking_checks"]
        assert any(c["check_id"] for c in score["banking_checks"])
        # Never invent measured profile without real judge
        assert score.get("measured_profile") in (None, {})


def test_demo_scores_endpoint(client):
    client.post(
        "/api/demo/run",
        json={
            "preset": "concise",
            "customer_id": "customer_A",
            "provider": "demo",
            "model_id": "scripted-demo",
            "scenario_ids": ["balance_check"],
            "auto_judge": True,
        },
    )
    res = client.get(
        "/api/demo/scores",
        params={
            "preset": "concise",
            "customer_id": "customer_A",
            "provider": "demo",
            "model_id": "scripted-demo",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["scored_count"] >= 1
    assert body["aggregate"]["banking_total"] >= 1


def test_fixtures_include_eval_categories(client):
    res = client.get("/api/fixtures")
    assert res.status_code == 200
    body = res.json()
    assert len(body["eval_categories"]) == 12
    cats = {s.get("category") for s in body["scenarios"]}
    assert "frustration" in cats
    assert "hallucination_pressure" in cats
