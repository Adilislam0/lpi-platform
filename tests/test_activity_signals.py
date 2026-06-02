"""Tests for Activity Signals — Phase 3 gate criteria.

Adil owns making these pass.
"""

import pytest


@pytest.mark.skip(reason="Phase 3 task: Activity Signals skipped for now") # jsut remove this line when ready to work on these tests
class TestIngestSignal:
    def test_ingest_returns_signal(self, client, sample_signal) -> None:
        """POST /api/v1/signals/ should store and return the signal."""
        response = client.post("/api/v1/signals/", json=sample_signal)
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["stream"] == "boardy"
        assert "id" in data

    def test_ingest_from_different_streams(self, client) -> None:
        """Should accept signals from any stream."""
        streams = ["boardy", "datapro", "vsab", "altiostar", "security"]
        for stream in streams:
            signal = {"stream": stream, "event_type": "test", "payload": {}}
            response = client.post("/api/v1/signals/", json=signal)
            assert response.status_code in (200, 201)


@pytest.mark.skip(reason="Phase 3 task: Activity Signals skipped for now")# just remove this line when ready to work on these tests
class TestQuerySignals:
    def test_list_signals(self, client) -> None:
        """GET /api/v1/signals/ should return a list."""
        response = client.get("/api/v1/signals/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_by_stream(self, client) -> None:
        """Should filter signals by stream name."""
        response = client.get("/api/v1/signals/?stream=boardy")
        assert response.status_code == 200



