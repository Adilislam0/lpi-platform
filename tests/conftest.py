"""Shared pytest fixtures for the LPI Platform.

The autouse `clear_store` fixture is the most important thing here.
Without it, a goal created in TestCreateGoal leaks into TestReadGoal,
making test_list_goals see unexpected data and fail non-deterministically
depending on test execution order.

`autouse=True` means pytest applies this fixture to EVERY test in the
suite automatically — no test has to explicitly request it.
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
    Both store.clear_all() and clear_transition_logs() are called on
    both sides so a failing test cannot pollute the next one.
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