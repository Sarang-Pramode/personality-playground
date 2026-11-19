"""Independent LLM judge — allowlisted small OpenAI, separate from target chat."""

from __future__ import annotations

from typing import Any

from app.config import Settings, get_settings
from app.evaluation.prompts import (
    JUDGE_PROMPT_VERSION,
    JUDGE_SYSTEM,
    build_judge_user_payload,
    extract_json_object,
)
from app.evaluation.schema import JudgeReport, TraitJudgment, validate_judge_payload
from app.llm.allowlist import OPENAI_ALLOWED_MODELS, is_openai_model_allowed, resolve_openai_model


class JudgeUnavailableError(RuntimeError):
    """Raised when no allowlisted judge model can run."""


def resolve_judge_model(settings: Settings) -> str:
    """Prefer JUDGE_MODEL / settings.judge_model if allowlisted, else openai_model."""
    requested = (settings.judge_model or "").strip() or settings.openai_model
    if not is_openai_model_allowed(requested):
        requested = resolve_openai_model(None, settings.openai_model)
    if requested not in OPENAI_ALLOWED_MODELS:
        requested = OPENAI_ALLOWED_MODELS[0]
    return requested


async def run_independent_judge(
    *,
    target_profile: dict[str, int],
    preset: str | None,
    scenario_id: str,
    user_message: str,
    assistant_reply: str,
    category: str | None = None,
    settings: Settings | None = None,
) -> JudgeReport:
    """
    Call a small OpenAI model as an independent judge.

    Does not invent scores when the judge is unavailable — returns judged=False.
    """
    settings = settings or get_settings()
    if not settings.openai_available:
        return JudgeReport(
            judge_prompt_version=JUDGE_PROMPT_VERSION,
            judge_model=None,
            traits=[
                TraitJudgment(
                    trait=t,  # type: ignore[arg-type]
                    score=None,
                    unable_to_judge=True,
                    abstain_reason="judge unavailable: OPENAI_API_KEY not set",
                )
                for t in (
                    "exploration",
                    "structure",
                    "energy",
                    "warmth",
                    "steadiness",
                )
            ],
            judged=False,
            skipped_reason="OPENAI_API_KEY not configured — personality scores withheld",
        )

    model_id = resolve_judge_model(settings)
    user_payload = build_judge_user_payload(
        target_profile=target_profile,
        preset=preset,
        scenario_id=scenario_id,
        user_message=user_message,
        assistant_reply=assistant_reply,
        category=category,
    )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        completion = await client.chat.completions.create(
            model=model_id,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM},
                {"role": "user", "content": user_payload},
            ],
        )
        content = completion.choices[0].message.content or ""
        payload = extract_json_object(content)
        traits = validate_judge_payload(payload)
        notes = payload.get("overall_notes")
        return JudgeReport(
            judge_prompt_version=JUDGE_PROMPT_VERSION,
            judge_model=model_id,
            traits=traits,
            overall_notes=notes if isinstance(notes, str) else None,
            judged=True,
        )
    except Exception as exc:  # noqa: BLE001 — surface as skipped, never fabricate
        return JudgeReport(
            judge_prompt_version=JUDGE_PROMPT_VERSION,
            judge_model=model_id,
            traits=[
                TraitJudgment(
                    trait=t,  # type: ignore[arg-type]
                    score=None,
                    unable_to_judge=True,
                    abstain_reason=f"judge error: {exc}",
                )
                for t in (
                    "exploration",
                    "structure",
                    "energy",
                    "warmth",
                    "steadiness",
                )
            ],
            judged=False,
            skipped_reason=f"judge failed: {exc}",
        )


def empty_report(*, reason: str, judge_model: str | None = None) -> JudgeReport:
    return JudgeReport(
        judge_prompt_version=JUDGE_PROMPT_VERSION,
        judge_model=judge_model,
        traits=[
            TraitJudgment(
                trait=t,  # type: ignore[arg-type]
                score=None,
                unable_to_judge=True,
                abstain_reason=reason,
            )
            for t in (
                "exploration",
                "structure",
                "energy",
                "warmth",
                "steadiness",
            )
        ],
        judged=False,
        skipped_reason=reason,
    )
