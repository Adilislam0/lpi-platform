# June 1 QA Setup Report — LPI Platform

**QA Lead:** Daksh Garg  
**Date:** 2026-06-01  
**Repository branch:** `staging`  
**Scope:** Environment setup and verification only (no application code changes)

---

## 1. Environment setup steps

| Step | Action | Result |
|------|--------|--------|
| 1 | Clone/pull `Life-Atlas/lpi-platform` (`staging`) | OK |
| 2 | `cd` to repository root | OK |
| 3 | `python -m pip install -e ".[dev]"` | OK — editable install of `lpi-platform` |
| 4 | Start API server | OK — see §4 |
| 5 | Open Swagger UI | OK — http://localhost:8000/docs |
| 6 | Document endpoints | OK — `docs/qa/june1_swagger_review.md` |

---

## 2. Dependencies installed

| Dependency | Version / notes |
|------------|-----------------|
| Python | 3.11.3 |
| `lpi-platform` | 0.1.0 (editable, `[dev]` extras) |
| FastAPI | ≥0.135 (installed via project) |
| Uvicorn | ≥0.30 with `[standard]` |
| pytest, ruff, mypy, pre-commit | via `[dev]` optional deps |

Install command used:

```bash
python -m pip install -e ".[dev]"
```

---

## 3. Server startup verification

### Command used

```bash
uvicorn lpi.main:app --reload --port 8000
```

*(An instance was already listening on port 8000 during this review; no restart required.)*

### Evidence

| Check | URL | Result |
|-------|-----|--------|
| Health | http://localhost:8000/health | `200` — `{"status":"ok","version":"0.1.0"}` |
| OpenAPI | http://localhost:8000/openapi.json | `200` — valid JSON, title `LPI Platform` |
| Import smoke | `pytest tests/test_smoke.py -q` | Passes (no import errors) |

### Startup issues and fixes

| Issue | Fix applied |
|-------|-------------|
| None during this session | Server responded on first health check |
| *(Historical)* `pip install` failed on Python 3.11 when `requires-python` was `>=3.12` | Resolved on `staging` — requirement set to `>=3.11` (prior commit) |
| *(Historical)* Background `uvicorn` exit code 1 after manual stop | Expected when process is killed; not a startup failure |

---

## 4. Swagger accessibility verification

| Item | Value |
|------|--------|
| URL accessed | http://localhost:8000/docs |
| HTTP status | `200` |
| Alternate docs | http://localhost:8000/redoc (available) |
| Schema URL | http://localhost:8000/openapi.json |

Swagger UI loaded successfully. All three API tags (**goals**, **signals**, **recommendations**) and `/health` were visible. Detailed per-endpoint review: **`docs/qa/june1_swagger_review.md`**.

---

## 5. Endpoint inventory summary

**9 application endpoints** registered in OpenAPI (plus `/docs`, `/openapi.json`, `/redoc`):

| Path | Methods |
|------|---------|
| `/health` | GET |
| `/api/v1/goals/` | POST, GET |
| `/api/v1/goals/{goal_id}` | GET, PATCH, DELETE |
| `/api/v1/signals/` | POST, GET |
| `/api/v1/recommendations/{user_id}` | GET |

**OpenAPI-documented success codes:** mostly `200` and `422` (validation).  
**Current runtime (stubs):** unimplemented handlers return `500` until Phase 2/3/4 work lands.

---

## 6. Related QA artifacts

| File | Purpose |
|------|---------|
| `docs/qa/june1_swagger_review.md` | Swagger walkthrough and endpoint table |
| `docs/qa/goal_endpoints_qa_matrix.md` | Phase 2 Goal CRUD test matrix |
| `docs/notes/phase3_signals_prep.md` | Phase 3 signals prep (June 1 session, not Phase 2 gate) |

---

## 7. Blockers

**None** — Swagger UI and API are accessible on localhost.

---

## 8. Next steps

- Execute Goal QA matrix when Phase 2 CRUD is implemented.
- Re-verify Swagger **Observed** column after stubs are replaced.
- Optional: `LPI_RUN_PHASE_GATES=1 pytest tests/ -v` for full gate suite.
