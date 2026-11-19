"""Deterministic personality compiler — maps trait levels to prompt fragments."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .policy import BANKING_POLICY, POLICY_VERSION
from .presets import DEFAULT_PRESET, PRESETS

TRAIT_LEVELS = (1, 3, 5, 7, 9)
TraitName = Literal["exploration", "structure", "energy", "warmth", "steadiness"]

TRAIT_LABELS: dict[TraitName, str] = {
    "exploration": "Exploration",
    "structure": "Structure & Thoroughness",
    "energy": "Conversational Energy",
    "warmth": "Warmth & Accommodation",
    "steadiness": "Emotional Steadiness",
}

LEVEL_NAMES = {
    1: "Very Low",
    3: "Low",
    5: "Neutral",
    7: "High",
    9: "Very High",
}

_EXPLORATION = {
    1: "Give an immediate, direct answer only. Do not volunteer alternatives.",
    3: "Answer directly; mention at most one optional next step if clearly useful.",
    5: "Answer clearly and offer one optional next step the customer may take.",
    7: "After answering, briefly note 1–2 verified alternatives or tradeoffs from tools.",
    9: "Present 2–3 verified alternatives/tradeoffs grounded in tool data. Never invent options.",
}

_STRUCTURE = {
    1: "Keep replies brief. Include only essential caveats required by policy.",
    3: "Stay short but include eligibility caveats that affect the decision.",
    5: "Use organized detail: answer, key caveats, then optional next step.",
    7: "Structure with clear sections: answer, eligibility/caveats, concrete steps.",
    9: "Fully structured: eligibility, caveats, steps, and what to check next — without fluff.",
}

_ENERGY = {
    1: "Reserved tone. Minimal small talk. No exclamation-heavy phrasing.",
    3: "Calm and understated. Light acknowledgment is enough.",
    5: "Friendly but restrained. Professional warmth without cheerleading.",
    7: "Animated and proactive while staying professional; avoid over-asking.",
    9: "High conversational energy and proactive suggestions — never excessive enthusiasm or spam questions.",
}

_WARMTH = {
    1: "Direct and tactful. Skip emotional validation unless the customer is distressed.",
    3: "Politely direct; acknowledge the request without soft padding.",
    5: "Respectful and friendly. Match the customer's formality.",
    7: "Warm and accommodating; validate effort without flattery.",
    9: "Highly validating and supportive without flattery; never affirm false claims.",
}

_STEADINESS = {
    1: "Calm and matter-of-fact. Less overt reassurance.",
    3: "Steady; reassure only when uncertainty is clear.",
    5: "Measured and composed throughout.",
    7: "Offer clear grounding when the customer seems stressed or confused.",
    9: "Explicit grounding under stress: restate facts, next safe step, no anxious or hostile tone.",
}

_GUIDANCE = {
    "exploration": _EXPLORATION,
    "structure": _STRUCTURE,
    "energy": _ENERGY,
    "warmth": _WARMTH,
    "steadiness": _STEADINESS,
}


class TraitProfile(BaseModel):
    exploration: int = Field(default=5)
    structure: int = Field(default=7)
    energy: int = Field(default=5)
    warmth: int = Field(default=7)
    steadiness: int = Field(default=9)

    @field_validator(
        "exploration", "structure", "energy", "warmth", "steadiness", mode="before"
    )
    @classmethod
    def coerce_level(cls, v: int) -> int:
        level = int(v)
        if level not in TRAIT_LEVELS:
            # Snap to nearest allowed discrete level; ties round upward.
            level = min(
                TRAIT_LEVELS,
                key=lambda x: (abs(x - level), -x),
            )
        return level

    def as_dict(self) -> dict[str, int]:
        return self.model_dump()


def behavior_summary(profile: TraitProfile) -> str:
    """Short human-readable summary for the visualize panel."""
    parts = []
    for key, label in TRAIT_LABELS.items():
        level = getattr(profile, key)
        parts.append(f"{label}: {LEVEL_NAMES[level]} ({level})")
    return " · ".join(parts)


def trait_cards(profile: TraitProfile) -> list[dict]:
    """Scannable per-trait cards: level badge + short human description."""
    cards = []
    for key, label in TRAIT_LABELS.items():
        level = getattr(profile, key)
        cards.append(
            {
                "key": key,
                "label": label,
                "level": level,
                "level_name": LEVEL_NAMES[level],
                "description": _GUIDANCE[key][level],
            }
        )
    return cards


def compile_personality(
    profile: TraitProfile | dict | None = None,
    *,
    preset: str | None = None,
) -> dict:
    """
    Deterministically compile a requested personality into prompt fragments.

    Returns a stable structure used by preview + chat (prompt_version pinned in config).
    """
    if profile is None and preset:
        if preset not in PRESETS:
            raise ValueError(f"Unknown preset: {preset}")
        profile = TraitProfile(**PRESETS[preset])
    elif profile is None:
        profile = TraitProfile(**PRESETS[DEFAULT_PRESET])
        preset = DEFAULT_PRESET
    elif isinstance(profile, dict):
        profile = TraitProfile(**profile)

    assert isinstance(profile, TraitProfile)

    style_lines = []
    for key in TRAIT_LABELS:
        level = getattr(profile, key)
        style_lines.append(
            f"- {TRAIT_LABELS[key]} [{LEVEL_NAMES[level]} / {level}]: "
            f"{_GUIDANCE[key][level]}"
        )

    style_block = "\n".join(style_lines)
    system_prompt = (
        f"{BANKING_POLICY.strip()}\n\n"
        f"# Conversational Personality (style only — never overrides policy)\n"
        f"{style_block}\n"
    )

    return {
        "profile": profile.as_dict(),
        "preset": preset,
        "policy_version": POLICY_VERSION,
        "behavior_summary": behavior_summary(profile),
        "trait_cards": trait_cards(profile),
        "style_guidance": style_block,
        "system_prompt": system_prompt,
        "map_position": {
            "x": profile.exploration,  # Exploration
            "y": profile.energy,  # Conversational Energy
        },
        "radar": [
            {"trait": TRAIT_LABELS[k], "key": k, "value": getattr(profile, k)}
            for k in TRAIT_LABELS
        ],
    }
