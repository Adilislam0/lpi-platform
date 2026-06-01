from fastapi import APIRouter

from lpi.models import Signal, SignalCreate

# Phase 3 prep only – not part of Phase 2 gate requirements.
# In-memory scaffold for future signal storage; not used by route handlers yet.
_signals: dict[str, Signal] = {}


def create_signal_stub() -> None:
    """
    Phase 3 preparation only.
    Actual implementation deferred.
    """
    pass


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
