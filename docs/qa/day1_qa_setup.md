# Day 1 QA Setup — LPI Platform

**QA Lead:** Daksh Garg  
**Date:** 2026-06-01  
**Environment:** Local (`uvicorn lpi.main:app --reload --port 8000`)  
**Swagger UI:** http://127.0.0.1:8000/docs  
**OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

## Prerequisites verified

- [x] `python -m pip install -e ".[dev]"`
- [x] Application starts without import errors
- [x] `GET /health` returns `200`
- [x] Swagger UI loads at `/docs`

## Available endpoints

| Endpoint | Method | Tag | Summary | Current response (stub) | Expected when implemented |
|----------|--------|-----|---------|---------------------------|---------------------------|
| `/health` | GET | — | Health check | `200` — `{"status":"ok","version":"0.1.0"}` | `200` |
| `/docs` | GET | — | Swagger UI | `200` (HTML) | `200` |
| `/openapi.json` | GET | — | OpenAPI schema | `200` (JSON) | `200` |
| `/api/v1/goals/` | POST | goals | Create goal | `500` (NotImplementedError) | `200` or `201` + Goal body |
| `/api/v1/goals/` | GET | goals | List goals | `500` (NotImplementedError) | `200` + `Goal[]` |
| `/api/v1/goals/{goal_id}` | GET | goals | Get goal by ID | `500` (NotImplementedError) | `200` + Goal; `404` if missing |
| `/api/v1/goals/{goal_id}` | PATCH | goals | Update goal | `500` (NotImplementedError) | `200` + Goal; `404` if missing |
| `/api/v1/goals/{goal_id}` | DELETE | goals | Delete goal | `500` (NotImplementedError) | `200`/`204`; `404` if missing |
| `/api/v1/signals/` | POST | signals | Ingest signal | `500` (NotImplementedError) | `200` or `201` + Signal body |
| `/api/v1/signals/` | GET | signals | List/query signals | `500` (NotImplementedError) | `200` + `Signal[]` |
| `/api/v1/recommendations/{user_id}` | GET | recommendations | Get recommendations | `500` (NotImplementedError) | `200` + `Recommendation[]` |

## Request models (from OpenAPI)

### GoalCreate (POST `/api/v1/goals/`)

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `title` | string | yes | — | Non-empty expected in QA |
| `description` | string | no | `""` | |
| `priority` | integer | no | `5` | Range 1–10 per product intent |
| `smile_phase` | enum | no | `sense` | `sense`, `model`, `intervene`, `learn`, `evolve` |

### GoalUpdate (PATCH `/api/v1/goals/{goal_id}`)

All fields optional: `title`, `description`, `priority`, `smile_phase`.

### SignalCreate (POST `/api/v1/signals/`)

| Field | Type | Required | Default |
|-------|------|----------|---------|
| `stream` | string | yes | — |
| `event_type` | string | yes | — |
| `payload` | object | no | `{}` |

### Query parameters

| Endpoint | Parameter | Type | Default | Purpose |
|----------|-----------|------|---------|---------|
| `GET /api/v1/goals/` | `user_id` | string | optional | Filter by user |
| `GET /api/v1/signals/` | `user_id` | string | optional | Filter by user |
| `GET /api/v1/signals/` | `stream` | string | optional | Filter by stream |
| `GET /api/v1/signals/` | `limit` | integer | `50` | Max results |
| `GET /api/v1/recommendations/{user_id}` | `limit` | integer | `3` | Max recommendations |

## Testing notes

1. **Phase 2 focus:** Goal CRUD endpoints are the primary QA scope for this sprint. Use `docs/qa/goal_endpoints_qa_matrix.md` for detailed cases.
2. **Stub behavior:** Unimplemented handlers raise `NotImplementedError` and currently surface as `500`. Re-test after Adil’s Phase 2 implementation; status codes should move to documented expectations.
3. **Phase gate tests:** Run full gate suite with `LPI_RUN_PHASE_GATES=1 pytest tests/ -v` when endpoints are ready.
4. **Smoke tests:** Default `pytest` runs Phase 1 smoke + SMILE tests only (gate tests skipped unless env flag is set).
5. **Swagger workflow:** Use “Try it out” on each tag; compare response schema to `lpi.models` Pydantic models.
6. **SMILE validation:** Invalid phase skips (e.g. `sense` → `intervene`) should be rejected once update logic is wired (see `lpi.smile.validate_phase_transition`).

## Local run commands

```bash
pip install -e ".[dev]"
uvicorn lpi.main:app --reload --port 8000
pytest tests/ -v
```
