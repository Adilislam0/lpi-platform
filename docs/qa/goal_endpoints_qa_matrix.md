# Goal Endpoints — QA Checklist & Matrix (Draft)

**QA Lead:** Daksh Garg | **Phase:** 2 (Goal CRUD)  
**Base URL:** `http://localhost:8000` | **Swagger:** `/docs`  
**Status:** Draft — execute after Phase 2 implementation (stubs currently return `500`)

---

## Endpoint checklist (sign-off)

| # | Endpoint | Method | Happy path | Error paths | Pass |
|---|----------|--------|------------|-------------|------|
| 1 | `/api/v1/goals/` | POST | G-POST-H* | G-POST-E* | [ ] |
| 2 | `/api/v1/goals/` | GET | G-GETL-H* | G-GETL-E* | [ ] |
| 3 | `/api/v1/goals/{goal_id}` | GET | G-GET-H* | G-GET-E* | [ ] |
| 4 | `/api/v1/goals/{goal_id}` | PATCH | G-PATCH-H* | G-PATCH-E* | [ ] |
| 5 | `/api/v1/goals/{goal_id}` | DELETE | G-DEL-H* | G-DEL-E* | [ ] |

**Gate:** `LPI_RUN_PHASE_GATES=1 pytest tests/test_goal_crud.py -v`

---

## 1. POST `/api/v1/goals/` — Create goal

### Happy path

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-POST-H01 | Create with all fields | `{"title":"Learn Docker","description":"Containers","priority":7,"smile_phase":"sense"}` | `200` or `201` | `Goal` with `id`, `user_id`, `created_at`, `updated_at` |
| G-POST-H02 | Create with title only | `{"title":"Learn Docker"}` | `200` or `201` | `priority=5`, `smile_phase=sense`, `description=""` |
| G-POST-H03 | Create each SMILE phase | `smile_phase` = `sense` … `evolve` | `200` or `201` | Phase echoed in response |
| G-POST-H04 | Minimum priority | `{"title":"X","priority":1}` | `200` or `201` | `priority: 1` |
| G-POST-H05 | Maximum priority | `{"title":"X","priority":10}` | `200` or `201` | `priority: 10` |

### Error paths

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-POST-E01 | Missing `title` | `{}` | `422` | Validation error (`title` required) |
| G-POST-E02 | Empty `title` | `{"title":""}` | `422` or `400` | Validation / business rule error |
| G-POST-E03 | Invalid `smile_phase` | `{"title":"X","smile_phase":"invalid"}` | `422` | Enum validation error |
| G-POST-E04 | Priority below range | `{"title":"X","priority":0}` | `422` or `400` | Out-of-range error (if enforced) |
| G-POST-E05 | Priority above range | `{"title":"X","priority":11}` | `422` or `400` | Out-of-range error (if enforced) |
| G-POST-E06 | Wrong type for `priority` | `{"title":"X","priority":"high"}` | `422` | Type validation error |
| G-POST-E07 | Malformed JSON | `{invalid json` | `422` | Parse error |
| G-POST-E08 | Wrong `Content-Type` | `text/plain` body | `415` or `422` | Unsupported media / validation |

---

## 2. GET `/api/v1/goals/` — List goals

### Happy path

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-GETL-H01 | Empty list | `GET /api/v1/goals/` (no data) | `200` | `[]` |
| G-GETL-H02 | Multiple goals | After 2+ POST creates | `200` | Array of `Goal` objects |
| G-GETL-H03 | Filter by `user_id` | `GET /api/v1/goals/?user_id=alice` | `200` | Only Alice’s goals |
| G-GETL-H04 | Filter returns empty | `?user_id=unknown` | `200` | `[]` |

### Error paths

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-GETL-E01 | Wrong HTTP method | `POST` without body to list URL | `405` or `422` | Method not allowed / validation |
| G-GETL-E02 | Invalid query type (if strict) | `?limit=not-int` (if param added later) | `422` | Validation error |

---

## 3. GET `/api/v1/goals/{goal_id}` — Get goal by ID

### Happy path

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-GET-H01 | Get existing goal | `GET /api/v1/goals/{id}` (id from POST) | `200` | Full `Goal` JSON |
| G-GET-H02 | Fields match create | Compare POST body vs GET | `200` | Same `title`, `smile_phase`, etc. |

### Error paths

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-GET-E01 | Goal not found | `GET /api/v1/goals/00000000-0000-0000-0000-000000000099` | `404` | `{"detail":"Goal not found"}` (or equivalent) |
| G-GET-E02 | Invalid ID format | `GET /api/v1/goals/not-a-valid-id` | `404` or `422` | Not found / validation |
| G-GET-E03 | Deleted goal | GET after DELETE | `404` | Not found |

---

## 4. PATCH `/api/v1/goals/{goal_id}` — Update goal

### Happy path

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-PATCH-H01 | Update title | `{"title":"New title"}` | `200` | Updated title; `updated_at` newer |
| G-PATCH-H02 | Update description | `{"description":"Updated"}` | `200` | Description changed |
| G-PATCH-H03 | Update priority | `{"priority":9}` | `200` | Priority changed |
| G-PATCH-H04 | Forward SMILE step | `sense` → `model` | `200` | `smile_phase: model` |
| G-PATCH-H05 | Backward SMILE step | `learn` → `sense` | `200` | Allowed re-evaluation |
| G-PATCH-H06 | Partial update | Only one field in body | `200` | Other fields unchanged |

### Error paths

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-PATCH-E01 | Goal not found | PATCH random UUID | `404` | Not found |
| G-PATCH-E02 | SMILE skip (sense → intervene) | `{"smile_phase":"intervene"}` on sense goal | `400` or `422` | Transition rejected |
| G-PATCH-E03 | SMILE same phase | `sense` → `sense` | `400` or `422` | No-op rejected |
| G-PATCH-E04 | Invalid enum | `{"smile_phase":"bogus"}` | `422` | Validation error |
| G-PATCH-E05 | Invalid priority | `{"priority":99}` | `422` or `400` | Range error |
| G-PATCH-E06 | Malformed JSON | Invalid body | `422` | Parse error |
| G-PATCH-E07 | Empty body policy | `{}` | `200` (no-op) or `422` | Document team choice |

---

## 5. DELETE `/api/v1/goals/{goal_id}` — Delete goal

### Happy path

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-DEL-H01 | Delete existing | `DELETE /api/v1/goals/{id}` | `200` or `204` | Success (`{"ok":true}` or empty) |
| G-DEL-H02 | Not in list after delete | `GET /api/v1/goals/` after delete | `200` | Deleted id absent |
| G-DEL-H03 | Not retrievable after delete | `GET /api/v1/goals/{id}` after delete | `404` | Not found |

### Error paths

| ID | Test case | Request | Expected status | Expected response |
|----|-----------|---------|-----------------|-------------------|
| G-DEL-E01 | Delete non-existent | DELETE random UUID | `404` | Not found |
| G-DEL-E02 | Double delete | DELETE same id twice | `404` on 2nd call | Not found |
| G-DEL-E03 | Invalid ID format | `DELETE .../bad-id` | `404` or `422` | Error per API policy |
| G-DEL-E04 | Wrong method | `GET` on delete-only semantics | N/A | Use DELETE only |

---

## Cross-endpoint flows (integration)

| ID | Flow | Steps | Expected |
|----|------|-------|----------|
| G-FLOW-01 | CRUD lifecycle | POST → GET by id → PATCH → GET → DELETE → GET | All status codes as above |
| G-FLOW-02 | List consistency | POST ×3 → GET list | `200`, length ≥ 3 |
| G-FLOW-03 | SMILE regression | PATCH illegal transition after legal create | `400`/`422`, goal unchanged |

---

## Execution log (fill during QA run)

| Date | Tester | Build/branch | Pass | Fail | Skip | Notes |
|------|--------|--------------|------|------|------|-------|
| | Daksh Garg | `staging` | | | | Stubs: use after Phase 2 merge |

---

## Reference — `Goal` response shape

```json
{
  "id": "string",
  "user_id": "string",
  "title": "string",
  "description": "string",
  "priority": 5,
  "smile_phase": "sense",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

**SMILE rules (PATCH):** forward +1 OK; backward OK; skip (e.g. sense→intervene) NOT OK; same phase NOT OK (`lpi.smile.validate_phase_transition`).
