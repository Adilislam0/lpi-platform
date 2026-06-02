# Goals QA Matrix — Daksh (Phase 2 QA + Phase 3 Prep)

**Date:** 2026-06-02  
**Base URL:** `http://localhost:8000`  
**Scope:** only requested work items A, B, C (+ Done When)

---

## A) POST `/api/v1/goals/` QA matrix (6 required cases)

| ID | Scenario | Sample request body | Expected status | Expected response notes |
|---|---|---|---|---|
| A-POST-01 | Full payload | `{"title":"Learn Docker","description":"Containerize apps","priority":7,"smile_phase":"sense"}` | `201` (or `200` per current implementation) | Goal object returned with generated `id`, timestamps |
| A-POST-02 | Minimal payload (title only) | `{"title":"Learn Docker"}` | `201` (or `200`) | Defaults applied (`priority=5`, `smile_phase=sense`, `description=""`) |
| A-POST-03 | Missing title | `{}` | `422` | Pydantic validation error (`title` required) |
| A-POST-04 | Invalid priority low | `{"title":"X","priority":0}` | `422` | Priority validation failure |
| A-POST-05 | Invalid priority high | `{"title":"X","priority":11}` | `422` | Priority validation failure |
| A-POST-06 | Unknown smile phase | `{"title":"X","smile_phase":"unknown"}` | `422` | Enum validation failure |

---

## B) GET `/api/v1/goals/` QA matrix

| ID | Scenario | Setup | Request | Expected status | Expected result |
|---|---|---|---|---|---|
| B-GET-01 | Empty list | Fresh store | `GET /api/v1/goals/` | `200` | `[]` |
| B-GET-02 | After 1 POST | Create 1 goal | `GET /api/v1/goals/` | `200` | Array length = 1 |
| B-GET-03 | After 3 POSTs | Create 3 goals with priorities 9, 5, 2 | `GET /api/v1/goals/` | `200` | Verify list sorted by `priority` DESC (`9,5,2`) |
| B-GET-04 | Smile phase filter | Mixed phases created | `GET /api/v1/goals/?smile_phase=sense` | `200` | Only goals with `smile_phase="sense"` returned |

**Priority sort verification note:** if API does not yet sort by priority DESC, mark as fail and raise as Phase 2 behavior gap.

---

## C) Priority scoring reproducibility verification

Run this after Jaivardhan lands scoring logic.

| ID | Scenario | Steps | Expected |
|---|---|---|---|
| C-SCORE-01 | Reproducible scoring | POST same goal payload twice (same input fields) | Computed score is identical both times |

### QA note template (fill once scoring is merged)

- **Scoring formula (from implementation):** `TBD — copy exact formula from code`
- **Inputs tested:** `TBD`
- **Run 1 score:** `TBD`
- **Run 2 score:** `TBD`
- **Result:** Pass if equal; Fail if mismatch

---

## Done When

- [ ] POST QA matrix complete (6 test cases documented)
- [ ] GET QA complete with priority sort verified
- [ ] Priority scoring reproducibility confirmed
