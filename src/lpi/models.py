"""Pydantic data models for the LPI Platform.

Phase 2 change vs Phase 1: added DeleteResponse at the bottom.
Everything else is identical to the original file so existing tests
(test_smile.py, test_smoke.py) continue to pass without modification.

Phase 2 (Task C — tomorrow): Jaivardhan will add urgency_flag: bool
to GoalCreate and Goal, and add Field() constraints matching the OpenAPI
contract. That is a separate commit, not part of this fix.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

# ── SMILE phase enum ──────────────────────────────────────────────────────────

class SmilePhase(StrEnum):
    SENSE = "sense"
    MODEL = "model"
    INTERVENE = "intervene"
    LEARN = "learn"
    EVOLVE = "evolve"


# ── Goal models ───────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    title: str
    description: str = ""
    priority: int = 5  # 1–10
    smile_phase: SmilePhase = SmilePhase.SENSE


class Goal(GoalCreate):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: int | None = None
    smile_phase: SmilePhase | None = None


# ── Signal models ─────────────────────────────────────────────────────────────

class SignalCreate(BaseModel):
    stream: str
    event_type: str
    payload: dict = {}


class Signal(SignalCreate):
    id: str
    user_id: str
    timestamp: datetime


# ── Recommendation model ──────────────────────────────────────────────────────

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


# ── Delete confirmation ───────────────────────────────────────────────────────

class DeleteResponse(BaseModel):
    """Returned by DELETE /api/v1/goals/{goal_id}.

    Field is `id` (not `goal_id`) to match the OpenAPI contract.
    """

    deleted: bool = True
    id: str