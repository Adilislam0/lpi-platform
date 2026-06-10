# Activity Signals Backend Documentation

## Data Fields
* `id`: UUID primary key generated automatically by the server.
* `user_id`: UUID mapping to the application user triggering the event.
* `stream`: String grouping identifier for the source system (e.g., Boardy, DataPro+).
* `event_type`: String action slug tracking specific user behaviors.
* `payload`: Flexible JSONB dictionary holding stream-specific nested metadata.
* `timestamp`: TIMESTAMPTZ server-generated ingestion timestamp.

## Indexing Strategy
As specified in `phase3_signals_prep.md`, dedicated B-Tree performance indexes are applied directly to the `user_id`, `stream`, and `timestamp` columns to eliminate sequential table scans during downstream recommendation engine evaluations.