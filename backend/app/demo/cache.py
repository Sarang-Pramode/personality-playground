"""Postgres/SQLite-backed demo result cache (reply + safe metadata only)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session_factory


def make_cache_key(
    *,
    preset: str,
    customer_id: str,
    scenario_id: str,
    provider: str,
    model_id: str,
    prompt_version: str,
) -> str:
    parts = [
        preset.strip(),
        customer_id.strip(),
        scenario_id.strip(),
        provider.strip().lower(),
        model_id.strip(),
        prompt_version.strip(),
    ]
    return "|".join(parts)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize_tool_traces(traces: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Strip bulky tool payloads — keep names + ok for inspector/demo UI."""
    summary: list[dict[str, Any]] = []
    for t in traces or []:
        result = t.get("result")
        ok = True
        error = None
        if isinstance(result, dict):
            ok = bool(result.get("ok", True))
            error = result.get("error")
        summary.append(
            {
                "tool": t.get("tool"),
                "ok": ok,
                "error": error,
            }
        )
    return summary


def safe_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Persist only non-secret demo metadata."""
    return {
        "profile": meta.get("profile"),
        "preset": meta.get("preset"),
        "prompt_version": meta.get("prompt_version"),
        "policy_version": meta.get("policy_version"),
        "fixture_id": meta.get("fixture_id"),
        "scenario_id": meta.get("scenario_id"),
        "model_id": meta.get("model_id"),
        "provider": meta.get("provider"),
        "mode": meta.get("mode"),
        "model_label": meta.get("model_label"),
        "behavior_summary": meta.get("behavior_summary"),
        "tool_trace_summary": summarize_tool_traces(meta.get("tool_traces")),
        "run_id": meta.get("run_id"),
    }


class DemoCacheStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _session(self) -> Session:
        return get_session_factory(self.settings)()

    def get(
        self,
        *,
        preset: str,
        customer_id: str,
        scenario_id: str,
        provider: str,
        model_id: str,
        prompt_version: str | None = None,
    ) -> dict[str, Any] | None:
        pv = prompt_version or self.settings.prompt_version
        key = make_cache_key(
            preset=preset,
            customer_id=customer_id,
            scenario_id=scenario_id,
            provider=provider,
            model_id=model_id,
            prompt_version=pv,
        )
        session = self._session()
        try:
            row = session.execute(
                text(
                    """
                    SELECT cache_key, preset, customer_id, scenario_id, provider,
                           model_id, prompt_version, reply, metadata_json,
                           created_at, updated_at
                    FROM demo_cache
                    WHERE cache_key = :key
                    """
                ),
                {"key": key},
            ).mappings().first()
            if not row:
                return None
            return self._row_to_entry(dict(row))
        finally:
            session.close()

    def list_entries(
        self,
        *,
        preset: str,
        customer_id: str,
        provider: str,
        model_id: str,
        prompt_version: str | None = None,
    ) -> list[dict[str, Any]]:
        pv = prompt_version or self.settings.prompt_version
        session = self._session()
        try:
            rows = session.execute(
                text(
                    """
                    SELECT cache_key, preset, customer_id, scenario_id, provider,
                           model_id, prompt_version, reply, metadata_json,
                           created_at, updated_at
                    FROM demo_cache
                    WHERE preset = :preset
                      AND customer_id = :customer_id
                      AND provider = :provider
                      AND model_id = :model_id
                      AND prompt_version = :prompt_version
                    ORDER BY scenario_id
                    """
                ),
                {
                    "preset": preset,
                    "customer_id": customer_id,
                    "provider": provider.strip().lower(),
                    "model_id": model_id,
                    "prompt_version": pv,
                },
            ).mappings().all()
            return [self._row_to_entry(dict(r)) for r in rows]
        finally:
            session.close()

    def put(
        self,
        *,
        preset: str,
        customer_id: str,
        scenario_id: str,
        provider: str,
        model_id: str,
        reply: str,
        metadata: dict[str, Any],
        prompt_version: str | None = None,
    ) -> dict[str, Any]:
        pv = prompt_version or self.settings.prompt_version
        key = make_cache_key(
            preset=preset,
            customer_id=customer_id,
            scenario_id=scenario_id,
            provider=provider,
            model_id=model_id,
            prompt_version=pv,
        )
        now = _utcnow()
        meta = safe_metadata(metadata)
        payload = json.dumps(meta, ensure_ascii=False)
        session = self._session()
        try:
            # Upsert works on SQLite 3.24+ and Postgres
            session.execute(
                text(
                    """
                    INSERT INTO demo_cache (
                        cache_key, preset, customer_id, scenario_id, provider,
                        model_id, prompt_version, reply, metadata_json,
                        created_at, updated_at
                    ) VALUES (
                        :cache_key, :preset, :customer_id, :scenario_id, :provider,
                        :model_id, :prompt_version, :reply, :metadata_json,
                        :created_at, :updated_at
                    )
                    ON CONFLICT(cache_key) DO UPDATE SET
                        reply = excluded.reply,
                        metadata_json = excluded.metadata_json,
                        updated_at = excluded.updated_at
                    """
                ),
                {
                    "cache_key": key,
                    "preset": preset,
                    "customer_id": customer_id,
                    "scenario_id": scenario_id,
                    "provider": provider.strip().lower(),
                    "model_id": model_id,
                    "prompt_version": pv,
                    "reply": reply,
                    "metadata_json": payload,
                    "created_at": now,
                    "updated_at": now,
                },
            )
            session.commit()
            return {
                "cache_key": key,
                "preset": preset,
                "customer_id": customer_id,
                "scenario_id": scenario_id,
                "provider": provider.strip().lower(),
                "model_id": model_id,
                "prompt_version": pv,
                "reply": reply,
                "metadata": meta,
                "created_at": now,
                "updated_at": now,
                "cached": True,
            }
        finally:
            session.close()

    def _row_to_entry(self, row: dict[str, Any]) -> dict[str, Any]:
        try:
            meta = json.loads(row["metadata_json"] or "{}")
        except json.JSONDecodeError:
            meta = {}
        return {
            "cache_key": row["cache_key"],
            "preset": row["preset"],
            "customer_id": row["customer_id"],
            "scenario_id": row["scenario_id"],
            "provider": row["provider"],
            "model_id": row["model_id"],
            "prompt_version": row["prompt_version"],
            "reply": row["reply"],
            "metadata": meta,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "cached": True,
        }
