-- Migration: Create Unified Activity Signals Table & Performance Indexes
-- Joint Authors: Aditi Mehta & Adil Islam
-- Date: 2026-06-12
-- Description: Core schema for Phase 3 with strict RLS and advanced indexing strings

CREATE TABLE IF NOT EXISTS activity_signals (
    id         TEXT        PRIMARY KEY,
    user_id    TEXT        NOT NULL DEFAULT 'default_user',
    stream     TEXT        NOT NULL,
    event_type TEXT        NOT NULL,
    payload    JSONB       NOT NULL DEFAULT '{}'::jsonb,
    source     TEXT        NOT NULL DEFAULT 'api',
    timestamp  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── INDEXING STRATEGY ────────────────────────────────────────────────────────

-- Individual lookup indexes for rapid filtering
CREATE INDEX IF NOT EXISTS idx_activity_signals_user_id    ON activity_signals(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_signals_stream     ON activity_signals(stream);
CREATE INDEX IF NOT EXISTS idx_activity_signals_event_type ON activity_signals(event_type);
CREATE INDEX IF NOT EXISTS idx_activity_signals_source     ON activity_signals(source);
CREATE INDEX IF NOT EXISTS idx_activity_signals_timestamp  ON activity_signals(timestamp DESC);

-- Composite index for high-frequency timeline queries (WHERE user_id = X ORDER BY timestamp DESC)
CREATE INDEX IF NOT EXISTS idx_activity_signals_user_time ON activity_signals(user_id, timestamp DESC);

-- JSONB Generalized Inverted Index (GIN) for deep structural payload searches
CREATE INDEX IF NOT EXISTS idx_activity_signals_payload ON activity_signals USING GIN (payload);


-- ── SECURITY & ACCESS CONTROL (RLS) ──────────────────────────────────────────

-- Enable Row Level Security to isolate data across tenants
ALTER TABLE activity_signals ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view data entries belonging to their own user context
DROP POLICY IF EXISTS "Users can only see their own signals" ON activity_signals;
CREATE POLICY "Users can only see their own signals"
    ON activity_signals FOR SELECT
    USING (auth.uid()::text = user_id);

-- Policy: Users can only write data entries validation-stamped to their own user context
DROP POLICY IF EXISTS "Users can only insert their own signals" ON activity_signals;
CREATE POLICY "Users can only insert their own signals"
    ON activity_signals FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);