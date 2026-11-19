# Personality Playground

Phase 1 Interactive MVP — a professional React + FastAPI studio for exploring five-dimensional conversational personality on a **synthetic banking rewards** chatbot.

- Configure traits (levels 1 / 3 / 5 / 7 / 9) and presets
- Visualize **Requested** radar + fixed 2D map (X=Exploration, Y=Energy)
- Chat live via FastAPI with OpenAI **or** Google (env-configurable)
- Deterministic personality compiler; immutable banking policy dominates style
- Developer inspector: prompts, fixture IDs, model IDs, tool traces, run IDs

Phase 2 Demo lab report cards + independent judges are included — see `docs/EVALUATION_DESIGN_FUTURE.md`.

## Auth + allowlist

Sign-up / login (password + optional Google OAuth). New accounts are **pending** until an admin approves them. Playground APIs (`/api/chat`, fixtures, preview, …) require an **approved** session cookie. Admin allowlist UI manages approve / deny / revoke. Seed admin: `ADMIN_EMAIL`.

## Quickstart

### 1. Environment

```bash
cp .env.example backend/.env
# Add at least one provider key for live chat (optional — scripted demo works without keys)
# For auth: set SESSION_SECRET, ADMIN_EMAIL, DATABASE_URL (Postgres in prod)
```

| Variable | Where | Purpose |
|----------|--------|---------|
| `DATABASE_URL` | backend / Vercel | Postgres (Neon). Local default: SQLite memory |
| `SESSION_SECRET` | backend / Vercel | Signed httpOnly session cookies |
| `ADMIN_EMAIL` | backend / Vercel | Auto-approved admin seed |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | backend / Vercel | Google Sign-In |
| `DATA_ENCRYPTION_KEY` | backend / Vercel | Optional Fernet for emails at rest |
| `RESEND_API_KEY` or `SMTP_*` | backend / Vercel | Notify admin of pending signups |
| `OPENAI_API_KEY` | backend / Vercel | OpenAI adapter |
| `GOOGLE_API_KEY` | backend / Vercel | Google Gemini adapter |
| `OPENAI_MODEL` | backend / Vercel | Default OpenAI model (`gpt-4o-mini`) |
| `JUDGE_MODEL` | backend / Vercel | Independent judge model — allowlisted small OpenAI only (`gpt-4o-mini` / `gpt-4.1-mini`) |
| `GOOGLE_MODEL` | backend / Vercel | Default Google model (`gemini-2.0-flash`) |
| `OPENAI_KEY_EXPIRES_AT` | backend / Vercel | ISO date (`YYYY-MM-DD`) for key-expiry banner (set when rotating a 7-day key) |
| `APP_BASE_URL` | backend / Vercel | Public origin (OAuth redirects) |
| `VITE_API_BASE_URL` | optional frontend | Defaults to same-origin `/api` via Vite proxy |

The frontend **never** holds API keys. If neither LLM key is set, use **Scripted demo mode** in the model switcher (explicitly labeled — never a silent fake live model).
### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

### 4. Tests

```bash
cd backend
source .venv/bin/activate
pytest -q
```

## Demo script (presenter)

1. Load **Explorer** preset → ask: *“What are my best options for redeeming rewards?”* (customer_A).
2. Switch to **Concise** → same question / new session.
3. Inspect **Developer Details** for compiled prompts + identical banking facts from tools.
4. Toggle model switcher between OpenAI, Google, and Scripted demo.
5. Scroll to **Demo lab** (page bottom) → **Run all + score** for a preset; report cards show personality (when `OPENAI_API_KEY` set) + banking checks automatically.

### OpenAI model allowlist

Experimentation only lists small models: `gpt-4o-mini`, `gpt-4.1-mini` (large models like `gpt-4o` / `o1` are rejected). Google + scripted demo are unchanged. Judges use the same allowlist via `JUDGE_MODEL`.

### Demo cache + report cards

Server-side rows in Postgres (`demo_cache` + `eval_scores`), keyed by preset/customer/scenario/provider/model/prompt (+ judge prompt version for scores). Stores reply text + safe metadata + judge/banking results (no API keys).

- `GET /api/demo/cache` — cached replies + attached scores
- `POST /api/demo/run` — fill cache; `auto_judge=true` (default) scores each run
- `GET /api/demo/scores` / `POST /api/demo/judge` — report cards / score cached only
- Measured radar overlay appears only when judges return a complete trait set (never fabricated)

### How to use Demo lab scores

1. Open the live site → scroll to **Demo lab** (or use header **Demo lab / scores**).
2. Pick preset, customer fixture, and model (scripted demo works offline; OpenAI needed for personality judges).
3. Click **Run all + score** (or **Score cached only** if replies already exist).
4. Each scenario shows a report card: trait scores / abstentions + banking checks. Aggregates appear above the list.

## API

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/health` | Status + provider availability + key expiry + allowlist |
| GET | `/api/fixtures` | customer_A / customer_B + scenarios + eval categories |
| GET | `/api/presets` | Named presets |
| GET | `/api/models` | Available adapters (OpenAI allowlisted) |
| POST | `/api/personality/preview` | Compile requested profile (+ trait cards) |
| POST | `/api/chat` | Chat + run metadata / tool traces |
| GET | `/api/evaluation/status` | Phase 2 judge status |
| GET | `/api/demo/cache` | Cached preset scenario demos + scores |
| POST | `/api/demo/run` | Run / refresh scenarios; auto-judge by default |
| GET | `/api/demo/scores` | Report cards for selection |
| POST | `/api/demo/judge` | Score existing cache |

## Repo layout

```
frontend/   React + TypeScript + Vite + Tailwind + Recharts
backend/    FastAPI + personality compiler + mock tools + LLM adapters
docs/       ROADMAP + future evaluation design
```

## License

MIT
