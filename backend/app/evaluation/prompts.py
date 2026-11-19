"""Versioned independent-judge prompts (separate from the target model)."""

from __future__ import annotations

import json
from typing import Any

# Bump when judge instructions change — scores are keyed by this version.
JUDGE_PROMPT_VERSION = "independent-judge-v1"

JUDGE_SYSTEM = """You are an independent evaluation judge for a synthetic banking rewards assistant.
You are NOT the assistant under test. Score observed conversational style only.

Rules:
- Use ONLY the transcript (user + assistant) and the TARGET trait profile as context.
- Do NOT treat the assistant's self-description of its personality as evidence.
- Cite concrete behaviors from the assistant reply (quotes or paraphrases of what it did).
- Score each trait on the discrete scale 1, 3, 5, 7, 9 (Very Low → Very High).
- If evidence is insufficient for a trait, set unable_to_judge=true, score=null, and abstain_reason.
- Banking policy compliance is scored elsewhere — do not fold factual correctness into trait scores.
- Return JSON only, matching the schema exactly.
"""


def build_judge_user_payload(
    *,
    target_profile: dict[str, int],
    preset: str | None,
    scenario_id: str,
    user_message: str,
    assistant_reply: str,
    category: str | None = None,
) -> str:
    schema_hint = {
        "traits": [
            {
                "trait": "exploration|structure|energy|warmth|steadiness",
                "score": "1|3|5|7|9 or null",
                "cited_behaviors": ["short evidence strings from the reply"],
                "rationale": "one or two sentences",
                "unable_to_judge": False,
                "abstain_reason": None,
            }
        ],
        "overall_notes": "optional short note",
    }
    return (
        "Evaluate the assistant reply against the TARGET personality profile.\n\n"
        f"TARGET profile: {json.dumps(target_profile)}\n"
        f"Preset: {preset or 'custom'}\n"
        f"Scenario: {scenario_id}"
        + (f" (category: {category})" if category else "")
        + "\n\n"
        f"USER:\n{user_message}\n\n"
        f"ASSISTANT:\n{assistant_reply}\n\n"
        f"Respond with JSON only, shape:\n{json.dumps(schema_hint, indent=2)}\n"
        "Include all five traits: exploration, structure, energy, warmth, steadiness."
    )


def extract_json_object(text: str) -> dict[str, Any]:
    """Best-effort extract of a JSON object from a model reply."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("empty judge response")
    if raw.startswith("```"):
        lines = raw.splitlines()
        # drop first fence and optional language tag; drop last fence
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        data = json.loads(raw[start : end + 1])
        if isinstance(data, dict):
            return data
    raise ValueError("could not parse judge JSON")
