import os

import pytest
from fastapi.testclient import TestClient

from lpi.main import app


def _phase_gate_enabled() -> bool:
    return os.getenv("LPI_RUN_PHASE_GATES", "").strip().lower() in {"1", "true", "yes", "on"}


@pytest.fixture(scope="session")
def phase_gate_enabled() -> bool:
    return _phase_gate_enabled()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_goal() -> dict:
    return {
        "title": "Learn Docker",
        "description": "Containerize my applications",
        "priority": 7,
        "smile_phase": "sense",
    }


@pytest.fixture
def sample_signal() -> dict:
    return {
        "stream": "boardy",
        "event_type": "match_created",
        "payload": {"person_a": "Alice", "person_b": "Bob", "score": 0.85},
    }
