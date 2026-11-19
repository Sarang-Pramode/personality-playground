"""OpenAI experimentation allowlist — exclude huge / expensive flagships."""

from __future__ import annotations

# Experimentation models for Personality Playground comparisons.
# Include mid-tier gpt-4o when requested; keep cheaper mini/nano options.
# Do NOT add shut-down IDs (gpt-4.1-nano, o4-mini as of Oct 2026) or
# expensive flagships (o1/o3, gpt-4.1 full, gpt-5/gpt-6 sol/astra, etc.).
OPENAI_ALLOWED_MODELS: tuple[str, ...] = (
    "gpt-4o-mini",
    "gpt-4.1-mini",
    "gpt-5.4-nano",
    "gpt-5.4-mini",
    "gpt-4o",
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
