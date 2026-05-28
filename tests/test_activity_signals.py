"""Tests for Activity Signals — Phase 3 gate criteria.

Adil owns making these pass.
"""

import pytest


class TestIngestSignal:
    def test_ingest_returns_signal(self, client, sample_signal, phase_gate_enabled: bool) -> None:
        """POST /api/v1/signals/ should store and return the signal."""
        if not phase_gate_enabled:
            pytest.skip("Phase gate tests are disabled by default. Set LPI_RUN_PHASE_GATES=1 to enable.")
        response = client.post("/api/v1/signals/", json=sample_signal)
        assert response.status_code in (200, 201)
        data = response.json()
        assert data["stream"] == "boardy"
        assert "id" in data

    def test_ingest_from_different_streams(self, client, phase_gate_enabled: bool) -> None:
        """Should accept signals from any stream."""
        if not phase_gate_enabled:
            pytest.skip("Phase gate tests are disabled by default. Set LPI_RUN_PHASE_GATES=1 to enable.")
        streams = ["boardy", "datapro", "vsab", "altiostar", "security"]
        for stream in streams:
            signal = {"stream": stream, "event_type": "test", "payload": {}}
            response = client.post("/api/v1/signals/", json=signal)
            assert response.status_code in (200, 201)


class TestQuerySignals:
    def test_list_signals(self, client, phase_gate_enabled: bool) -> None:
        """GET /api/v1/signals/ should return a list."""
        if not phase_gate_enabled:
            pytest.skip("Phase gate tests are disabled by default. Set LPI_RUN_PHASE_GATES=1 to enable.")
        response = client.get("/api/v1/signals/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_by_stream(self, client, phase_gate_enabled: bool) -> None:
        """Should filter signals by stream name."""
        if not phase_gate_enabled:
            pytest.skip("Phase gate tests are disabled by default. Set LPI_RUN_PHASE_GATES=1 to enable.")
        response = client.get("/api/v1/signals/?stream=boardy")
        assert response.status_code == 200
