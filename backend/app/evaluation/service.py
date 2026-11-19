"""Orchestrate banking checks + independent judges for demo lab report cards."""

from __future__ import annotations

from typing import Any

from app.config import Settings, get_settings
from app.demo.cache import DemoCacheStore
from app.evaluation.banking_checks import run_banking_checks
from app.evaluation.judge import run_independent_judge
from app.evaluation.prompts import JUDGE_PROMPT_VERSION
from app.evaluation.schema import JudgeReport
from app.evaluation.store import EvalScoreStore
from app.fixtures.data import SCENARIOS
from app.personality.presets import PRESETS


def _scenario_meta(scenario_id: str) -> dict[str, Any]:
    for s in SCENARIOS:
        if s["scenario_id"] == scenario_id:
            return s
    return {
        "scenario_id": scenario_id,
        "title": scenario_id,
        "suggested_prompt": "",
        "category": None,
    }


def _target_profile(preset: str) -> dict[str, int]:
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset '{preset}'")
    return dict(PRESETS[preset])


def aggregate_scores(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate measured trait means + banking pass rate across scored runs."""
    trait_sums: dict[str, list[int]] = {
        "exploration": [],
        "structure": [],
        "energy": [],
        "warmth": [],
        "steadiness": [],
    }
    banking_pass = 0
    banking_total = 0
    judged_count = 0
    for e in entries:
        if e.get("judged"):
            judged_count += 1
            for t in e.get("traits") or []:
                if (
                    isinstance(t, dict)
                    and not t.get("unable_to_judge")
                    and t.get("score") is not None
                ):
                    trait_sums.setdefault(t["trait"], []).append(int(t["score"]))
        for c in e.get("banking_checks") or []:
            if isinstance(c, dict):
                banking_total += 1
                if c.get("passed"):
                    banking_pass += 1

    means: dict[str, float | None] = {}
    for k, vals in trait_sums.items():
        means[k] = round(sum(vals) / len(vals), 2) if vals else None

    measured = None
    if all(v is not None for v in means.values()):
        # Snap display means to nearest discrete for radar overlay only when complete
        measured = {k: int(round(v)) for k, v in means.items() if v is not None}  # type: ignore[arg-type]
        # Keep raw means separately
    return {
        "scored_runs": len(entries),
        "judged_runs": judged_count,
        "trait_means": means,
        "measured_profile_approx": measured if judged_count else None,
        "banking_pass_rate": (
            round(banking_pass / banking_total, 3) if banking_total else None
        ),
        "banking_passed": banking_pass,
        "banking_total": banking_total,
    }


class EvaluationService:
    def __init__(
        self,
        *,
        score_store: EvalScoreStore | None = None,
        cache_store: DemoCacheStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.scores = score_store or EvalScoreStore(self.settings)
        self.cache = cache_store or DemoCacheStore(self.settings)

    def status(self) -> dict[str, Any]:
        return {
            "phase": 2,
            "implemented": True,
            "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "judge_model": (self.settings.judge_model or self.settings.openai_model),
            "judge_available": self.settings.openai_available,
            "message": (
                "Independent judges + banking checks available. "
                "Measured overlays appear only after real judge scores exist."
                if self.settings.openai_available
                else "Banking checks available; personality judges need OPENAI_API_KEY."
            ),
        }

    async def score_entry(
        self,
        *,
        preset: str,
        customer_id: str,
        scenario_id: str,
        provider: str,
        model_id: str,
        reply: str,
        user_message: str | None = None,
        metadata: dict[str, Any] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        meta = metadata or {}
        if not force:
            existing = self.scores.get(
                preset=preset,
                customer_id=customer_id,
                scenario_id=scenario_id,
                provider=provider,
                model_id=model_id,
                prompt_version=self.settings.prompt_version,
            )
            if existing:
                return existing

        target = _target_profile(preset)
        scenario = _scenario_meta(scenario_id)
        prompt = user_message or scenario.get("suggested_prompt") or ""
        tool_summary = meta.get("tool_trace_summary") or []
        mode = meta.get("mode")

        banking = run_banking_checks(
            reply=reply,
            customer_id=customer_id,
            scenario_id=scenario_id,
            tool_trace_summary=tool_summary,
            mode=mode,
        )

        report: JudgeReport = await run_independent_judge(
            target_profile=target,
            preset=preset,
            scenario_id=scenario_id,
            user_message=prompt,
            assistant_reply=reply,
            category=scenario.get("category"),
            settings=self.settings,
        )
        report.banking_checks = banking

        return self.scores.put(
            preset=preset,
            customer_id=customer_id,
            scenario_id=scenario_id,
            provider=provider,
            model_id=model_id,
            target_profile=target,
            report=report,
            prompt_version=self.settings.prompt_version,
        )

    async def score_cached_selection(
        self,
        *,
        preset: str,
        customer_id: str,
        provider: str,
        model_id: str,
        force: bool = False,
        scenario_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        entries = self.cache.list_entries(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=model_id,
            prompt_version=self.settings.prompt_version,
        )
        if scenario_ids:
            wanted = set(scenario_ids)
            entries = [e for e in entries if e["scenario_id"] in wanted]

        results: list[dict[str, Any]] = []
        for e in entries:
            scenario = _scenario_meta(e["scenario_id"])
            scored = await self.score_entry(
                preset=preset,
                customer_id=customer_id,
                scenario_id=e["scenario_id"],
                provider=provider,
                model_id=model_id,
                reply=e["reply"],
                user_message=scenario.get("suggested_prompt"),
                metadata=e.get("metadata") or {},
                force=force,
            )
            results.append(
                {
                    "scenario_id": e["scenario_id"],
                    "title": scenario.get("title"),
                    "category": scenario.get("category"),
                    "score": scored,
                }
            )

        agg = aggregate_scores([r["score"] for r in results])
        return {
            "preset": preset,
            "customer_id": customer_id,
            "provider": provider.lower().strip(),
            "model_id": model_id,
            "prompt_version": self.settings.prompt_version,
            "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "results": results,
            "aggregate": agg,
            "scored_count": len(results),
        }

    def report_cards(
        self,
        *,
        preset: str,
        customer_id: str,
        provider: str,
        model_id: str,
    ) -> dict[str, Any]:
        scores = self.scores.list_for_selection(
            preset=preset,
            customer_id=customer_id,
            provider=provider,
            model_id=model_id,
            prompt_version=self.settings.prompt_version,
        )
        by_scenario = {s["scenario_id"]: s for s in scores}
        cards = []
        for s in SCENARIOS:
            if customer_id not in s.get("fixture_ids", []):
                continue
            sid = s["scenario_id"]
            cards.append(
                {
                    "scenario_id": sid,
                    "title": s["title"],
                    "category": s.get("category"),
                    "suggested_prompt": s["suggested_prompt"],
                    "score": by_scenario.get(sid),
                }
            )
        agg = aggregate_scores(scores)
        model_all = self.scores.list_for_model(
            provider=provider,
            model_id=model_id,
            prompt_version=self.settings.prompt_version,
        )
        model_agg = aggregate_scores(model_all)
        return {
            "preset": preset,
            "customer_id": customer_id,
            "provider": provider.lower().strip(),
            "model_id": model_id,
            "prompt_version": self.settings.prompt_version,
            "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "judge_available": self.settings.openai_available,
            "cards": cards,
            "aggregate": agg,
            "model_aggregate": model_agg,
            "scored_count": sum(1 for c in cards if c["score"]),
            "total": len(cards),
        }


_service: EvaluationService | None = None


def get_evaluation_service() -> EvaluationService:
    global _service
    if _service is None:
        _service = EvaluationService()
    return _service
