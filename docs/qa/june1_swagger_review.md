# June 1 Swagger Review — LPI Platform

**QA Lead:** Daksh Garg  
**Date:** 2026-06-01  
**Swagger UI:** http://localhost:8000/docs  
**OpenAPI schema:** http://localhost:8000/openapi.json  
**API title (OpenAPI):** LPI Platform v0.1.0

## Review method

1. Started local server (see `docs/qa/june1_qa_setup.md` for startup evidence).
2. Opened Swagger UI in browser at `http://localhost:8000/docs`.
3. Compared UI tags/operations with `GET /openapi.json`.
4. Spot-checked **Try it out** on `/health` and stub routes to record runtime behavior.

## Endpoint inventory

| # | Path | Method | Tag | Description | Expected status codes (OpenAPI) | Observed at review (runtime) |
|---|------|--------|-----|-------------|--------------------------------|------------------------------|
| 1 | `/health` | GET | — | Health check for API availability | `200` | `200` |
| 2 | `/api/v1/goals/` | POST | goals | Create a new goal with SMILE phase tracking | `200`, `422` | `500` (stub: NotImplementedError) |
| 3 | `/api/v1/goals/` | GET | goals | List goals, optionally filtered by user | `200`, `422` | `500` (stub) |
| 4 | `/api/v1/goals/{goal_id}` | GET | goals | Get a specific goal | `200`, `422` | `500` (stub) |
| 5 | `/api/v1/goals/{goal_id}` | PATCH | goals | Update a goal (including SMILE phase transitions) | `200`, `422` | `500` (stub) |
| 6 | `/api/v1/goals/{goal_id}` | DELETE | goals | Delete a goal | `200`, `422` | `500` (stub) |
| 7 | `/api/v1/signals/` | POST | signals | Ingest an activity signal from any stream | `200`, `422` | `500` (stub) |
| 8 | `/api/v1/signals/` | GET | signals | Query signals by user, stream, or both | `200`, `422` | `500` (stub) |
| 9 | `/api/v1/recommendations/{user_id}` | GET | recommendations | Get top recommendations based on goals + signals | `200`, `422` | `500` (stub) |

### Supporting routes (not in application tags)

| Path | Method | Purpose | Expected status |
|------|--------|---------|-----------------|
| `/docs` | GET | Swagger UI (interactive documentation) | `200` |
| `/openapi.json` | GET | Machine-readable OpenAPI schema | `200` |
| `/redoc` | GET | ReDoc alternative docs (FastAPI default) | `200` |

## Swagger UI structure

| Tag | Operations |
|-----|------------|
| **goals** | POST, GET `/api/v1/goals/`; GET, PATCH, DELETE `/api/v1/goals/{goal_id}` |
| **signals** | POST, GET `/api/v1/signals/` |
| **recommendations** | GET `/api/v1/recommendations/{user_id}` |
| *(default)* | GET `/health` |

## Path parameters and query strings (from OpenAPI)

| Endpoint | Parameters |
|----------|------------|
| `GET /api/v1/goals/` | `user_id` (optional query) |
| `GET /api/v1/signals/` | `user_id`, `stream` (optional query); `limit` (default `50`) |
| `GET /api/v1/recommendations/{user_id}` | `user_id` (path); `limit` (query, default `3`) |
| `GET/PATCH/DELETE /api/v1/goals/{goal_id}` | `goal_id` (path) |

## QA notes from Swagger inspection

- **Schemas:** Request/response models (`Goal`, `GoalCreate`, `GoalUpdate`, `Signal`, `SignalCreate`, `Recommendation`) are visible under **Schemas** in Swagger.
- **Validation:** Invalid bodies (e.g. missing `title` on POST goal) should return `422` per spec; stub handlers may return `500` before validation runs on unimplemented paths.
- **Phase 2 QA focus:** Five Goal operations — detailed cases in `docs/qa/goal_endpoints_qa_matrix.md`.
- **Re-test:** After Phase 2/3 implementation, re-run Swagger **Try it out** and update the “Observed” column.

## Blockers

None for Swagger access. UI and OpenAPI JSON both reachable on localhost.
