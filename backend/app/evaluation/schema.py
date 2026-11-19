"""Judge output schema — validated before persistence or Measured overlays."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

TRAIT_KEYS = ("exploration", "structure", "energy", "warmth", "steadiness")
TRAIT_LEVELS = (1, 3, 5, 7, 9)


class TraitJudgment(BaseModel):
    trait: Literal[
        "exploration", "structure", "energy", "warmth", "steadiness"
    ]
    score: int | None = None
    cited_behaviors: list[str] = Field(default_factory=list)
    rationale: str = ""
    unable_to_judge: bool = False
    abstain_reason: str | None = None

    @field_validator("score")
    @classmethod
    def score_discrete_or_none(cls, v: int | None) -> int | None:
        if v is None:
            return None
        level = int(v)
        if level not in TRAIT_LEVELS:
            level = min(TRAIT_LEVELS, key=lambda x: (abs(x - level), -x))
        return level

    @model_validator(mode="after")
    def abstain_clears_score(self) -> TraitJudgment:
        if self.unable_to_judge or self.score is None:
            self.score = None
            if self.unable_to_judge and not self.abstain_reason:
                self.abstain_reason = "insufficient evidence"
        return self


class BankingCheckResult(BaseModel):
    check_id: str
    passed: bool
    detail: str
    evidence: list[str] = Field(default_factory=list)


class JudgeReport(BaseModel):
    judge_prompt_version: str
    judge_model: str | None
    traits: list[TraitJudgment]
    overall_notes: str | None = None
    banking_checks: list[BankingCheckResult] = Field(default_factory=list)
    judged: bool = True
    skipped_reason: str | None = None

    def measured_profile(self) -> dict[str, int] | None:
        """Return Observed scores only when every trait has a real score."""
        if not self.judged:
            return None
        out: dict[str, int] = {}
        for t in self.traits:
            if t.unable_to_judge or t.score is None:
                return None
            out[t.trait] = t.score
        if len(out) != len(TRAIT_KEYS):
            return None
        return out

    def partial_measured(self) -> dict[str, int | None]:
        return {t.trait: t.score for t in self.traits}


def validate_judge_payload(payload: dict[str, Any]) -> list[TraitJudgment]:
    """Parse LLM JSON into TraitJudgment list; raises ValueError on bad shape."""
    traits_raw = payload.get("traits")
    if not isinstance(traits_raw, list) or not traits_raw:
        raise ValueError("judge payload must include a non-empty traits list")

    by_trait: dict[str, TraitJudgment] = {}
    for item in traits_raw:
        if not isinstance(item, dict):
            raise ValueError("each trait judgment must be an object")
        judgment = TraitJudgment.model_validate(item)
        by_trait[judgment.trait] = judgment

    missing = [k for k in TRAIT_KEYS if k not in by_trait]
    if missing:
        raise ValueError(f"judge payload missing traits: {', '.join(missing)}")

    return [by_trait[k] for k in TRAIT_KEYS]
