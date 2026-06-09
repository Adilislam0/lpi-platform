"""Pydantic data models for the LPI Platform.

CRITICAL CORRECTION — SMILE Methodology
═══════════════════════════════════════════════════════════════
The previous codebase used a hallucinated 5-phase SMILE acronym:
  SENSE → MODEL → INTERVENE → LEARN → EVOLVE
This does not exist in any LPI data source.

The CORRECT methodology from data/smile-framework.json is:
  S.M.I.L.E. = Sustainable Methodology for Impact Lifecycle Enablement
  Author: Nicolas Waern, WINNIIO / LifeAtlas

6 correct phases (IDs match the JSON `id` field exactly):
  1. reality-emulation
  2. concurrent-engineering
  3. collective-intelligence
  4. contextual-intelligence
  5. continuous-intelligence
  6. perpetual-wisdom

Principle: "Impact first, data last."
  Outcome → Action → Insight → Information → Data
═══════════════════════════════════════════════════════════════
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class SmilePhase(StrEnum):
    """The 6 phases of S.M.I.L.E. (Sustainable Methodology for Impact Lifecycle Enablement).

    Source of truth: data/smile-framework.json in lpi-mcp-server.
    Author: Nicolas Waern, WINNIIO / LifeAtlas.

    StrEnum means the value IS the string:
        SmilePhase.REALITY_EMULATION == "reality-emulation"  →  True

    The enum attribute names use underscores (Python convention).
    The VALUES use hyphens, matching the JSON `id` field exactly.
    FastAPI serialises these to JSON as-is, so the API returns
    "reality-emulation", not "REALITY_EMULATION".

    Default phase for a new goal is REALITY_EMULATION (order 1) —
    every LPI journey begins by establishing the reality canvas.
    """

    REALITY_EMULATION = "reality-emulation"           # Phase 1
    CONCURRENT_ENGINEERING = "concurrent-engineering"  # Phase 2
    COLLECTIVE_INTELLIGENCE = "collective-intelligence"  # Phase 3
    CONTEXTUAL_INTELLIGENCE = "contextual-intelligence"  # Phase 4
    CONTINUOUS_INTELLIGENCE = "continuous-intelligence"  # Phase 5
    PERPETUAL_WISDOM = "perpetual-wisdom"               # Phase 6


# ── Goal models ───────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    """Request body for POST /api/v1/goals/.

    urgency_flag is a Task C addition. It contributes 0.20 to the composite
    score when True, surfacing time-sensitive goals above same-priority peers.
    Default is False for backward compatibility with existing callers.
    """

    title: str
    description: str = ""
    priority: int = 5  # 1 (low) to 10 (high)
    smile_phase: SmilePhase = SmilePhase.REALITY_EMULATION
    urgency_flag: bool = False  # Task C: 0.20 score boost when True


class Goal(GoalCreate):
    """Full goal object — inherits all GoalCreate fields plus server-assigned ones.

    Because Goal inherits from GoalCreate, adding a field to GoalCreate
    (like urgency_flag) automatically makes it available here too.
    The **goal.model_dump() spread in create_goal() picks it up automatically.
    """

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class GoalUpdate(BaseModel):
    """Partial update schema for PATCH /api/v1/goals/{goal_id}.

    Every field is Optional (None = "caller didn't send this, leave unchanged").
    urgency_flag uses bool | None specifically so a PATCH that only changes
    the title doesn't silently reset urgency to False.
    """

    title: str | None = None
    description: str | None = None
    priority: int | None = None
    smile_phase: SmilePhase | None = None
    urgency_flag: bool | None = None  # Task C


class DeleteResponse(BaseModel):
    """Returned by DELETE /api/v1/goals/{goal_id}.
    Field is `id` (not `goal_id`) to match the OpenAPI contract.
    """

    deleted: bool = True
    id: str


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
    """smile_phase now references the correct 6-phase SmilePhase enum above."""

    id: str
    user_id: str
    action: str
    reasoning: str
    smile_phase: SmilePhase
    priority: float
    source_goals: list[str] = []
    source_signals: list[str] = []
    created_at: datetime
