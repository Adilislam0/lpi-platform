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

REVIEW FIXES (Jaivardhan, July 1 2026)
───────────────────────────────────────
  Fix #1 — Deterministic signal ID (was random UUID, dedup never triggered)
  Fix #7 — Reject malformed timestamps with ValueError instead of silently
            substituting now() — bad timestamps corrupt analytics
  Fix #8 — Pydantic schema validation before normalization
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

# Canonical mapping: ZeroClaw event_type → LPI event_type
_EVENT_TYPE_MAP: dict[str, str] = {
    "scan.started": "zeroclaw_scan_started",
    "scan.completed": "zeroclaw_scan_completed",
    "scan.failed": "zeroclaw_scan_failed",
    "vulnerability.detected": "vulnerability_detected",
}

_VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
_VALID_STATUSES = {"active", "suppressed"}


# ── Fix #8: Pydantic schema validation ───────────────────────────────────────

class ZeroClawVulnerability(BaseModel):
    """Validates a single vulnerability entry from ZeroClaw."""
    id: str
    severity: str
    file_path: str
    line_number: int
    description: str
    status: str = "active"

    @field_validator("severity")
    @classmethod
    def _valid_severity(cls, v: str) -> str:
        if v not in _VALID_SEVERITIES:
            raise ValueError(f"severity must be one of {_VALID_SEVERITIES}, got {v!r}")
        return v

    @field_validator("status")
    @classmethod
    def _valid_status(cls, v: str) -> str:
        if v not in _VALID_STATUSES:
            raise ValueError(f"status must be one of {_VALID_STATUSES}, got {v!r}")
        return v


class ZeroClawWebhookPayload(BaseModel):
    """Validates the top-level ZeroClaw webhook payload before normalization."""
    event_type: str
    scanner_name: str
    timestamp: str
    vulnerabilities: list[ZeroClawVulnerability] = []


# ── Output type ───────────────────────────────────────────────────────────────

@dataclass
class NormalizedSignal:
    """Intermediate struct after normalization, before Signal() construction."""

    signal_id: str           # deterministic SHA-256 of payload — Fix #1
    event_type: str          # LPI event_type slug
    stream: str              # always "zeroclaw"
    source: str              # always "zeroclaw_webhook"
    timestamp: datetime      # UTC-aware datetime — Fix #7: raises on bad ts
    payload: dict            # full raw ZeroClaw payload stored as JSONB


class ZeroClawNormalizationError(ValueError):
    """Raised when the payload cannot be normalized."""


class ZeroClawTimestampError(ZeroClawNormalizationError):
    """Raised specifically for malformed timestamps — Fix #7."""


# ── Fix #1: Deterministic ID generation ──────────────────────────────────────

def _deterministic_id(raw: dict[str, Any]) -> str:
    """Generate a deterministic SHA-256 ID from the payload.

    Fix #1 (Jaivardhan review): the original code used uuid4() which generates
    a new random ID on every request. If ZeroClaw retries the same event, the
    second insert gets a different ID and the UNIQUE constraint never fires —
    4 retries = 4 duplicate signals in the DB.

    Using SHA-256 over the sorted JSON means:
        same payload → same ID → UNIQUE constraint rejects duplicate → correct
    """
    canonical = json.dumps(raw, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── Main normalizer ───────────────────────────────────────────────────────────

def normalize(raw: dict[str, Any]) -> NormalizedSignal:
    """Normalize and validate a raw ZeroClaw payload into LPI Signal fields.

    Args:
        raw: The parsed JSON body from the ZeroClaw webhook POST.

    Returns:
        NormalizedSignal ready to be passed to Signal() constructor.

    Raises:
        ZeroClawNormalizationError: unknown event_type (caller returns 200+skip)
        ZeroClawTimestampError: malformed timestamp (caller returns 400)
        pydantic.ValidationError: schema validation failure (caller returns 400)
    """
    # Fix #8: validate schema first before any normalization
    # Raises pydantic.ValidationError on bad field types/values
    validated = ZeroClawWebhookPayload.model_validate(raw)

    # Fix #6: unknown events now raise clearly — caller logs WARNING
    # (previously silently skipped with no log — hard to detect data loss)
    lpi_event_type = _EVENT_TYPE_MAP.get(validated.event_type)
    if lpi_event_type is None:
        raise ZeroClawNormalizationError(
            f"Unknown ZeroClaw event_type: {validated.event_type!r}. "
            f"Expected one of: {list(_EVENT_TYPE_MAP.keys())}"
        )

    # Fix #7: reject malformed timestamps instead of silently using now()
    # Bad timestamps corrupt analytics — better to reject with 400
    try:
        timestamp = datetime.fromisoformat(
            validated.timestamp.replace("Z", "+00:00")
        )
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
    except (ValueError, AttributeError) as exc:
        raise ZeroClawTimestampError(
            f"Malformed ZeroClaw timestamp {validated.timestamp!r}: {exc}"
        ) from exc

    # Fix #1: deterministic ID — same payload always produces same ID
    signal_id = _deterministic_id(raw)

    return NormalizedSignal(
        signal_id=signal_id,
        event_type=lpi_event_type,
        stream="zeroclaw",
        source="zeroclaw_webhook",
        timestamp=timestamp,
        payload=raw,
    )
