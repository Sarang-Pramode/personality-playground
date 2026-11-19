# Personality Playground

Phase 1 Interactive MVP — a professional React + FastAPI studio for exploring five-dimensional conversational personality on a **synthetic banking rewards** chatbot.

- Configure traits (levels 1 / 3 / 5 / 7 / 9) and presets
- Visualize **Requested** radar + fixed 2D map (X=Exploration, Y=Energy)
- Chat live via FastAPI with OpenAI **or** Google (env-configurable)
- Deterministic personality compiler; immutable banking policy dominates style
- Developer inspector: prompts, fixture IDs, model IDs, tool traces, run IDs

Phase 2 evaluation UI / judges are **not** included — see `docs/ROADMAP.md`.

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
5. Scroll to **Demo lab** (page bottom) → Run all scenarios for a preset; reload to see cache hits.

### OpenAI model allowlist

Experimentation only lists small models: `gpt-4o-mini`, `gpt-4.1-mini` (large models like `gpt-4o` / `o1` are rejected). Google + scripted demo are unchanged.

### Demo cache

Server-side rows in Postgres (`demo_cache`), keyed by `preset|customer|scenario|provider|model|prompt_version`. Stores reply text + safe metadata (no API keys). `GET /api/demo/cache` loads hits; `POST /api/demo/run` fills misses (`force=true` refreshes).

## API

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/health` | Status + provider availability + key expiry + allowlist |
| GET | `/api/fixtures` | customer_A / customer_B + scenarios |
| GET | `/api/presets` | Named presets |
| GET | `/api/models` | Available adapters (OpenAI allowlisted) |
| POST | `/api/personality/preview` | Compile requested profile |
| POST | `/api/chat` | Chat + run metadata / tool traces |
| GET | `/api/demo/cache` | Cached preset scenario demos |
| POST | `/api/demo/run` | Run / refresh starter scenarios into cache |

## Repo layout

```
frontend/   React + TypeScript + Vite + Tailwind + Recharts
backend/    FastAPI + personality compiler + mock tools + LLM adapters
docs/       ROADMAP + future evaluation design
```

## License

MIT
