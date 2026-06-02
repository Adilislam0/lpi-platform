"""SMILE phase transition logger — Phase 2 stub.

Design spec : Yashika Verma
Stub written : Jaivardhan Singh (unblocks Adil's goals.py import)

Phase 2: writes to an in-memory list so tests can inspect transitions.
Phase 3: Yashika replaces the body with a Supabase INSERT into
         goal_phase_transitions (see 003_transitions.sql).
"""

from datetime import datetime, timezone

from lpi.models import SmilePhase

# Inspectable in tests — check that transitions are logged correctly
phase_transition_logs: list[dict] = []


def log_transition(
    goal_id: str,
    from_phase: SmilePhase,
    to_phase: SmilePhase,
    user_id: str,
) -> None:
    """Record a valid SMILE phase transition.

    Phase 2: appends a dict to phase_transition_logs.
    Phase 3: Yashika replaces this body with a Supabase insert — no
             other file needs to change when that swap happens.
    """
    phase_transition_logs.append({
        "goal_id": goal_id,
        "from_phase": str(from_phase),
        "to_phase": str(to_phase),
        "transitioned_at": datetime.now(timezone.utc).isoformat(), # noqa: UP017
        "user_id": user_id,
    })


def clear_transition_logs() -> None:
    """Wipe the log. Called by the test autouse fixture."""
    phase_transition_logs.clear()