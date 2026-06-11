-- Migration: Create Activity Signals Table & Indexes
-- Author: Aditi Mehta 
-- Description: Core schema for Phase 3 Module 2 with strict Row Level Security (RLS)

CREATE TABLE activity_signals (
    id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id    UUID NOT NULL,
    stream     VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload    JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── INDEXING STRATEGY ────────────────────────────────────────────────────────

-- Individual lookup indexes for rapid filtering
CREATE INDEX idx_activity_signals_user_id ON activity_signals(user_id);
CREATE INDEX idx_activity_signals_stream ON activity_signals(stream);
CREATE INDEX idx_activity_signals_event_type ON activity_signals(event_type);
CREATE INDEX idx_activity_signals_timestamp ON activity_signals(timestamp DESC);

-- Composite index for high-frequency timeline queries (WHERE user_id = X ORDER BY timestamp DESC)
CREATE INDEX idx_activity_signals_user_time ON activity_signals(user_id, timestamp DESC);

-- JSONB Generalized Inverted Index (GIN) for deep structural payload searches
CREATE INDEX idx_activity_signals_payload ON activity_signals USING GIN (payload);


-- ── SECURITY & ACCESS CONTROL (RLS) ──────────────────────────────────────────

-- Enable Row Level Security to isolate data across tenants
ALTER TABLE activity_signals ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only view data entries belonging to their own user context
CREATE POLICY "Users can only see their own signals"
    ON activity_signals FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can only write data entries validation-stamped to their own user context
CREATE POLICY "Users can only insert their own signals"
    ON activity_signals FOR INSERT
    WITH CHECK (auth.uid() = user_id);