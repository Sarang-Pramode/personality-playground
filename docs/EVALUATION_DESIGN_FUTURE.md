# Evaluation Design (Phase 2 — implemented)

Independent judges and banking checks ship with the Demo lab. Measured radar overlays appear **only** when a complete real judge score set exists.

## Capabilities

- Reuses the same chat adapter / Demo cache path as live studio runs
- Independent LLM judges (allowlisted small OpenAI via `JUDGE_MODEL`) score traits with cited behaviors; abstain when evidence is weak
- Deterministic banking checks (balance match, tools, eligibility, hallucination / policy) separate from personality scores
- Scenario seed covering multiple of 12 eval categories (frustration, exploration, structure, …)
- Demo lab report cards per preset × model × scenario; aggregates by selection and by model
- Scores persisted in Postgres (`eval_scores`); judge prompts versioned (`independent-judge-v1`)

## API

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/evaluation/status` | Judge availability + versions |
| GET | `/api/demo/cache` | Cached replies + attached scores |
| POST | `/api/demo/run` | Run scenarios; `auto_judge=true` by default |
| GET | `/api/demo/scores` | Report cards for selection |
| POST | `/api/demo/judge` | Score existing cache without re-running chat |

## Env

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Required for personality judges (banking checks work without it) |
| `JUDGE_MODEL` | Allowlisted small OpenAI id (`gpt-4o-mini` default, or `gpt-4.1-mini`) |
| `OPENAI_MODEL` | Fallback when `JUDGE_MODEL` unset / invalid |

Never fabricate Measured scores when the judge is unavailable — banking checks still run and show on report cards.
