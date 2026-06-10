-- Migration: Create Activity Signals Table & Indexes
-- Author: Aditi Mehta
-- Description: Core schema matching lpi.models.Signal

CREATE TABLE activity_signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    stream VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexing strategy 
CREATE INDEX idx_activity_signals_user_id ON activity_signals(user_id);
CREATE INDEX idx_activity_signals_stream ON activity_signals(stream);
CREATE INDEX idx_activity_signals_timestamp ON activity_signals(timestamp DESC);