from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class SmilePhase(StrEnum):
    SENSE = "sense"
    MODEL = "model"
    INTERVENE = "intervene"
    LEARN = "learn"
    EVOLVE = "evolve"


class GoalCreate(BaseModel):
    title: str
    description: str = ""
    priority: int = 5  # 1-10
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


class SignalCreate(BaseModel):
    stream: str
    event_type: str
    payload: dict = {}


class Signal(SignalCreate):
    id: str
    user_id: str
    timestamp: datetime


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


class DeleteResponse(BaseModel):
    deleted: bool
    id: str
