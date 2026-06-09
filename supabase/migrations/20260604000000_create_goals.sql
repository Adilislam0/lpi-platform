-- Migration: Create goals table for LPI Platform Phase 2
-- Owner: Adil Islam
-- Date: 2026-06-04 (updated 2026-06-07 — corrected SMILE phase slugs)
--
-- CORRECTION: smile_phase CHECK constraint updated from hallucinated 5-phase
-- slugs (sense, model, intervene, learn, evolve) to the correct 6-phase SMILE
-- framework slugs from data/smile-framework.json.
-- Default also updated from 'sense' to 'reality-emulation' (Phase 1).

CREATE TABLE IF NOT EXISTS goals (
    id           TEXT        PRIMARY KEY,
    user_id      TEXT        NOT NULL DEFAULT 'default_user',
    title        TEXT        NOT NULL,
    description  TEXT        NOT NULL DEFAULT '',
    priority     INTEGER     NOT NULL DEFAULT 5,
    smile_phase  TEXT        NOT NULL DEFAULT 'reality-emulation'
                     CHECK (smile_phase IN (
                         'reality-emulation',
                         'concurrent-engineering',
                         'collective-intelligence',
                         'contextual-intelligence',
                         'continuous-intelligence',
                         'perpetual-wisdom'
                     )),
    urgency_flag BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for common filter queries
CREATE INDEX IF NOT EXISTS idx_goals_user_id     ON goals (user_id);
CREATE INDEX IF NOT EXISTS idx_goals_smile_phase ON goals (smile_phase);