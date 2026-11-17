# Phase 1 MVP Acceptance Checklist

Status as of implementation. Update when verified against a running stack.

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Monorepo `frontend/` (React+TS+Vite, Tailwind, Recharts) + `backend/` (FastAPI) | Done |
| 2 | Five trait sliders at discrete levels 1/3/5/7/9 | Done |
| 3 | Presets: balanced (default), concise, explorer, supportive | Done |
| 4 | localStorage save / delete / export profiles | Done |
| 5 | Requested-profile radar only (no Measured overlay) | Done |
| 6 | Fixed 2D map X=Exploration, Y=Conversational Energy | Done |
| 7 | Behavior summary card | Done |
| 8 | Three-column studio + developer inspector | Done |
| 9 | Deterministic personality compiler + banking policy dominates | Done |
| 10 | `POST /api/personality/preview`, `GET /api/health`, `GET /api/fixtures`, `POST /api/chat` | Done |
| 11 | Chat run metadata + tool traces | Done |
| 12 | Fixtures customer_A / customer_B, ≥3 scenarios | Done (4 scenarios) |
| 13 | Allowlisted read-only mock tools only | Done |
| 14 | OpenAI + Google adapters via env; model switcher in header | Done |
| 15 | Frontend never holds API keys | Done |
| 16 | LLM unavailable → visible error or labeled scripted demo | Done |
| 17 | No Phase 2 evaluation UI / judges / uploads / Measured overlays | Done (stubs + docs only) |
| 18 | Tests: compiler, tools, chat | Done (19 pytest) |
| 19 | README quickstart + `.env.example` only (no secrets committed) | Done |
| 20 | Public GitHub repo + PR to `main` | Done — https://github.com/Sarang-Pramode/personality-playground/pull/1 |

## Presenter demo

Explorer vs Concise on the same redemption question → inspect prompts → identical banking facts from tools.
