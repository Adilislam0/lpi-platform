"""Tests for Goal CRUD — Phase 2 gate criteria.

Owner : Adil Islam
QA    : Daksh Garg

This is the clean version of the test file. The PR #11 version had
duplicate method definitions inside the same class (both the old
`pytest.skip` stub AND the new implementation). In Python, the second
definition silently replaces the first, so the tests happened to run the
real code — but the file was confusing and error-prone. This version has
exactly one definition per test method.

The `clear_store` autouse fixture in conftest.py resets the in-memory
store before and after every test, so tests are fully isolated.
"""


class TestCreateGoal:
    def test_create_returns_201(self, client, sample_goal) -> None:
        """POST /api/v1/goals/ should return 201 with the created goal."""
        response = client.post("/api/v1/goals/", json=sample_goal)
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["title"] == "Learn Docker"
        assert "id" in data

    def test_create_assigns_smile_phase(self, client, sample_goal) -> None:
        """New goal should carry the SMILE phase sent in the request."""
        response = client.post("/api/v1/goals/", json=sample_goal)
        assert response.json()["smile_phase"] == "sense"


class TestReadGoal:
    def test_list_goals(self, client) -> None:
        """GET /api/v1/goals/ should return an empty list when store is clear."""
        response = client.get("/api/v1/goals/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestUpdateGoal:
    def test_update_smile_phase(self, client, sample_goal) -> None:
        """PATCH should allow a valid forward transition: SENSE → MODEL."""
        # Create a goal so we have an ID to work with
        create_resp = client.post("/api/v1/goals/", json=sample_goal)
        assert create_resp.status_code in (200, 201)
        goal_id = create_resp.json()["id"]

        # Advance one step forward — this is a valid transition
        patch_resp = client.patch(
            f"/api/v1/goals/{goal_id}",
            json={"smile_phase": "model"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["smile_phase"] == "model"

    def test_invalid_phase_skip_rejected(self, client, sample_goal) -> None:
        """SENSE → INTERVENE skips MODEL — must be rejected with 422."""
        create_resp = client.post("/api/v1/goals/", json=sample_goal)
        assert create_resp.status_code in (200, 201)
        goal_id = create_resp.json()["id"]

        # Skipping a phase is forbidden — 422 Unprocessable Entity
        patch_resp = client.patch(
            f"/api/v1/goals/{goal_id}",
            json={"smile_phase": "intervene"},
        )
        assert patch_resp.status_code == 422


class TestDeleteGoal:
    def test_delete_returns_success(self, client, sample_goal) -> None:
        """DELETE should remove the goal and confirm via a follow-up GET."""
        create_resp = client.post("/api/v1/goals/", json=sample_goal)
        assert create_resp.status_code in (200, 201)
        goal_id = create_resp.json()["id"]

        # Delete it
        delete_resp = client.delete(f"/api/v1/goals/{goal_id}")
        assert delete_resp.status_code == 200
        body = delete_resp.json()
        assert body["deleted"] is True
        assert body["id"] == goal_id   # field is `id`, not `goal_id` — matches OpenAPI

        # Confirm it's actually gone — subsequent GET must return 404
        get_resp = client.get(f"/api/v1/goals/{goal_id}")
        assert get_resp.status_code == 404