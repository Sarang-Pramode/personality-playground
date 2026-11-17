"""FastAPI entrypoint for Personality Playground Phase 1 + gated auth."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.auth.deps import require_admin, require_approved
from app.auth.routes import admin_router, router as auth_router
from app.auth.users import User, ensure_admin_seed
from app.chat.service import get_chat_service
from app.config import get_settings
from app.db import get_session_factory, run_migrations
from app.fixtures.data import list_fixtures
from app.llm.adapters import list_models
from app.personality.compiler import compile_personality
from app.personality.presets import PRESETS
from app.schemas import ChatRequest, ChatResponse, PreviewRequest
from app.tools.registry import list_tool_names

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    import os

    if os.environ.get("VERCEL") and ":memory:" in settings.database_url:
        raise RuntimeError(
            "DATABASE_URL must be a Postgres connection string on Vercel "
            "(in-memory SQLite is not durable across serverless invocations)."
        )
    run_migrations(settings)
    factory = get_session_factory(settings)
    session = factory()
    try:
        ensure_admin_seed(session, settings)
    finally:
        session.close()
    yield


app = FastAPI(
    title="Personality Playground API",
    version="0.2.0",
    description="Phase 1 Interactive MVP — gated allowlist auth + synthetic banking rewards chatbot",
    lifespan=lifespan,
)

_origins = [o for o in settings.cors_origin_list if o != "*"]
# Cookie auth requires explicit origins (not *). Include APP_BASE_URL.
if settings.app_base_url.rstrip("/") not in _origins:
    _origins.append(settings.app_base_url.rstrip("/"))
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
    """Public health — no auth (for probes). Does not expose user data."""
    models = list_models(settings)
    return {
        "status": "ok",
        "prompt_version": settings.prompt_version,
        "auth": True,
        "llm": {
            "openai": settings.openai_available,
            "google": settings.google_available,
            "any_live": settings.any_llm_available,
        },
        "models": models,
        "tools": list_tool_names(),
    }


@app.get("/api/fixtures")
def fixtures(_user: User = Depends(require_approved)) -> dict:
    return list_fixtures()


@app.get("/api/presets")
def presets(_user: User = Depends(require_approved)) -> dict:
    return {"presets": PRESETS, "default": "balanced"}


@app.get("/api/models")
def models(_user: User = Depends(require_approved)) -> dict:
    return {"models": list_models(settings)}


@app.post("/api/personality/preview")
def personality_preview(
    body: PreviewRequest, _user: User = Depends(require_approved)
) -> dict:
    try:
        profile = body.profile.model_dump() if body.profile else None
        return compile_personality(profile, preset=body.preset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest, _user: User = Depends(require_approved)
) -> ChatResponse:
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
def evaluation_status_stub(_user: User = Depends(require_admin)) -> dict:
    """Phase 2 stub — admin-only placeholder."""
    return {
        "phase": 2,
        "implemented": False,
        "message": "Batch evaluation, judges, and Measured overlays are reserved for Phase 2.",
    }
