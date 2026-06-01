"""Goal/Intent Registry — LPI Phase 2 implementation.

Routes owned by Adil Islam. Paired with Daksh (QA lead).
SMILE logging utility designed by Yashika (floater).

Changes vs Adil's first version (code review fixes):
  - BLOCKER-1 FIXED: log_transition now imported from lpi.utils.logging
    (stub created by Jaivardhan — Yashika wires real DB in Phase 3)
  - BLOCKER-2 FIXED: _goals replaced with store._goals + store._goals_lock
    so the autouse clear_store() fixture in conftest.py clears it correctly
  - CONFLICT-1 FIXED: local DeleteResponse removed; imported from lpi.models
    field name changed from goal_id → id to match OpenAPI contract and models.py
  - WARNING-1 FIXED: DeleteResponse now imported from lpi.models (one source of truth)
  - WARNING-2 FIXED: threading.Lock used via store._goals_lock
"""
import uuid
from datetime import datetime, timezone, UTC

from fastapi import APIRouter, HTTPException, status

from lpi import store
from lpi.models import DeleteResponse, Goal, GoalCreate, GoalUpdate, SmilePhase
from lpi.smile import validate_phase_transition
from lpi.utils.logging import log_transition

router = APIRouter()


# ============================================================================
# POST /api/v1/goals/  — Create a new goal
# ============================================================================
@router.post("/", response_model=Goal, status_code=status.HTTP_201_CREATED)
def create_goal(goal: GoalCreate) -> Goal:
    """Create a new goal and register it in the in-memory store.

    Returns HTTP 201 with the full Goal object including:
    - A server-generated UUID as the id
    - A placeholder user_id (auth is Phase 3)
    - UTC-aware created_at and updated_at timestamps
    """
    now = datetime.now(UTC)

    new_goal = Goal(
        id=str(uuid.uuid4()),
        user_id="default_user",
        created_at=now,
        updated_at=now,
        **goal.model_dump(),
    )

    with store._goals_lock:
        store._goals[new_goal.id] = new_goal
    return new_goal


# ============================================================================
# GET /api/v1/goals/  — List all goals (optional filters)
# ============================================================================
@router.get("/", response_model=list[Goal])
def list_goals(
    user_id: str | None = None,
    smile_phase: SmilePhase | None = None,
) -> list[Goal]:
    """Return all goals, optionally filtered.

    Example: GET /api/v1/goals/?user_id=default_user&smile_phase=sense
    """
    with store._goals_lock:
        all_goals = list(store._goals.values())

    if user_id is not None:
        all_goals = [g for g in all_goals if g.user_id == user_id]
    if smile_phase is not None:
        all_goals = [g for g in all_goals if g.smile_phase == smile_phase]

    return all_goals


# ============================================================================
# GET /api/v1/goals/{goal_id}  — Fetch a single goal by ID
# ============================================================================
@router.get("/{goal_id}", response_model=Goal)
def get_goal(goal_id: str) -> Goal:
    """Fetch a specific goal by its UUID. 404 if not found."""
    with store._goals_lock:
        goal = store._goals.get(goal_id)

    if goal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goal {goal_id} not found",
        )
    return goal


# ============================================================================
# PATCH /api/v1/goals/{goal_id}  — Partial update with SMILE validation
# ============================================================================
@router.patch("/{goal_id}", response_model=Goal)
def update_goal(goal_id: str, update: GoalUpdate) -> Goal:
    """Partially update a goal. All fields are optional.

    SMILE transition rules (enforced here, not in Pydantic):
      Forward one step:  SENSE→MODEL→INTERVENE→LEARN→EVOLVE  ✅
      Backward any step: LEARN→SENSE, INTERVENE→MODEL         ✅
      Skip forward:      SENSE→INTERVENE, MODEL→LEARN         ❌ 422
      Same phase:        SENSE→SENSE                          ❌ 422
    """
    with store._goals_lock:
        goal = store._goals.get(goal_id)
        if goal is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal {goal_id} not found",
            )

        # Validate SMILE phase transition if phase is being changed
        if update.smile_phase is not None and update.smile_phase != goal.smile_phase:
            is_valid = validate_phase_transition(
                current=goal.smile_phase,
                target=update.smile_phase,
            )

            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Invalid SMILE transition: {goal.smile_phase} → "
                        f"{update.smile_phase}. "
                        f"Skipping phases is not allowed."
                    ),
                )

            # Log the valid transition (Yashika's design — Phase 3 writes to DB)
            log_transition(
                goal_id=goal_id,
                from_phase=goal.smile_phase,
                to_phase=update.smile_phase,
                user_id=goal.user_id,
            )

        # Apply partial update — exclude_unset=True prevents None from
        # overwriting existing values for fields the caller did not send
        update_data = update.model_dump(exclude_unset=True)
        updated_goal = goal.model_copy(
            update={
                **update_data,
                "updated_at": datetime.now(UTC),
            }
        )

        store._goals[goal_id] = updated_goal

    return updated_goal


# ============================================================================
# DELETE /api/v1/goals/{goal_id}  — Remove a goal
# ============================================================================
@router.delete("/{goal_id}", response_model=DeleteResponse)
def delete_goal(goal_id: str) -> DeleteResponse:
    """Delete a goal by ID. Returns { deleted: true, id: "<id>" }.

    Note: field is `id` (not `goal_id`) — matches OpenAPI contract.
    Raises HTTP 404 if the goal does not exist.
    """
    with store._goals_lock:
        if goal_id not in store._goals:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goal {goal_id} not found",
            )
        store._goals.pop(goal_id)

    return DeleteResponse(deleted=True, id=goal_id)
