"""Judge payload schema + JSON extraction tests."""

import pytest

from app.evaluation.prompts import extract_json_object
from app.evaluation.schema import (
    JudgeReport,
    TraitJudgment,
    validate_judge_payload,
)


def test_validate_judge_payload_happy_path():
    payload = {
        "traits": [
            {
                "trait": "exploration",
                "score": 7,
                "cited_behaviors": ["listed two redemption options"],
                "rationale": "Offered alternatives",
                "unable_to_judge": False,
            },
            {
                "trait": "structure",
                "score": 5,
                "cited_behaviors": ["organized bullets"],
                "rationale": "Clear sections",
                "unable_to_judge": False,
            },
            {
                "trait": "energy",
                "score": 3,
                "cited_behaviors": ["reserved greeting"],
                "rationale": "Calm tone",
                "unable_to_judge": False,
            },
            {
                "trait": "warmth",
                "score": 5,
                "cited_behaviors": ["polite hello"],
                "rationale": "Friendly",
                "unable_to_judge": False,
            },
            {
                "trait": "steadiness",
                "score": 9,
                "cited_behaviors": ["restated balance facts"],
                "rationale": "Grounded",
                "unable_to_judge": False,
            },
        ],
        "overall_notes": "ok",
    }
    traits = validate_judge_payload(payload)
    assert len(traits) == 5
    assert traits[0].trait == "exploration"
    assert traits[0].score == 7


def test_unable_to_judge_clears_score():
    t = TraitJudgment(
        trait="energy",
        score=7,
        unable_to_judge=True,
        abstain_reason="too short",
    )
    assert t.score is None
    assert t.unable_to_judge is True


def test_score_snaps_to_discrete():
    t = TraitJudgment(trait="warmth", score=6)
    assert t.score == 7  # nearest, ties round up via (-x) key


def test_missing_trait_raises():
    with pytest.raises(ValueError, match="missing traits"):
        validate_judge_payload(
            {
                "traits": [
                    {"trait": "exploration", "score": 5, "unable_to_judge": False}
                ]
            }
        )


def test_measured_profile_requires_all_scores():
    traits = [
        TraitJudgment(trait="exploration", score=5),
        TraitJudgment(trait="structure", score=5),
        TraitJudgment(trait="energy", score=5),
        TraitJudgment(trait="warmth", score=5),
        TraitJudgment(trait="steadiness", unable_to_judge=True),
    ]
    report = JudgeReport(
        judge_prompt_version="independent-judge-v1",
        judge_model="gpt-4o-mini",
        traits=traits,
        judged=True,
    )
    assert report.measured_profile() is None

    full = [
        TraitJudgment(trait=t, score=5)
        for t in ("exploration", "structure", "energy", "warmth", "steadiness")
    ]
    report2 = JudgeReport(
        judge_prompt_version="independent-judge-v1",
        judge_model="gpt-4o-mini",
        traits=full,
        judged=True,
    )
    assert report2.measured_profile() == {
        "exploration": 5,
        "structure": 5,
        "energy": 5,
        "warmth": 5,
        "steadiness": 5,
    }


def test_extract_json_object_fenced():
    text = '```json\n{"traits": [], "overall_notes": "x"}\n```'
    data = extract_json_object(text)
    assert data["overall_notes"] == "x"
