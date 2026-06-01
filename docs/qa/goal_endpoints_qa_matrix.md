# Goal Endpoints QA Matrix — Phase 2

**QA Lead:** Daksh Garg  
**Scope:** `POST`, `GET`, `PATCH`, `DELETE` on `/api/v1/goals/`  
**Base URL (local):** `http://127.0.0.1:8000`

Legend: **Current** = behavior today (stubs); **Target** = expected after Phase 2 implementation.

---

## POST `/api/v1/goals/`

| ID | Category | Test case | Request body | Expected status (target) | Expected response (target) | Current status |
|----|----------|-----------|--------------|----------------------------|----------------------------|----------------|
| G-POST-01 | Happy path | Create goal with all fields | Valid `GoalCreate` (title, description, priority, smile_phase) | `200` or `201` | Goal JSON with `id`, `user_id`, `created_at`, `updated_at` | `500` |
| G-POST-02 | Happy path | Create goal with title only | `{"title": "Learn Docker"}` | `200` or `201` | Goal with defaults: `priority=5`, `smile_phase=sense` | `500` |
| G-POST-03 | Validation | Missing required `title` | `{}` or no title | `422` | Validation error detail | `422` or `500` |
| G-POST-04 | Validation | Empty `title` | `{"title": ""}` | `422` or `400` | Error message | `422` or `500` |
| G-POST-05 | Validation | Invalid `smile_phase` | `{"title": "X", "smile_phase": "invalid"}` | `422` | Enum validation error | `422` |
| G-POST-06 | Validation | Priority out of range (if enforced) | `{"title": "X", "priority": 0}` | `422` or `400` | Error message | `422` or `500` |
| G-POST-07 | Validation | Priority out of range high | `{"title": "X", "priority": 11}` | `422` or `400` | Error message | `422` or `500` |
| G-POST-08 | Error | Malformed JSON | Invalid JSON body | `422` | Parse/validation error | `422` |
| G-POST-09 | Error | Wrong content type | `text/plain` body | `422` or `415` | Error message | `422` or `415` |

---

## GET `/api/v1/goals/`

| ID | Category | Test case | Query / setup | Expected status (target) | Expected response (target) | Current status |
|----|----------|-----------|---------------|----------------------------|----------------------------|----------------|
| G-GETL-01 | Happy path | List all goals (empty) | No goals created | `200` | `[]` | `500` |
| G-GETL-02 | Happy path | List all goals (with data) | After 2+ creates | `200` | Array of Goal objects | `500` |
| G-GETL-03 | Happy path | Filter by `user_id` | `?user_id=test-user` | `200` | Only matching user’s goals | `500` |
| G-GETL-04 | Validation | Unknown query param (if strict) | `?foo=bar` | `200` (ignore) or `422` | Per API policy | `500` |
| G-GETL-05 | Error | Invalid method | `POST` to list URL without body | `405` or `422` | Method/body error | `405`/`422` |

---

## GET `/api/v1/goals/{goal_id}`

| ID | Category | Test case | Path / setup | Expected status (target) | Expected response (target) | Current status |
|----|----------|-----------|--------------|----------------------------|----------------------------|----------------|
| G-GET-01 | Happy path | Get existing goal | Valid `goal_id` from create | `200` | Full Goal JSON | `500` |
| G-GET-02 | Error | Goal not found | Random UUID | `404` | `{"detail": "Goal not found"}` (or equivalent) | `500` |
| G-GET-03 | Validation | Invalid ID format (if validated) | `goal_id=not-a-uuid` | `404` or `422` | Error message | `500` |
| G-GET-04 | Error | Empty path segment | `/api/v1/goals/` vs missing id | `404` or `307` | Routing behavior documented | N/A |

---

## PATCH `/api/v1/goals/{goal_id}`

| ID | Category | Test case | Request body | Expected status (target) | Expected response (target) | Current status |
|----|----------|-----------|--------------|----------------------------|----------------------------|----------------|
| G-PATCH-01 | Happy path | Update title | `{"title": "Updated title"}` | `200` | Goal with new title, `updated_at` changed | `500` |
| G-PATCH-02 | Happy path | Update smile_phase (valid forward) | `sense` → `model` | `200` | Goal with `smile_phase: model` | `500` |
| G-PATCH-03 | Happy path | Partial update (priority only) | `{"priority": 9}` | `200` | Other fields unchanged | `500` |
| G-PATCH-04 | Validation | Invalid phase skip | `sense` → `intervene` | `400` or `422` | SMILE transition rejected | `500` |
| G-PATCH-05 | Validation | Same phase no-op | `sense` → `sense` | `400` or `422` | Rejected per SMILE rules | `500` |
| G-PATCH-06 | Validation | Invalid enum value | `{"smile_phase": "bogus"}` | `422` | Validation error | `422` or `500` |
| G-PATCH-07 | Error | Goal not found | Random `goal_id` | `404` | Not found detail | `500` |
| G-PATCH-08 | Error | Empty patch body | `{}` | `200` (no-op) or `422` | Per API policy | `500` |
| G-PATCH-09 | Error | Malformed JSON | Invalid JSON | `422` | Validation error | `422` |

---

## DELETE `/api/v1/goals/{goal_id}`

| ID | Category | Test case | Path / setup | Expected status (target) | Expected response (target) | Current status |
|----|----------|-----------|--------------|----------------------------|----------------------------|----------------|
| G-DEL-01 | Happy path | Delete existing goal | Valid `goal_id` | `200` or `204` | Success payload or empty body | `500` |
| G-DEL-02 | Happy path | Verify deleted | GET same id after delete | `404` | Not found | `500` |
| G-DEL-03 | Error | Delete non-existent goal | Random UUID | `404` | Not found detail | `500` |
| G-DEL-04 | Error | Double delete | Delete same id twice | `404` on second call | Not found | `500` |
| G-DEL-05 | Error | Invalid ID format | `goal_id=bad` | `404` or `422` | Error message | `500` |

---

## Cross-cutting checks (all Goal endpoints)

| ID | Category | Test case | Expected (target) |
|----|----------|-----------|-------------------|
| G-X-01 | Contract | Response matches OpenAPI `Goal` schema | All required fields present |
| G-X-02 | Contract | `Content-Type: application/json` on JSON responses | Header present |
| G-X-03 | Security | No auth header (Phase 1) | Same as authenticated until auth added |
| G-X-04 | Performance | Single request latency (local) | &lt; 500ms smoke threshold |

---

## Sign-off checklist (Phase 2 gate)

- [ ] All happy-path rows pass with target status codes
- [ ] Validation rows return `422`/`400` as specified
- [ ] Not-found rows return `404`
- [ ] SMILE phase transition rules enforced on PATCH
- [ ] `LPI_RUN_PHASE_GATES=1 pytest tests/test_goal_crud.py -v` passes
