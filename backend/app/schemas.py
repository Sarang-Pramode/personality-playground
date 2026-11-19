"""API request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PersonalityProfile(BaseModel):
    exploration: int = 5
    structure: int = 7
    energy: int = 5
    warmth: int = 7
    steadiness: int = 9


class PreviewRequest(BaseModel):
    profile: PersonalityProfile | None = None
    preset: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    customer_id: Literal["customer_A", "customer_B"] = "customer_A"
    scenario_id: str | None = None
    session_id: str | None = None
    reset_session: bool = False
    personality: PersonalityProfile | None = None
    preset: str | None = None
    provider: Literal["openai", "google", "demo"] = "demo"
    model_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    run_id: str
    session_id: str
    error: str | None = None
    metadata: dict[str, Any]


class DemoCacheQuery(BaseModel):
    preset: str = "balanced"
    customer_id: Literal["customer_A", "customer_B"] = "customer_A"
    provider: Literal["openai", "google", "demo"] = "demo"
    model_id: str | None = None


class DemoRunRequest(BaseModel):
    preset: str = "balanced"
    customer_id: Literal["customer_A", "customer_B"] = "customer_A"
    provider: Literal["openai", "google", "demo"] = "demo"
    model_id: str | None = None
    force: bool = False
    scenario_ids: list[str] | None = None
