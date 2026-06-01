"""Tests for Goal CRUD — Phase 2 gate criteria.

Adil owns making these pass.

CHANGES vs Adil's first version:
  - body["goal_id"] → body["id"]  (CONFLICT-1 fix — matches OpenAPI contract)
  - Added clear_transition_logs() to conftest autouse fixture (see conftest.py note)
"""
import pytest
class TestCreateGoal:
    def test_create_returns_201(self, client, sample_goal) -> None:
        """POST /api/v1/goals/ should create a goal."""
        response = client.post("/api/v1/goals/", json=sample_goal)
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["title"] == "Learn Docker"
        assert "id" in data

    def test_create_assigns_smile_phase(self, client, sample_goal) -> None:
        """New goal should have the specified SMILE phase."""
        response = client.post("/api/v1/goals/", json=sample_goal)
        assert response.json()["smile_phase"] == "sense"


class TestReadGoal:
    def test_list_goals(self, client) -> None:
        """GET /api/v1/goals/ should return a list."""
        response = client.get("/api/v1/goals/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestUpdateGoal:
    def test_update_smile_phase(self, client, sample_goal) -> None:
        """PATCH should allow a valid forward SMILE phase transition (SENSE → MODEL)."""
        create_resp = client.post("/api/v1/goals/", json=sample_goal)
        assert create_resp.status_code in (200, 201)
        goal_id = create_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/v1/goals/{goal_id}",
            json={"smile_phase": "model"},
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["smile_phase"] == "model"

    def test_invalid_phase_skip_rejected(self, client, sample_goal) -> None:
        """SENSE → INTERVENE is a skip (forbidden) — should return HTTP 422."""
        create_resp = client.post("/api/v1/goals/", json=sample_goal)
        assert create_resp.status_code in (200, 201)
        goal_id = create_resp.json()["id"]

        patch_resp = client.patch(
            f"/api/v1/goals/{goal_id}",
            json={"smile_phase": "intervene"},
        )
        assert patch_resp.status_code == 422


class TestDeleteGoal:
    def test_delete_returns_success(self, client, sample_goal) -> None:
        """DELETE should remove the goal and return { deleted: true, id: ... }."""
        create_resp = client.post("/api/v1/goals/", json=sample_goal)
        assert create_resp.status_code in (200, 201)
        goal_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/v1/goals/{goal_id}")
        assert delete_resp.status_code == 200
        body = delete_resp.json()
        assert body["deleted"] is True
        assert body["id"] == goal_id          # ← FIXED: was body["goal_id"]

        # Verify it's actually gone
        get_resp = client.get(f"/api/v1/goals/{goal_id}")
        assert get_resp.status_code == 404
