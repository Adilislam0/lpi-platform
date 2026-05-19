from fastapi import APIRouter

from lpi.models import Goal, GoalCreate, GoalUpdate

router = APIRouter()


@router.post("/", response_model=Goal)
def create_goal(goal: GoalCreate) -> Goal:
    """Create a new goal with SMILE phase tracking."""
    raise NotImplementedError("Phase 2 task: Adil implements this")


@router.get("/", response_model=list[Goal])
def list_goals(user_id: str | None = None) -> list[Goal]:
    """List goals, optionally filtered by user."""
    raise NotImplementedError("Phase 2 task: Adil implements this")


@router.get("/{goal_id}", response_model=Goal)
def get_goal(goal_id: str) -> Goal:
    """Get a specific goal."""
    raise NotImplementedError("Phase 2 task: Adil implements this")


@router.patch("/{goal_id}", response_model=Goal)
def update_goal(goal_id: str, update: GoalUpdate) -> Goal:
    """Update a goal (including SMILE phase transitions)."""
    raise NotImplementedError("Phase 2 task: Adil implements this")


@router.delete("/{goal_id}")
def delete_goal(goal_id: str) -> dict:
    """Delete a goal."""
    raise NotImplementedError("Phase 2 task: Adil implements this")
