# Personality Playground

Phase 1 Interactive MVP — a professional React + FastAPI studio for exploring five-dimensional conversational personality on a **synthetic banking rewards** chatbot.

- Configure traits (levels 1 / 3 / 5 / 7 / 9) and presets
- Visualize **Requested** radar + fixed 2D map (X=Exploration, Y=Energy)
- Chat live via FastAPI with OpenAI **or** Google (env-configurable)
- Deterministic personality compiler; immutable banking policy dominates style
- Developer inspector: prompts, fixture IDs, model IDs, tool traces, run IDs

Phase 2 evaluation UI / judges are **not** included — see `docs/ROADMAP.md`.

## Quickstart

### 1. Environment

```bash
cp .env.example backend/.env
# Add at least one provider key for live chat (optional — scripted demo works without keys)
```

| Variable | Where | Purpose |
|----------|--------|---------|
| `OPENAI_API_KEY` | `backend/.env` | OpenAI adapter |
| `GOOGLE_API_KEY` | `backend/.env` | Google Gemini adapter |
| `OPENAI_MODEL` | `backend/.env` | Default OpenAI model (`gpt-4o-mini`) |
| `GOOGLE_MODEL` | `backend/.env` | Default Google model (`gemini-2.0-flash`) |
| `VITE_API_BASE_URL` | optional frontend | Defaults to same-origin `/api` via Vite proxy |

The frontend **never** holds API keys. If neither key is set, use **Scripted demo mode** in the model switcher (explicitly labeled — never a silent fake live model).

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

## API

| Method | Path | Notes |
|--------|------|-------|
| GET | `/api/health` | Status + provider availability |
| GET | `/api/fixtures` | customer_A / customer_B + scenarios |
| GET | `/api/presets` | Named presets |
| GET | `/api/models` | Available adapters |
| POST | `/api/personality/preview` | Compile requested profile |
| POST | `/api/chat` | Chat + run metadata / tool traces |

## Repo layout

```
frontend/   React + TypeScript + Vite + Tailwind + Recharts
backend/    FastAPI + personality compiler + mock tools + LLM adapters
docs/       ROADMAP + future evaluation design
```

## License

MIT
