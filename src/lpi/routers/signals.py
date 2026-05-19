from fastapi import APIRouter

from lpi.models import Signal, SignalCreate

router = APIRouter()


@router.post("/", response_model=Signal)
def ingest_signal(signal: SignalCreate) -> Signal:
    """Ingest an activity signal from any stream."""
    raise NotImplementedError("Phase 3 task: Adil implements this")


@router.get("/", response_model=list[Signal])
def list_signals(
    user_id: str | None = None,
    stream: str | None = None,
    limit: int = 50,
) -> list[Signal]:
    """Query signals by user, stream, or both."""
    raise NotImplementedError("Phase 3 task: Adil implements this")
