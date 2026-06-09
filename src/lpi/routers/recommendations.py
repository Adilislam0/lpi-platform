"""Module 3 — Recommendation Engine.

Owner : Jaivardhan Singh  (Phase 4)
QA    : Ankit Kumar Singh

Phase 1/2 gate: returns empty list [] to prove the route is wired and
the server starts without error. The NotImplementedError that was here
caused HTTP 500 on every call and broke test_recommendations.py.

Phase 4: Jaivardhan replaces the body with LangGraph agent reasoning.
"""

from fastapi import APIRouter, Query

from lpi.models import Recommendation

router = APIRouter()


@router.get("/{user_id}", response_model=list[Recommendation])
def get_recommendations(
    user_id: str,
    limit: int = Query(default=3, ge=1, le=10),
) -> list[Recommendation]:
    """Return personalised next-action recommendations.

    Phase 1/2: always returns [] — placeholder, route confirmed wired.
    Phase 4: Jaivardhan implements SMILE-grounded LangGraph reasoning here.
    """
    return []
