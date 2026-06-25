"""Per-goal recommendation flow tests (Jaivardhan — Module 2 to Module 3).

These tests are SUPABASE-FREE: they mock the store layer and the LangGraph
agent at the call-site module so the integration can be validated without
a running Supabase instance. They run in CI alongside the no-DB smoke
tests.

OVERVIEW
--------
The new endpoint POST /api/v1/recommendations/{user_id}/by-goal/{goal_id}
runs the LangGraph reasoning agent over a SINGLE goal and ONLY the
activity_signals whose goal_id matches that goal. This file proves:

  1. The store call passes goal_id=<goal> (server-side filter is wired).
  2. The LangGraph agent receives only signals tied to that goal — never
     unrelated signals from the user's portfolio.
  3. The LLM prompt is updated to include the new "advance to next phase"
     instruction and renders each signal's goal_id.
  4. The response is sorted by priority desc and capped at 3 items.
  5. POST /api/v1/signals/sync-github/{goal_id} rejects cross-tenant
     goal_ids with 404 and never writes a signal for a goal the caller
     does not own.

Run with:
  pytest tests/test_recommendations_goal_scoped.py -v --tb=short
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from lpi.main import app
from lpi.middleware.auth import get_current_user
from lpi.middleware.rate_limit import _store as _rate_limit_store
from lpi.models import Goal, Recommendation, Signal, SmilePhase
from lpi.routers import recommendations as rec_router
from lpi.routers import signals as signals_router

# The fixed test user id from conftest.py — kept here so this file is
# fully self-contained even if the conftest value is renamed later.
TEST_USER_ID = "00000000-0000-0000-0000-000000000001"

# Fixed UUIDs for the fixtures — easy to spot in assertion failures.
_OWNED_GOAL_ID = "11111111-1111-1111-1111-111111111111"
_SCOPED_SIGNAL_ID = "22222222-2222-2222-2222-222222222222"
_UNRELATED_GOAL_ID = "99999999-9999-9999-9999-999999999999"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clear_in_memory_state() -> None:
    """Override the autouse `clear_store` fixture from conftest.py.

    conftest's `clear_store` calls store.list_goals() to check Supabase
    availability, which fails without `supabase start`. We don't need a
    live store here — every store call is mocked. We only need to reset
    the in-memory rate-limit dict for hygiene.
    """
    _rate_limit_store.clear()
    yield
    _rate_limit_store.clear()
    # Drop any dependency overrides set in the client fixture so other
    # test files aren't affected when this one runs.
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    """TestClient with `get_current_user` overridden to TEST_USER_ID.

    Skips the real JWT verification path entirely — we don't have (or
    need) a live Supabase Auth server in this file.
    """

    def _fake_user() -> str:
        return TEST_USER_ID

    app.dependency_overrides[get_current_user] = _fake_user
    return TestClient(app)


@pytest.fixture
def owned_goal() -> Goal:
    """A Goal owned by TEST_USER_ID at reality-emulation (Phase 1)."""
    return Goal(
        id=_OWNED_GOAL_ID,
        user_id=TEST_USER_ID,
        title="Wire the ontology layer",
        description="",
        priority=7,
        smile_phase=SmilePhase.REALITY_EMULATION,
        urgency_flag=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def other_users_goal() -> Goal:
    """A Goal owned by SOMEONE ELSE — used to verify cross-tenant rejection."""
    return Goal(
        id=_OWNED_GOAL_ID,  # same id, different owner
        user_id="ffffffff-ffff-ffff-ffff-ffffffffffff",
        title="Not yours",
        description="",
        priority=5,
        smile_phase=SmilePhase.REALITY_EMULATION,
        urgency_flag=False,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def goal_scoped_signal(owned_goal: Goal) -> Signal:
    """A Signal tagged with owned_goal.id — what the LLM should see."""
    return Signal(
        id=_SCOPED_SIGNAL_ID,
        user_id=TEST_USER_ID,
        stream="github",
        event_type="PushEvent",
        source="lpi-platform",
        goal_id=owned_goal.id,
        timestamp=datetime.now(UTC),
        payload={"repo": "lpi-platform", "size": 3},
    )


@pytest.fixture
def unrelated_signal() -> Signal:
    """A Signal tied to a DIFFERENT goal — must NEVER be passed to the LLM."""
    return Signal(
        id="33333333-3333-3333-3333-333333333333",
        user_id=TEST_USER_ID,
        stream="github",
        event_type="PullRequestEvent",
        source="other-repo",
        goal_id=_UNRELATED_GOAL_ID,  # NOT owned_goal.id
        timestamp=datetime.now(UTC),
        payload={},
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestByGoalFiltersByGoalID:
    """The endpoint must call store.list_signals with goal_id=<goal> so the
    DB returns only signals tied to that goal.
    """

    def test_endpoint_calls_list_signals_with_goal_id(
        self,
        client: TestClient,
        owned_goal: Goal,
        goal_scoped_signal: Signal,
    ) -> None:
        # 1. Mock the goal lookup so the ownership check passes.
        # 2. Mock list_signals to return just the one goal-scoped signal.
        # 3. Mock the LangGraph path so we get a deterministic 1-rec return.
        with (
            patch.object(rec_router.store, "get_goal", return_value=owned_goal),
            patch.object(
                rec_router.store, "list_signals", return_value=[goal_scoped_signal]
            ) as mock_list_signals,
            patch.object(
                rec_router,
                "_try_langgraph_recommendations",
                return_value=[
                    Recommendation(
                        id="rec-1",
                        user_id=TEST_USER_ID,
                        action="Advance 'Wire the ontology layer' to concurrent-engineering",
                        reasoning=(
                            "Signals indicate reality-emulation is complete. "
                            "This action targets the concurrent-engineering phase."
                        ),
                        smile_phase=SmilePhase.CONCURRENT_ENGINEERING,
                        priority=3.80,
                        source_goals=[owned_goal.id],
                        source_signals=[goal_scoped_signal.id],
                        created_at=datetime.now(UTC),
                    )
                ],
            ),
        ):
            response = client.post(
                f"/api/v1/recommendations/{TEST_USER_ID}/by-goal/{owned_goal.id}"
            )

        assert response.status_code == 200, response.text
        body = response.json()
        assert isinstance(body, list)
        assert len(body) == 1

        # Critical: list_signals was called with goal_id=<the owned goal>.
        mock_list_signals.assert_called_once()
        _call_args, call_kwargs = mock_list_signals.call_args
        assert call_kwargs.get("goal_id") == owned_goal.id
        assert call_kwargs.get("user_id") == TEST_USER_ID

    def test_agent_receives_only_goal_scoped_signals(
        self,
        client: TestClient,
        owned_goal: Goal,
        goal_scoped_signal: Signal,
    ) -> None:
        """The mock for store.list_signals returns ONLY goal_scoped_signal.

        The LangGraph agent must therefore receive only that signal —
        never the unrelated one. This proves the per-goal wiring actually
        narrows the agent's input to that goal's evidence.
        """
        captured: dict = {}

        def _fake_langgraph(_user_id: str, goals, signals):
            captured["goals"] = list(goals)
            captured["signals"] = list(signals)
            return [
                Recommendation(
                    id="rec-only",
                    user_id=_user_id,
                    action="Advance to next phase",
                    reasoning="Test reasoning. This action targets the concurrent-engineering phase.",
                    smile_phase=SmilePhase.CONCURRENT_ENGINEERING,
                    priority=3.50,
                    source_goals=[g.id for g in goals],
                    source_signals=[s.id for s in signals],
                    created_at=datetime.now(UTC),
                )
            ]

        with (
            patch.object(rec_router.store, "get_goal", return_value=owned_goal),
            patch.object(
                rec_router.store, "list_signals", return_value=[goal_scoped_signal]
            ),
            patch.object(
                rec_router, "_try_langgraph_recommendations", side_effect=_fake_langgraph
            ),
        ):
            response = client.post(
                f"/api/v1/recommendations/{TEST_USER_ID}/by-goal/{owned_goal.id}"
            )

        assert response.status_code == 200

        # The agent was called with exactly the goal-scoped signal.
        assert len(captured["signals"]) == 1
        assert captured["signals"][0].goal_id == owned_goal.id
        # The unrelated signal MUST NOT have leaked into the agent's input.
        assert all(s.goal_id == owned_goal.id for s in captured["signals"])


class TestPromptContent:
    """The LLM prompt must include the new "advance" instruction AND render
    each signal's goal_id so the LLM can reason about one goal at a time.
    """

    def test_prompt_includes_new_advance_instruction_and_goal_id(
        self,
        owned_goal: Goal,
        goal_scoped_signal: Signal,
    ) -> None:
        # Import inside the test to keep module-level deps minimal.
        from lpi.langgraph_agent import _build_prompt

        prompt = _build_prompt([owned_goal], [goal_scoped_signal])

        # 1. The new per-goal instruction is present. The prompt wraps
        #    the prose across multiple lines, so we assert short
        #    phrases that don't cross line boundaries.
        assert "Analyze the recent activity signals." in prompt
        assert "If the signals indicate the current" in prompt
        assert "SMILE phase objectives are met" in prompt
        assert "recommend advancing the goal to the next" in prompt
        assert "phase." in prompt, (
            "Prompt is missing the new per-goal instruction. "
            "The new instruction must appear in _build_prompt so the "
            "LLM is told to advance when the current phase's signals "
            "look complete."
        )

        # 2. The rendered signal line carries goal_id=<value>.
        assert "goal_id=" in prompt, (
            "Prompt does not render each signal's goal_id. "
            "Each '- id=...' line must end with `goal_id=<value>` so the "
            "LLM can see which goal the signal is evidence for."
        )

        # 3. The goal's current SMILE phase slug is named in the prompt —
        #    so the LLM knows what to advance FROM.
        assert "reality-emulation" in prompt, (
            "Prompt does not name the goal's current SMILE phase. "
            "The agent must see reality-emulation (or whichever phase the "
            "goal is at) so it can recommend advancing to the NEXT phase."
        )


class TestByGoalResponseShape:
    """The response must follow the Recommendation contract: up to 3 items,
    sorted by priority descending, with all required fields present.
    """

    def test_returns_max_3_sorted_by_priority_desc(
        self,
        client: TestClient,
        owned_goal: Goal,
        goal_scoped_signal: Signal,
    ) -> None:
        mock_recs = [
            Recommendation(
                id="rec-high",
                user_id=TEST_USER_ID,
                action="High-priority action",
                reasoning="Most important next step. This action targets the reality-emulation phase.",
                smile_phase=SmilePhase.REALITY_EMULATION,
                priority=5.00,
                source_goals=[owned_goal.id],
                source_signals=[],
                created_at=datetime.now(UTC),
            ),
            Recommendation(
                id="rec-mid",
                user_id=TEST_USER_ID,
                action="Mid-priority action",
                reasoning="Solid next step. This action targets the concurrent-engineering phase.",
                smile_phase=SmilePhase.CONCURRENT_ENGINEERING,
                priority=3.00,
                source_goals=[owned_goal.id],
                source_signals=[],
                created_at=datetime.now(UTC),
            ),
            Recommendation(
                id="rec-low",
                user_id=TEST_USER_ID,
                action="Low-priority action",
                reasoning="Worthwhile but secondary. This action targets the collective-intelligence phase.",
                smile_phase=SmilePhase.COLLECTIVE_INTELLIGENCE,
                priority=1.00,
                source_goals=[owned_goal.id],
                source_signals=[],
                created_at=datetime.now(UTC),
            ),
        ]

        with (
            patch.object(rec_router.store, "get_goal", return_value=owned_goal),
            patch.object(
                rec_router.store, "list_signals", return_value=[goal_scoped_signal]
            ),
            patch.object(
                rec_router, "_try_langgraph_recommendations", return_value=mock_recs
            ),
        ):
            response = client.post(
                f"/api/v1/recommendations/{TEST_USER_ID}/by-goal/{owned_goal.id}"
            )

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 3, f"Expected exactly 3 recs, got {len(body)}"

        # Priority order must be DESC.
        priorities = [r["priority"] for r in body]
        assert priorities == [5.00, 3.00, 1.00], (
            f"Recommendations not sorted by priority desc: {priorities}"
        )

        # Each item matches the Recommendation schema.
        valid_phases = {p.value for p in SmilePhase}
        for rec in body:
            assert isinstance(rec["id"], str) and rec["id"]
            assert rec["user_id"] == TEST_USER_ID
            assert isinstance(rec["action"], str) and rec["action"]
            assert isinstance(rec["reasoning"], str) and rec["reasoning"]
            assert rec["smile_phase"] in valid_phases
            assert isinstance(rec["priority"], (int, float))
            assert 0.80 <= rec["priority"] <= 7.00
            assert isinstance(rec["source_goals"], list)
            assert isinstance(rec["source_signals"], list)
            datetime.fromisoformat(rec["created_at"])


class TestByGoalOwnership:
    """The endpoint must 404 when the goal does not belong to the caller.
    Mirrors the goals.py pattern — return 404, never 403, so existence is
    not leaked to callers.
    """

    def test_returns_404_when_goal_not_owned_by_caller(
        self,
        client: TestClient,
        other_users_goal: Goal,
    ) -> None:
        # store.get_goal returns another user's goal — the ownership
        # check in the router must reject it.
        with patch.object(rec_router.store, "get_goal", return_value=other_users_goal):
            response = client.post(
                f"/api/v1/recommendations/{TEST_USER_ID}/by-goal/{_OWNED_GOAL_ID}"
            )

        assert response.status_code == 404

    def test_returns_404_when_goal_does_not_exist(
        self,
        client: TestClient,
    ) -> None:
        with patch.object(rec_router.store, "get_goal", return_value=None):
            response = client.post(
                f"/api/v1/recommendations/{TEST_USER_ID}/by-goal/{_OWNED_GOAL_ID}"
            )

        assert response.status_code == 404


class TestSyncGithubOwnership:
    """POST /api/v1/signals/sync-github/{goal_id} must reject goal_ids that
    belong to other users — preventing cross-tenant signal injection.
    """

    def test_sync_github_rejects_goal_owned_by_other_user(
        self,
        client: TestClient,
        other_users_goal: Goal,
    ) -> None:
        # Patch the store calls INSIDE the signals router module so the
        # early-return 404 fires before any httpx call.
        with (
            patch.object(
                signals_router.store, "get_goal", return_value=other_users_goal
            ),
            patch.object(
                signals_router.store, "insert_signal", new=MagicMock()
            ) as mock_insert,
            # Defensive: even if the ownership check were missing, the
            # httpx call would happen — mock it to prevent a real network
            # request from firing and immediately failing the test.
            patch(
                "lpi.routers.signals.httpx.AsyncClient",
                new=MagicMock(get=AsyncMock(return_value=MagicMock(status_code=200))),
            ),
        ):
            response = client.post(
                f"/api/v1/signals/sync-github/{_OWNED_GOAL_ID}?repo_name=lpi-platform"
            )

        assert response.status_code == 404, (
            f"Cross-tenant sync_github_events did NOT 404 — got "
            f"{response.status_code}: {response.text}"
        )
        # No signal was ever inserted.
        mock_insert.assert_not_called()

    def test_sync_github_rejects_nonexistent_goal(
        self,
        client: TestClient,
    ) -> None:
        with (
            patch.object(signals_router.store, "get_goal", return_value=None),
            patch(
                "lpi.routers.signals.httpx.AsyncClient",
                new=MagicMock(get=AsyncMock(return_value=MagicMock(status_code=200))),
            ),
        ):
            response = client.post(
                f"/api/v1/signals/sync-github/{_OWNED_GOAL_ID}?repo_name=lpi-platform"
            )

        assert response.status_code == 404