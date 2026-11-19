"""Run preset × scenario demos with cache hit/miss (+ optional auto-judge)."""

from __future__ import annotations

from typing import Any

from app.chat.service import ChatService, get_chat_service
from app.config import Settings, get_settings
from app.demo.cache import DemoCacheStore
from app.evaluation.service import EvaluationService, get_evaluation_service
from app.fixtures.data import SCENARIOS
from app.llm.allowlist import is_openai_model_allowed
from app.personality.presets import PRESETS


class DemoLabService:
    def __init__(
        self,
        *,
        store: DemoCacheStore | None = None,
        chat: ChatService | None = None,
        settings: Settings | None = None,
        evaluation: EvaluationService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.store = store or DemoCacheStore(self.settings)
        self.chat = chat or get_chat_service()
        self.evaluation = evaluation or get_evaluation_service()

    def validate_selection(
        self, *, preset: str, customer_id: str, provider: str, model_id: str | None
    ) -> str:
        if preset not in PRESETS:
            raise ValueError(f"Unknown preset '{preset}'. Use one of: {', '.join(PRESETS)}")
        if customer_id not in ("customer_A", "customer_B"):
            raise ValueError("customer_id must be customer_A or customer_B")
        provider = (provider or "").lower().strip()
        if provider not in ("openai", "google", "demo"):
            raise ValueError("provider must be openai, google, or demo")
        mid = (model_id or "").strip()
        if provider == "openai":
            if not mid:
                mid = self.settings.openai_model
            if not is_openai_model_allowed(mid):
                raise ValueError(
                    f"OpenAI model '{mid}' is not allowlisted for experimentation."
                )
        elif provider == "google":
            mid = mid or self.settings.google_model
        else:
            mid = mid or "scripted-demo"
        return mid

    def list_cached(
        self,
        *,
        preset: str,
        customer_id: str,
        provider: str,
        model_id: str | None,
    ) -> dict[str, Any]:
        mid = self.validate_selection(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=model_id,
        )
        entries = self.store.list_entries(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=mid,
            prompt_version=self.settings.prompt_version,
        )
        scenarios = [
            s
            for s in SCENARIOS
            if customer_id in s.get("fixture_ids", [])
        ]
        by_scenario = {e["scenario_id"]: e for e in entries}
        report = self.evaluation.report_cards(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=mid,
        )
        score_by = {
            c["scenario_id"]: c["score"] for c in report["cards"] if c.get("score")
        }
        results = []
        for s in scenarios:
            sid = s["scenario_id"]
            hit = by_scenario.get(sid)
            results.append(
                {
                    "scenario_id": sid,
                    "title": s["title"],
                    "suggested_prompt": s["suggested_prompt"],
                    "category": s.get("category"),
                    "hit": hit is not None,
                    "entry": hit,
                    "score": score_by.get(sid),
                }
            )
        return {
            "preset": preset,
            "customer_id": customer_id,
            "provider": provider.lower().strip(),
            "model_id": mid,
            "prompt_version": self.settings.prompt_version,
            "results": results,
            "cached_count": sum(1 for r in results if r["hit"]),
            "scored_count": sum(1 for r in results if r.get("score")),
            "total": len(results),
            "aggregate": report["aggregate"],
            "model_aggregate": report["model_aggregate"],
            "judge_available": report["judge_available"],
            "judge_prompt_version": report["judge_prompt_version"],
        }

    async def run_all(
        self,
        *,
        preset: str,
        customer_id: str,
        provider: str,
        model_id: str | None,
        force: bool = False,
        scenario_ids: list[str] | None = None,
        auto_judge: bool = True,
    ) -> dict[str, Any]:
        mid = self.validate_selection(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=model_id,
        )
        scenarios = [
            s
            for s in SCENARIOS
            if customer_id in s.get("fixture_ids", [])
        ]
        if scenario_ids:
            wanted = set(scenario_ids)
            scenarios = [s for s in scenarios if s["scenario_id"] in wanted]

        results: list[dict[str, Any]] = []
        for s in scenarios:
            sid = s["scenario_id"]
            entry: dict[str, Any] | None = None
            cache_hit = False
            error = None

            if not force:
                hit = self.store.get(
                    preset=preset,
                    customer_id=customer_id,
                    scenario_id=sid,
                    provider=provider,
                    model_id=mid,
                    prompt_version=self.settings.prompt_version,
                )
                if hit:
                    entry = hit
                    cache_hit = True

            if entry is None:
                chat_result = await self.chat.chat(
                    message=s["suggested_prompt"],
                    customer_id=customer_id,
                    personality=None,
                    preset=preset,
                    provider=provider,
                    model_id=mid,
                    session_id=None,
                    scenario_id=sid,
                    reset_session=True,
                    settings=self.settings,
                )
                error = chat_result.get("error")
                if chat_result.get("metadata", {}).get("mode") != "error" and not error:
                    entry = self.store.put(
                        preset=preset,
                        customer_id=customer_id,
                        scenario_id=sid,
                        provider=provider,
                        model_id=mid,
                        reply=chat_result["reply"],
                        metadata=chat_result["metadata"],
                        prompt_version=self.settings.prompt_version,
                    )
                else:
                    # Still return the live/error reply without caching failures
                    entry = {
                        "cache_key": None,
                        "preset": preset,
                        "customer_id": customer_id,
                        "scenario_id": sid,
                        "provider": provider.lower().strip(),
                        "model_id": mid,
                        "prompt_version": self.settings.prompt_version,
                        "reply": chat_result["reply"],
                        "metadata": {
                            "mode": chat_result.get("metadata", {}).get("mode"),
                            "model_id": mid,
                            "provider": provider,
                            "fixture_id": customer_id,
                            "scenario_id": sid,
                            "preset": preset,
                            "tool_trace_summary": [],
                        },
                        "cached": False,
                    }

            score = None
            if auto_judge and entry and entry.get("reply") and not error:
                try:
                    score = await self.evaluation.score_entry(
                        preset=preset,
                        customer_id=customer_id,
                        scenario_id=sid,
                        provider=provider,
                        model_id=mid,
                        reply=entry["reply"],
                        user_message=s["suggested_prompt"],
                        metadata=entry.get("metadata") or {},
                        force=force,
                    )
                except Exception as exc:  # noqa: BLE001
                    score = {
                        "judged": False,
                        "skipped_reason": f"scoring failed: {exc}",
                        "traits": [],
                        "banking_checks": [],
                    }

            results.append(
                {
                    "scenario_id": sid,
                    "title": s["title"],
                    "suggested_prompt": s["suggested_prompt"],
                    "category": s.get("category"),
                    "cache_hit": cache_hit,
                    "entry": entry,
                    "error": error,
                    "score": score,
                }
            )

        scored = [r["score"] for r in results if r.get("score")]
        from app.evaluation.service import aggregate_scores

        report = self.evaluation.report_cards(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=mid,
        )
        return {
            "preset": preset,
            "customer_id": customer_id,
            "provider": provider.lower().strip(),
            "model_id": mid,
            "prompt_version": self.settings.prompt_version,
            "force": force,
            "results": results,
            "cache_hits": sum(1 for r in results if r["cache_hit"]),
            "cache_misses": sum(1 for r in results if not r["cache_hit"]),
            "scored_count": len(scored),
            "total": len(results),
            "aggregate": aggregate_scores(scored) if scored else report["aggregate"],
            "model_aggregate": report["model_aggregate"],
            "judge_available": report["judge_available"],
            "judge_prompt_version": report["judge_prompt_version"],
        }


_service: DemoLabService | None = None


def get_demo_lab_service() -> DemoLabService:
    global _service
    if _service is None:
        _service = DemoLabService()
    return _service
