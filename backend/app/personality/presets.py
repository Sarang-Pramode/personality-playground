"""Named personality presets (Balanced is the default)."""

PRESETS: dict[str, dict[str, int]] = {
    "balanced": {
        "exploration": 5,
        "structure": 7,
        "energy": 5,
        "warmth": 7,
        "steadiness": 9,
    },
    "concise": {
        "exploration": 3,
        "structure": 3,
        "energy": 3,
        "warmth": 5,
        "steadiness": 9,
    },
    "explorer": {
        "exploration": 9,
        "structure": 7,
        "energy": 5,
        "warmth": 7,
        "steadiness": 9,
    },
    "supportive": {
        "exploration": 5,
        "structure": 7,
        "energy": 5,
        "warmth": 9,
        "steadiness": 9,
    },
}

DEFAULT_PRESET = "balanced"
