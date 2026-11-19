"""Persist judge + banking scores in Postgres/SQLite."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_session_factory
from app.demo.cache import make_cache_key
from app.evaluation.prompts import JUDGE_PROMPT_VERSION
from app.evaluation.schema import JudgeReport


def make_score_key(
    *,
    preset: str,
    customer_id: str,
    scenario_id: str,
    provider: str,
    model_id: str,
    prompt_version: str,
    judge_prompt_version: str = JUDGE_PROMPT_VERSION,
) -> str:
    return "|".join(
        [
            preset.strip(),
            customer_id.strip(),
            scenario_id.strip(),
            provider.strip().lower(),
            model_id.strip(),
            prompt_version.strip(),
            judge_prompt_version.strip(),
        ]
    )


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class EvalScoreStore:
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
        judge_prompt_version: str = JUDGE_PROMPT_VERSION,
    ) -> dict[str, Any] | None:
        pv = prompt_version or self.settings.prompt_version
        key = make_score_key(
            preset=preset,
            customer_id=customer_id,
            scenario_id=scenario_id,
            provider=provider,
            model_id=model_id,
            prompt_version=pv,
            judge_prompt_version=judge_prompt_version,
        )
        session = self._session()
        try:
            row = session.execute(
                text(
                    """
                    SELECT score_key, cache_key, preset, customer_id, scenario_id,
                           provider, model_id, prompt_version, judge_prompt_version,
                           judge_model, target_profile_json, trait_scores_json,
                           banking_checks_json, judge_raw_json, created_at, updated_at
                    FROM eval_scores
                    WHERE score_key = :key
                    """
                ),
                {"key": key},
            ).mappings().first()
            if not row:
                return None
            return self._row_to_entry(dict(row))
        finally:
            session.close()

    def list_for_selection(
        self,
        *,
        preset: str,
        customer_id: str,
        provider: str,
        model_id: str,
        prompt_version: str | None = None,
        judge_prompt_version: str = JUDGE_PROMPT_VERSION,
    ) -> list[dict[str, Any]]:
        pv = prompt_version or self.settings.prompt_version
        session = self._session()
        try:
            rows = session.execute(
                text(
                    """
                    SELECT score_key, cache_key, preset, customer_id, scenario_id,
                           provider, model_id, prompt_version, judge_prompt_version,
                           judge_model, target_profile_json, trait_scores_json,
                           banking_checks_json, judge_raw_json, created_at, updated_at
                    FROM eval_scores
                    WHERE preset = :preset
                      AND customer_id = :customer_id
                      AND provider = :provider
                      AND model_id = :model_id
                      AND prompt_version = :prompt_version
                      AND judge_prompt_version = :judge_prompt_version
                    ORDER BY scenario_id
                    """
                ),
                {
                    "preset": preset,
                    "customer_id": customer_id,
                    "provider": provider.strip().lower(),
                    "model_id": model_id,
                    "prompt_version": pv,
                    "judge_prompt_version": judge_prompt_version,
                },
            ).mappings().all()
            return [self._row_to_entry(dict(r)) for r in rows]
        finally:
            session.close()

    def list_for_model(
        self,
        *,
        provider: str,
        model_id: str,
        prompt_version: str | None = None,
        judge_prompt_version: str = JUDGE_PROMPT_VERSION,
    ) -> list[dict[str, Any]]:
        pv = prompt_version or self.settings.prompt_version
        session = self._session()
        try:
            rows = session.execute(
                text(
                    """
                    SELECT score_key, cache_key, preset, customer_id, scenario_id,
                           provider, model_id, prompt_version, judge_prompt_version,
                           judge_model, target_profile_json, trait_scores_json,
                           banking_checks_json, judge_raw_json, created_at, updated_at
                    FROM eval_scores
                    WHERE provider = :provider
                      AND model_id = :model_id
                      AND prompt_version = :prompt_version
                      AND judge_prompt_version = :judge_prompt_version
                    ORDER BY preset, customer_id, scenario_id
                    """
                ),
                {
                    "provider": provider.strip().lower(),
                    "model_id": model_id,
                    "prompt_version": pv,
                    "judge_prompt_version": judge_prompt_version,
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
        target_profile: dict[str, int],
        report: JudgeReport,
        prompt_version: str | None = None,
    ) -> dict[str, Any]:
        pv = prompt_version or self.settings.prompt_version
        jpv = report.judge_prompt_version or JUDGE_PROMPT_VERSION
        key = make_score_key(
            preset=preset,
            customer_id=customer_id,
            scenario_id=scenario_id,
            provider=provider,
            model_id=model_id,
            prompt_version=pv,
            judge_prompt_version=jpv,
        )
        cache_key = make_cache_key(
            preset=preset,
            customer_id=customer_id,
            scenario_id=scenario_id,
            provider=provider,
            model_id=model_id,
            prompt_version=pv,
        )
        now = _utcnow()
        trait_scores = [t.model_dump() for t in report.traits]
        banking = [c.model_dump() for c in report.banking_checks]
        raw = report.model_dump()
        session = self._session()
        try:
            session.execute(
                text(
                    """
                    INSERT INTO eval_scores (
                        score_key, cache_key, preset, customer_id, scenario_id,
                        provider, model_id, prompt_version, judge_prompt_version,
                        judge_model, target_profile_json, trait_scores_json,
                        banking_checks_json, judge_raw_json, created_at, updated_at
                    ) VALUES (
                        :score_key, :cache_key, :preset, :customer_id, :scenario_id,
                        :provider, :model_id, :prompt_version, :judge_prompt_version,
                        :judge_model, :target_profile_json, :trait_scores_json,
                        :banking_checks_json, :judge_raw_json, :created_at, :updated_at
                    )
                    ON CONFLICT(score_key) DO UPDATE SET
                        cache_key = excluded.cache_key,
                        judge_model = excluded.judge_model,
                        target_profile_json = excluded.target_profile_json,
                        trait_scores_json = excluded.trait_scores_json,
                        banking_checks_json = excluded.banking_checks_json,
                        judge_raw_json = excluded.judge_raw_json,
                        updated_at = excluded.updated_at
                    """
                ),
                {
                    "score_key": key,
                    "cache_key": cache_key,
                    "preset": preset,
                    "customer_id": customer_id,
                    "scenario_id": scenario_id,
                    "provider": provider.strip().lower(),
                    "model_id": model_id,
                    "prompt_version": pv,
                    "judge_prompt_version": jpv,
                    "judge_model": report.judge_model,
                    "target_profile_json": json.dumps(target_profile, ensure_ascii=False),
                    "trait_scores_json": json.dumps(trait_scores, ensure_ascii=False),
                    "banking_checks_json": json.dumps(banking, ensure_ascii=False),
                    "judge_raw_json": json.dumps(raw, ensure_ascii=False),
                    "created_at": now,
                    "updated_at": now,
                },
            )
            session.commit()
            return {
                "score_key": key,
                "cache_key": cache_key,
                "preset": preset,
                "customer_id": customer_id,
                "scenario_id": scenario_id,
                "provider": provider.strip().lower(),
                "model_id": model_id,
                "prompt_version": pv,
                "judge_prompt_version": jpv,
                "judge_model": report.judge_model,
                "target_profile": target_profile,
                "traits": trait_scores,
                "banking_checks": banking,
                "judged": report.judged,
                "skipped_reason": report.skipped_reason,
                "measured_profile": report.measured_profile(),
                "overall_notes": report.overall_notes,
                "created_at": now,
                "updated_at": now,
            }
        finally:
            session.close()

    def _row_to_entry(self, row: dict[str, Any]) -> dict[str, Any]:
        def _loads(s: str | None, default: Any) -> Any:
            try:
                return json.loads(s or "") if s else default
            except json.JSONDecodeError:
                return default

        traits = _loads(row.get("trait_scores_json"), [])
        banking = _loads(row.get("banking_checks_json"), [])
        target = _loads(row.get("target_profile_json"), {})
        raw = _loads(row.get("judge_raw_json"), {})
        judged = bool(raw.get("judged", True)) if isinstance(raw, dict) else True
        measured = None
        if judged and isinstance(traits, list) and traits:
            tmp: dict[str, int] = {}
            ok = True
            for t in traits:
                if not isinstance(t, dict) or t.get("unable_to_judge") or t.get("score") is None:
                    ok = False
                    break
                tmp[str(t["trait"])] = int(t["score"])
            if ok and len(tmp) == 5:
                measured = tmp
        return {
            "score_key": row["score_key"],
            "cache_key": row.get("cache_key"),
            "preset": row["preset"],
            "customer_id": row["customer_id"],
            "scenario_id": row["scenario_id"],
            "provider": row["provider"],
            "model_id": row["model_id"],
            "prompt_version": row["prompt_version"],
            "judge_prompt_version": row["judge_prompt_version"],
            "judge_model": row.get("judge_model"),
            "target_profile": target,
            "traits": traits,
            "banking_checks": banking,
            "judged": judged,
            "skipped_reason": raw.get("skipped_reason") if isinstance(raw, dict) else None,
            "measured_profile": measured,
            "overall_notes": raw.get("overall_notes") if isinstance(raw, dict) else None,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
