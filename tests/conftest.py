"""Shared pytest fixtures for the LPI Platform.

SMILE correction: sample_goal now uses "reality-emulation" (Phase 1 of
the correct 6-phase framework) instead of the hallucinated "sense" value.

The autouse `clear_store` fixture is the most important thing in this file.
Without it, a goal created in TestCreateGoal leaks into TestReadGoal,
making test_list_goals see unexpected data and fail non-deterministically
depending on test execution order. autouse=True applies it to every test
automatically without any explicit request.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from lpi import store
from lpi.main import app
from lpi.utils.logging import clear_transition_logs


@pytest.fixture(autouse=True)
def clear_store() -> Generator[None, None, None]:
    """Wipe all in-memory state before and after every test.

    The `yield` splits setup (before) from teardown (after).
    Both sides are cleared so a failing test cannot pollute the next one.
    """
    store.clear_all()
    clear_transition_logs()
    yield
    store.clear_all()
    clear_transition_logs()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client — shared across all test modules."""
    return TestClient(app)


@pytest.fixture
def sample_goal() -> dict:
    """A minimal valid goal payload.

    SMILE correction: smile_phase changed from "sense" (hallucinated) to
    "reality-emulation" (Phase 1 of the correct SMILE framework).
    This is the default starting phase for any new LPI goal.
    """
    return {
        "title": "Learn Docker",
        "description": "Containerize my applications",
        "priority": 7,
        "smile_phase": "reality-emulation",  # CORRECTED: was "sense"
    }


@pytest.fixture
def sample_signal() -> dict:
    return {
        "stream": "boardy",
        "event_type": "match_created",
        "payload": {"person_a": "Alice", "person_b": "Bob", "score": 0.85},
    }