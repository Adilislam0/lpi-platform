"""Pydantic data models for the LPI Platform.

═══════════════════════════════════════════════════════════════
TASK C CHANGE — What was added and WHY
═══════════════════════════════════════════════════════════════

New field:  urgency_flag: bool = False

WHY this field exists:
  The scoring formula has THREE components:
    (priority × 0.5) + (smile_phase_weight × 0.3) + (urgency_flag × 0.2)

  `priority` captures long-term strategic importance.
  `smile_phase_weight` captures where in the SMILE journey the goal is.
  `urgency_flag` captures "this needs attention RIGHT NOW" — a short-term
  override for things like deadlines, meetings, or external blockers.

  Example without urgency_flag:
    Goal A: priority=5, sense, urgent=False → score = 2.80
    Goal B: priority=5, evolve, urgent=False → score = 4.00
    B surfaces first — reasonable, it has more momentum.

  Example with urgency_flag:
    Goal A: priority=5, sense, urgent=True → score = 3.00
    Goal B: priority=5, evolve, urgent=False → score = 4.00
    B still surfaces first, but A moved up — its urgency is acknowledged.

WHY it's in GoalCreate (not Goal):
  GoalCreate is the request body for POST /api/v1/goals/.
  The user sets urgency_flag when creating a goal.
  Goal inherits from GoalCreate, so it automatically carries the field.

WHY it's also in GoalUpdate:
  Users need to be able to toggle urgency on/off on existing goals.
  PATCH /api/v1/goals/{id} with {"urgency_flag": true} activates urgency.
  The `None` default means "if you don't send this field, don't change it."

WHY this is a coordinated change with scoring.py and goals.py:
  1. models.py first — the field must EXIST before anyone can use it.
  2. scoring.py — uses goal.urgency_flag in the formula.
     Without updating scoring.py, urgency_flag would be stored but ignored.
  3. goals.py (list_goals only) — uses sort_goals_by_score so urgency
     affects the order goals are returned in.

  All three files must be committed together in one PR/commit.
  If you commit models.py alone, the score is wrong (urgency ignored).
  If you commit scoring.py without models.py, `goal.urgency_flag` doesn't
  exist yet → AttributeError on every score_goal() call.
═══════════════════════════════════════════════════════════════
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

# ── SMILE phase enum ──────────────────────────────────────────────────────────

class SmilePhase(StrEnum):
    """The five SMILE methodology phases, used throughout the LPI platform.

    StrEnum means the values ARE strings — SmilePhase.SENSE == "sense" is True.
    This makes JSON serialisation automatic: FastAPI converts SmilePhase.SENSE
    to the string "sense" in API responses without any extra configuration.
    """
    SENSE = "sense"
    MODEL = "model"
    INTERVENE = "intervene"
    LEARN = "learn"
    EVOLVE = "evolve"


# ── Goal models ───────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    """Request body schema for POST /api/v1/goals/.

    Fields the API caller provides when creating a goal.
    `user_id` is NOT here — the server assigns "default_user" in Phase 2
    and will read it from the JWT bearer token in Phase 3.

    All fields have sensible defaults so the minimal valid payload
    is just {"title": "My goal"}.
    """

    title: str
    description: str = ""
    priority: int = 5               # 1 = lowest urgency, 10 = highest
    smile_phase: SmilePhase = SmilePhase.SENSE

    # ── TASK C ADDITION ───────────────────────────────────────────────────────
    urgency_flag: bool = False
    # Contributes 0.2 to the composite score when True.
    # Use this when a goal needs immediate attention that its base priority
    # doesn't fully reflect — e.g., a deliverable due tomorrow, or a goal
    # suddenly made urgent by an external event.
    # Defaults to False so existing callers who don't send this field
    # continue to work without any change (backward compatible).
    # ─────────────────────────────────────────────────────────────────────────


class Goal(GoalCreate):
    """Full goal object returned by all goal endpoints.

    Inherits title, description, priority, smile_phase, urgency_flag
    from GoalCreate. Adds server-assigned fields: id, user_id, timestamps.

    Because Goal INHERITS from GoalCreate, adding urgency_flag to GoalCreate
    automatically makes it available on Goal objects too — no duplication.

    The `**goal.model_dump()` spread in create_goal() picks up urgency_flag
    automatically because model_dump() returns ALL fields of GoalCreate,
    including the new urgency_flag field.
    """

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class GoalUpdate(BaseModel):
    """Partial update schema for PATCH /api/v1/goals/{goal_id}.

    Every field is optional (None = "don't change this field").
    Only fields the caller explicitly sends get updated — this is enforced
    by `model_dump(exclude_unset=True)` in the route handler.

    Why `bool | None` instead of just `bool`:
      - `None` = caller didn't send this field → leave it unchanged
      - `True`  = caller sent urgency_flag=true → activate urgency
      - `False` = caller sent urgency_flag=false → deactivate urgency
      If we used `bool = False`, sending {"title": "X"} without urgency_flag
      would RESET urgency_flag to False even though the caller never touched it.
    """

    title: str | None = None
    description: str | None = None
    priority: int | None = None
    smile_phase: SmilePhase | None = None
    urgency_flag: bool | None = None  # TASK C ADDITION


# ── Signal models (unchanged) ─────────────────────────────────────────────────

class SignalCreate(BaseModel):
    stream: str
    event_type: str
    payload: dict = {}


class Signal(SignalCreate):
    id: str
    user_id: str
    timestamp: datetime


# ── Recommendation model (unchanged) ─────────────────────────────────────────

class Recommendation(BaseModel):
    id: str
    user_id: str
    action: str
    reasoning: str
    smile_phase: SmilePhase
    priority: float
    source_goals: list[str] = []
    source_signals: list[str] = []
    created_at: datetime


# ── Delete confirmation (added in Phase 2 CRUD fix, unchanged here) ───────────

class DeleteResponse(BaseModel):
    """Returned by DELETE /api/v1/goals/{goal_id}.

    Field is `id` (not `goal_id`) to match the OpenAPI contract.
    """
    deleted: bool = True
    id: str