"""OpenAI experimentation allowlist — exclude large / expensive models."""

from __future__ import annotations

# Small / mid models only. Do not add o1, o3, gpt-4o (full), gpt-4.1 (full), etc.
OPENAI_ALLOWED_MODELS: tuple[str, ...] = (
    "gpt-4o-mini",
    "gpt-4.1-mini",
)

OPENAI_ALLOWED_MODEL_SET = frozenset(OPENAI_ALLOWED_MODELS)


def is_openai_model_allowed(model_id: str | None) -> bool:
    if not model_id:
        return False
    return model_id.strip() in OPENAI_ALLOWED_MODEL_SET


def resolve_openai_model(requested: str | None, default: str) -> str:
    """Pick an allowlisted model; fall back to default or first allowlisted id."""
    if requested and is_openai_model_allowed(requested):
        return requested.strip()
    if is_openai_model_allowed(default):
        return default.strip()
    return OPENAI_ALLOWED_MODELS[0]
