"""Tests for Goal CRUD — Phase 2 gate criteria.

Adil owns making these pass.
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
    def test_update_smile_phase(self, client) -> None:
        """PATCH should allow SMILE phase transition."""
        pytest.skip("Implement after create works")

    def test_invalid_phase_skip_rejected(self, client) -> None:
        """SENSE → INTERVENE (skip) should be rejected."""
        pytest.skip("Implement after phase validation is wired")


class TestDeleteGoal:
    def test_delete_returns_success(self, client) -> None:
        """DELETE /api/v1/goals/{id} should remove the goal."""
        pytest.skip("Implement after create works")
