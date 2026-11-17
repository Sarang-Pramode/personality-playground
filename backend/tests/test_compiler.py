"""Tests for deterministic personality compiler."""

from app.personality.compiler import TraitProfile, compile_personality
from app.personality.presets import PRESETS
from app.personality.policy import POLICY_VERSION


def test_balanced_preset_default():
    out = compile_personality()
    assert out["profile"] == PRESETS["balanced"]
    assert out["policy_version"] == POLICY_VERSION
    assert "system_prompt" in out
    assert out["map_position"] == {"x": 5, "y": 5}


def test_explorer_vs_concise_differ():
    explorer = compile_personality(preset="explorer")
    concise = compile_personality(preset="concise")
    assert explorer["profile"]["exploration"] == 9
    assert concise["profile"]["exploration"] == 3
    assert explorer["system_prompt"] != concise["system_prompt"]
    assert "2–3 verified alternatives" in explorer["style_guidance"]
    assert "Answer directly" in concise["style_guidance"]


def test_policy_dominates_in_prompt():
    out = compile_personality(preset="concise")
    assert "Banking Rewards Policy" in out["system_prompt"]
    assert out["system_prompt"].index("Banking Rewards Policy") < out[
        "system_prompt"
    ].index("Conversational Personality")


def test_discrete_level_snap():
    # Off-grid values snap to nearest allowed level; ties round upward.
    profile = TraitProfile(exploration=4, structure=8, energy=2, warmth=6, steadiness=10)
    assert profile.exploration == 5
    assert profile.structure == 9
    assert profile.energy == 3
    assert profile.warmth == 7
    assert profile.steadiness == 9


def test_compile_is_deterministic():
    a = compile_personality(PRESETS["supportive"])
    b = compile_personality(PRESETS["supportive"])
    assert a == b


def test_radar_has_five_axes():
    out = compile_personality(preset="balanced")
    assert len(out["radar"]) == 5
    keys = {r["key"] for r in out["radar"]}
    assert keys == {"exploration", "structure", "energy", "warmth", "steadiness"}
