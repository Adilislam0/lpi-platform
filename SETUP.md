# Local Dev Setup Guide

**Goal:** Every team member can run `make test` and `make run` on their machine.
This is the Phase 1 gate — once you've done it, say so in standup.

---

## Prerequisites

| Tool | Min version | Check |
|------|-------------|-------|
| Python | 3.12+ | `python --version` |
| pip | any recent | `pip --version` |
| Git | any | `git --version` |

You do **not** need Docker or the Supabase CLI to run tests or the server locally — the app starts fine without a live Supabase connection (the config defaults to empty strings).

---

## Step 1 — Clone the repo

```bash
git clone https://github.com/Life-Atlas/lpi-platform.git
cd lpi-platform
```

If you already cloned it, just pull latest:

```bash
git checkout main
git pull
```

---

## Step 2 — Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

- **Windows (cmd):** `.venv\Scripts\activate`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Mac/Linux:** `source .venv/bin/activate`

You should see `(.venv)` in your terminal prompt. Keep this active for every step below.

---

## Step 3 — Install dependencies

```bash
pip install -e ".[dev]"
```

This installs FastAPI, uvicorn, supabase client, pytest, ruff, mypy, and pre-commit — everything in `pyproject.toml`.

---

## Step 4 — Set up your `.env` file

```bash
cp .env.example .env
```

For running tests and the server locally, you can leave the Supabase values empty — the app will start and tests will pass without a live DB connection. You only need real values when working on endpoints that actually query Supabase.

Your `.env` will look like:

```
SUPABASE_URL=
SUPABASE_KEY=
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=
DAILY_COST_CAP_USD=10.0
```

> **Never commit your `.env` file.** It is already in `.gitignore`.

---

## Step 5 — Run the tests

```bash
make test
```

Or directly:

```bash
pytest tests/ -v --tb=short
```

All tests should pass. If any fail, check the error and ask in the team chat before assuming your setup is broken.

---

## Step 6 — Run the API server

```bash
make run
```

Or directly:

```bash
uvicorn lpi.main:app --reload --port 8000
```

Then open your browser:

- **Health check:** http://localhost:8000/health — should return `{"status": "ok", "version": "0.1.0"}`
- **Interactive API docs:** http://localhost:8000/docs — Swagger UI with all endpoints

Once you see the health check return `ok`, you are done. Tell Jaivardhan in standup.

---

## Connecting to a real Supabase instance (optional for Phase 1)

You only need this when working on endpoints that actually read/write data. For Phase 1, skip this unless you are Jaivardhan or Aditi working on the OpenAPI spec.

**Option A — Use the shared dev project (ask Jaivardhan for credentials)**

Fill in `.env`:
```
SUPABASE_URL=https://<project-id>.supabase.co
SUPABASE_KEY=<anon-key>
```

**Option B — Run Supabase locally with Docker**

Requires Docker Desktop installed and running.

```bash
# Install Supabase CLI
npm install -g supabase

# Start local Supabase (first run downloads ~1 GB of images)
supabase start
```

This prints a local `API URL` and `anon key` — paste those into your `.env`. Stop it later with `supabase stop`.

---

## Common problems

**`ModuleNotFoundError: No module named 'lpi'`**
You forgot the `-e` flag or your venv is not active. Run `pip install -e ".[dev]"` with the venv active.

**`python --version` shows 3.10 or 3.11`**
The project requires Python 3.12+. Install it from https://www.python.org/downloads/ and recreate the venv.

**`make: command not found` (Windows)**
Run the commands directly:
- `pip install -e ".[dev]"` instead of `make install`
- `pytest tests/ -v --tb=short` instead of `make test`
- `uvicorn lpi.main:app --reload --port 8000` instead of `make run`

**PowerShell says "running scripts is disabled"**
Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Port 8000 already in use**
Use a different port: `uvicorn lpi.main:app --reload --port 8001`

---

## Checklist — confirm in standup once done

- [ ] Cloned (or pulled latest) the repo
- [ ] Virtual environment created and activated
- [ ] `pip install -e ".[dev]"` ran without errors
- [ ] `.env` file created from `.env.example`
- [ ] `make test` — all tests pass
- [ ] `make run` — server starts, `/health` returns `ok`
