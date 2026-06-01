# Phase 3 — Signals Module Preparation

**Author:** Daksh Garg (Signals prep)  
**Status:** Preparation only — not a Phase 2 gate requirement

## Purpose

The Signals module ingests **activity events** from external streams (Boardy, DataPro+, VSAB, AltioStar, Security, etc.) and stores them for downstream use by the recommendation engine and SMILE workflow. Phase 3 owns full ingestion, query, and persistence; Phase 2 focuses on Goal registry QA.

## Proposed Signal model fields

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `id` | string (UUID) | Server-generated | Primary key |
| `user_id` | string | Auth / context | Owner of the signal |
| `stream` | string | Client | Source system name |
| `event_type` | string | Client | e.g. `match_created`, `alert_triggered` |
| `payload` | object | Client | Stream-specific JSON |
| `timestamp` | datetime (UTC) | Server | Ingestion time |

Defined in code: `lpi.models.SignalCreate` (input) and `lpi.models.Signal` (stored record).

## Storage approach

| Phase | Approach |
|-------|----------|
| Prep (now) | In-memory dict scaffold `_signals: dict[str, Signal]` in `signals.py` — not wired to routes |
| Phase 3 | Persist to Supabase (Postgres) via `supabase` client; optional local dev with Supabase CLI |
| Later | Index by `user_id`, `stream`, `timestamp` for query performance |

## Future API endpoints

| Method | Path | Purpose | Owner phase |
|--------|------|---------|-------------|
| POST | `/api/v1/signals/` | Ingest one signal | Phase 3 |
| GET | `/api/v1/signals/` | List/filter (`user_id`, `stream`, `limit`) | Phase 3 |

Router stubs exist today; handlers raise `NotImplementedError` until Phase 3 implementation.

## Relation to Goal Registry

```
External streams → POST /signals → Signal store
                                      ↓
Goals (Phase 2) ─────────────────→ Recommendation engine (Phase 4)
                                      ↑
                              SMILE phase context
```

- **Goals** define what the user is trying to achieve and current SMILE phase.
- **Signals** provide evidence of real-world activity aligned to those goals.
- **Recommendations** (Phase 4) combine `source_goals` and `source_signals` on the `Recommendation` model.

Signals do not mutate goals directly; correlation happens in the recommendation layer.

## Implementation notes for Phase 3

1. Generate `id` and `timestamp` on ingest; never trust client for those.
2. Validate `stream` against an allowlist or registry when product defines streams.
3. Keep `payload` schema flexible per stream; document per-stream shapes separately.
4. Re-enable gate tests with `LPI_RUN_PHASE_GATES=1` when endpoints are ready.
