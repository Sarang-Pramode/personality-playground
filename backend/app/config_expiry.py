"""OpenAI API key expiry countdown helpers (date only — never the key)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any


def parse_expiry_date(raw: str | None) -> date | None:
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    # Accept YYYY-MM-DD or full ISO datetime
    try:
        if "T" in text:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return dt.date()
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def openai_key_expiry_payload(expires_at_raw: str | None) -> dict[str, Any] | None:
    expires = parse_expiry_date(expires_at_raw)
    if expires is None:
        return None
    today = datetime.now(timezone.utc).date()
    days_remaining = (expires - today).days
    return {
        "expires_at": expires.isoformat(),
        "days_remaining": days_remaining,
        "warn": days_remaining < 2,
        "expired": days_remaining < 0,
    }
