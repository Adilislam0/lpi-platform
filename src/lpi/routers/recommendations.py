from fastapi import APIRouter

from lpi.models import Recommendation

router = APIRouter()


@router.get("/{user_id}", response_model=list[Recommendation])
def get_recommendations(user_id: str, limit: int = 3) -> list[Recommendation]:
    """Get top recommendations based on goals + signals."""
    raise NotImplementedError("Phase 4 task: Jaivardhan implements this")
