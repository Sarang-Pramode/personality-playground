"""FastAPI entrypoint for Personality Playground Phase 1 + gated auth."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth.deps import require_approved
from app.auth.routes import admin_router, router as auth_router
from app.auth.users import User, ensure_admin_seed
from app.chat.service import get_chat_service
from app.config import get_settings
from app.config_expiry import openai_key_expiry_payload
from app.db import get_session_factory, run_migrations
from app.demo.service import get_demo_lab_service
from app.evaluation.service import get_evaluation_service
from app.fixtures.data import list_fixtures
from app.llm.adapters import list_models
from app.llm.allowlist import OPENAI_ALLOWED_MODELS
from app.personality.compiler import compile_personality
from app.personality.presets import PRESETS
from app.schemas import (
    ChatRequest,
    ChatResponse,
    DemoJudgeRequest,
    DemoRunRequest,
    PreviewRequest,
)
from app.tools.registry import list_tool_names

@asynccontextmanager
async def lifespan(_app: FastAPI):
    import os

    settings = get_settings()
    if os.environ.get("VERCEL") and ":memory:" in settings.database_url:
        raise RuntimeError(
            "DATABASE_URL must be a Postgres connection string on Vercel "
            "(in-memory SQLite is not durable across serverless invocations)."
        )
    run_migrations(settings)
    if settings.auth_enabled:
        factory = get_session_factory(settings)
        session = factory()
        try:
            ensure_admin_seed(session, settings)
        finally:
            session.close()
    yield


app = FastAPI(
    title="Personality Playground API",
    version="0.3.0",
    description=(
        "Personality studio + Demo lab with Phase 2 independent judges "
        "(auth optional via AUTH_ENABLED)"
    ),
    lifespan=lifespan,
)

_boot = get_settings()
_origins = [o for o in _boot.cors_origin_list if o != "*"]
# Cookie auth requires explicit origins (not *). Include APP_BASE_URL.
if _boot.app_base_url.rstrip("/") not in _origins:
    _origins.append(_boot.app_base_url.rstrip("/"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/api/health")
def health() -> dict:
    """Public health — no auth (for probes). Does not expose user data or API keys."""
    settings = get_settings()
    models = list_models(settings)
    return {
        "status": "ok",
        "prompt_version": settings.prompt_version,
        "auth": settings.auth_enabled,
        "auth_enabled": settings.auth_enabled,
        "llm": {
            "openai": settings.openai_available,
            "google": settings.google_available,
            "any_live": settings.any_llm_available,
        },
        "openai_allowed_models": list(OPENAI_ALLOWED_MODELS),
        "openai_key_expiry": openai_key_expiry_payload(settings.openai_key_expires_at),
        "models": models,
        "tools": list_tool_names(),
    }


@app.get("/api/fixtures")
def fixtures(_user: User | None = Depends(require_approved)) -> dict:
    return list_fixtures()


@app.get("/api/presets")
def presets(_user: User | None = Depends(require_approved)) -> dict:
    return {"presets": PRESETS, "default": "balanced"}


@app.get("/api/models")
def models(_user: User | None = Depends(require_approved)) -> dict:
    return {"models": list_models(get_settings())}


@app.post("/api/personality/preview")
def personality_preview(
    body: PreviewRequest, _user: User | None = Depends(require_approved)
) -> dict:
    try:
        profile = body.profile.model_dump() if body.profile else None
        return compile_personality(profile, preset=body.preset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest, _user: User | None = Depends(require_approved)
) -> ChatResponse:
    settings = get_settings()
    service = get_chat_service()
    result = await service.chat(
        message=body.message,
        customer_id=body.customer_id,
        personality=body.personality.model_dump() if body.personality else None,
        preset=body.preset,
        provider=body.provider,
        model_id=body.model_id,
        session_id=body.session_id,
        scenario_id=body.scenario_id,
        reset_session=body.reset_session,
        settings=settings,
    )
    return ChatResponse(**result)


@app.get("/api/evaluation/status")
def evaluation_status(
    _user: User | None = Depends(require_approved),
) -> dict:
    """Phase 2 status — independent judges + banking checks."""
    return get_evaluation_service().status()


@app.get("/api/demo/cache")
def demo_cache_get(
    preset: str = "balanced",
    customer_id: str = "customer_A",
    provider: str = "demo",
    model_id: str | None = None,
    _user: User | None = Depends(require_approved),
) -> dict:
    """Return cached preset scenario demos + any persisted report-card scores."""
    try:
        return get_demo_lab_service().list_cached(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=model_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/demo/run")
async def demo_run(
    body: DemoRunRequest, _user: User | None = Depends(require_approved)
) -> dict:
    """
    Run starter scenarios for a preset × fixture × model.
    Cache hits return instantly; set force=true to refresh (re-run LLM).
    By default auto-runs independent judges + banking checks for report cards.
    """
    try:
        return await get_demo_lab_service().run_all(
            preset=body.preset,
            customer_id=body.customer_id,
            provider=body.provider,
            model_id=body.model_id,
            force=body.force,
            scenario_ids=body.scenario_ids,
            auto_judge=body.auto_judge,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/demo/scores")
def demo_scores_get(
    preset: str = "balanced",
    customer_id: str = "customer_A",
    provider: str = "demo",
    model_id: str | None = None,
    _user: User | None = Depends(require_approved),
) -> dict:
    """Report cards for preset × fixture × model (persisted scores only)."""
    try:
        mid = get_demo_lab_service().validate_selection(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=model_id,
        )
        return get_evaluation_service().report_cards(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=mid,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/demo/judge")
async def demo_judge(
    body: DemoJudgeRequest, _user: User | None = Depends(require_approved)
) -> dict:
    """Score cached demo replies with independent judges + banking checks."""
    try:
        mid = get_demo_lab_service().validate_selection(
            preset=body.preset,
            customer_id=body.customer_id,
            provider=body.provider,
            model_id=body.model_id,
        )
        return await get_evaluation_service().score_cached_selection(
            preset=body.preset,
            customer_id=body.customer_id,
            provider=body.provider,
            model_id=mid,
            force=body.force,
            scenario_ids=body.scenario_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
