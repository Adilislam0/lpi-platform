"""ZeroClaw payload normalizer — maps raw ZeroClaw JSON to LPI Signal schema.

ZeroClaw emits 4 event types (confirmed June 27, 2026):
    scan.started         → zeroclaw_scan_started
    scan.completed       → zeroclaw_scan_completed
    scan.failed          → zeroclaw_scan_failed
    vulnerability.detected → vulnerability_detected

Raw ZeroClaw payload shape (from schema.json contract):
    {
        "event_type": "vulnerability.detected",
        "scanner_name": "pattern_scanner",
        "timestamp": "2026-06-27T10:00:00Z",
        "vulnerabilities": [
            {
                "id": "PATTERN-0001",
                "severity": "HIGH",
                "file_path": "src/lpi/routers/goals.py",
                "line_number": 42,
                "description": "...",
                "status": "active"
            }
        ]
    }

The normalizer:
  1. Validates the event_type is one we recognise
  2. Maps scanner_name → stream field ("zeroclaw")
  3. Parses timestamp → UTC datetime (falls back to now() if missing/invalid)
  4. Stores the full raw payload in Signal.payload as JSONB
  5. Returns a NormalizedSignal dataclass ready for Signal() construction
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

# Canonical mapping: ZeroClaw event_type → LPI event_type
_EVENT_TYPE_MAP: dict[str, str] = {
    "scan.started": "zeroclaw_scan_started",
    "scan.completed": "zeroclaw_scan_completed",
    "scan.failed": "zeroclaw_scan_failed",
    "vulnerability.detected": "vulnerability_detected",
}


@dataclass
class NormalizedSignal:
    """Intermediate struct after normalization, before Signal() construction."""

    event_type: str          # LPI event_type slug
    stream: str              # always "zeroclaw"
    source: str              # always "zeroclaw_webhook"
    timestamp: datetime      # UTC-aware datetime
    payload: dict            # full raw ZeroClaw payload stored as JSONB


class ZeroClawNormalizationError(ValueError):
    """Raised when the payload cannot be normalized (unknown event type etc.)."""


def normalize(raw: dict) -> NormalizedSignal:
    """Normalize a raw ZeroClaw payload into LPI Signal fields.

    Args:
        raw: The parsed JSON body from the ZeroClaw webhook POST.

    Returns:
        NormalizedSignal ready to be passed to Signal() constructor.

    Raises:
        ZeroClawNormalizationError: if event_type is unknown or payload is
        structurally invalid. The caller should return 400 on this exception.
    """
    raw_event_type = raw.get("event_type", "")

    lpi_event_type = _EVENT_TYPE_MAP.get(raw_event_type)
    if lpi_event_type is None:
        logger.warning(
            "ZeroClaw sent unknown event_type=%r — skipping normalization",
            raw_event_type,
        )
        raise ZeroClawNormalizationError(
            f"Unknown ZeroClaw event_type: {raw_event_type!r}. "
            f"Expected one of: {list(_EVENT_TYPE_MAP.keys())}"
        )

    # Parse timestamp — fall back to now() if missing or malformed
    raw_ts = raw.get("timestamp")
    timestamp: datetime
    if raw_ts:
        try:
            timestamp = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)
        except (ValueError, AttributeError):
            logger.warning(
                "ZeroClaw sent unparseable timestamp %r — using now()", raw_ts
            )
            timestamp = datetime.now(UTC)
    else:
        timestamp = datetime.now(UTC)

    return NormalizedSignal(
        event_type=lpi_event_type,
        stream="zeroclaw",
        source="zeroclaw_webhook",
        timestamp=timestamp,
        payload=raw,  # store full raw payload as JSONB
    )
