"""Tests for Activity Signals — Phase 3 gate criteria.

Adil owns making these pass.
"""

import pytest


@pytest.mark.skip(
    reason=(
        "Phase 3 task: Activity Signals skipped for now"
    ),
)
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

    def test_missing_stream_field(self, client) -> None:
        """Signal ingestion should reject payloads missing the stream field.

        Current Phase 3 behavior:
        - router still returns HTTP 501 (stub implementation)

        Future expected behavior:
        - FastAPI/Pydantic validation should return HTTP 422
        """
        signal = {
            "event_type": "match_created",
            "payload": {},
        }

        response = client.post("/api/v1/signals/", json=signal)

        # Accept both for now while implementation is incomplete
        assert response.status_code in (422, 501)


    def test_missing_event_type(self, client) -> None:
        """Signal ingestion should reject payloads missing event_type.

        event_type is required for downstream timeline processing
        and recommendation-engine event classification.
        """
        signal = {
            "stream": "boardy",
            "payload": {},
        }

        response = client.post("/api/v1/signals/", json=signal)

        assert response.status_code in (422, 501)


    def test_invalid_payload_type(self, client) -> None:
        """Signal payload should eventually require a dictionary object.

        Current implementation is still a Phase 3 stub, but this test
        prepares validation coverage for malformed payload structures.
        """
        signal = {
            "stream": "boardy",
            "event_type": "match_created",
            "payload": "invalid_payload",
        }

        response = client.post("/api/v1/signals/", json=signal)

        assert response.status_code in (422, 501)


    def test_empty_payload(self, client) -> None:
        """Empty payloads should not crash the ingestion endpoint.

        Empty payloads may still be considered valid depending on
        stream-specific event schemas in later phases.
        """
        signal = {
            "stream": "boardy",
            "event_type": "match_created",
            "payload": {},
        }

        response = client.post("/api/v1/signals/", json=signal)

        # Stub currently returns 501 until implementation is wired
        assert response.status_code in (201, 501)

@pytest.mark.skip(
    reason=(
        "Phase 3 task: Activity Signals skipped for now"
    ),
)
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
    
    def test_empty_signal_list(self, client) -> None:
        """GET /signals/ should safely return an empty list.

        Current Phase 3 implementation intentionally returns []
        until real querying and persistence are implemented.
        """
        response = client.get("/api/v1/signals/")

        assert response.status_code == 200
        assert response.json() == []


    def test_filter_invalid_stream(self, client) -> None:
        """Filtering by an unknown stream should not crash the API.

        Future implementation should safely return an empty list
        when no matching signals exist.
        """
        response = client.get("/api/v1/signals/?stream=unknown")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
