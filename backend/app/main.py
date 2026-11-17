"""FastAPI entrypoint for Personality Playground Phase 1."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.chat.service import get_chat_service
from app.config import get_settings
from app.fixtures.data import list_fixtures
from app.llm.adapters import list_models
from app.personality.compiler import compile_personality
from app.personality.presets import PRESETS
from app.schemas import ChatRequest, ChatResponse, PreviewRequest
from app.tools.registry import list_tool_names

settings = get_settings()

app = FastAPI(
    title="Personality Playground API",
    version="0.1.0",
    description="Phase 1 Interactive MVP — synthetic banking rewards chatbot",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    models = list_models(settings)
    return {
        "status": "ok",
        "prompt_version": settings.prompt_version,
        "llm": {
            "openai": settings.openai_available,
            "google": settings.google_available,
            "any_live": settings.any_llm_available,
        },
        "models": models,
        "tools": list_tool_names(),
    }


@app.get("/api/fixtures")
def fixtures() -> dict:
    return list_fixtures()


@app.get("/api/presets")
def presets() -> dict:
    return {"presets": PRESETS, "default": "balanced"}


@app.get("/api/models")
def models() -> dict:
    return {"models": list_models(settings)}


@app.post("/api/personality/preview")
def personality_preview(body: PreviewRequest) -> dict:
    try:
        profile = body.profile.model_dump() if body.profile else None
        return compile_personality(profile, preset=body.preset)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest) -> ChatResponse:
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
def evaluation_status_stub() -> dict:
    """Phase 2 stub — batch evaluation is not implemented in MVP."""
    return {
        "phase": 2,
        "implemented": False,
        "message": "Batch evaluation, judges, and Measured overlays are reserved for Phase 2.",
    }
