-- Migration: Create goal_phase_transitions table for SMILE transition logging
-- Owner: Adil Islam / Yashika Verma (Phase 2)
-- Date: 2026-06-05 (updated 2026-06-07 — corrected SMILE phase slugs)
--
-- WHY THIS TABLE EXISTS
-- ─────────────────────
-- Every valid SMILE phase transition is recorded here:
--   1. Audit trail — who changed what, and when
--   2. Velocity metrics — how long goals spend in each SMILE phase
--   3. Phase 4 recommendation engine input
--
-- CORRECTION: CHECK constraints updated from hallucinated 5-phase slugs
-- to the correct 6-phase SMILE framework slugs.
--
-- This table is INSERT-only in Phase 2. Never UPDATE or DELETE rows here.
--
-- HOW TO VIEW LOGS
-- ─────────────────
-- Supabase Studio → Table Editor → goal_phase_transitions
-- NOT the Logs & Analytics tab — that shows infrastructure logs only.

CREATE TABLE IF NOT EXISTS goal_phase_transitions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id         TEXT        NOT NULL,
    from_phase      TEXT        NOT NULL
                        CHECK (from_phase IN (
                            'reality-emulation',
                            'concurrent-engineering',
                            'collective-intelligence',
                            'contextual-intelligence',
                            'continuous-intelligence',
                            'perpetual-wisdom'
                        )),
    to_phase        TEXT        NOT NULL
                        CHECK (to_phase IN (
                            'reality-emulation',
                            'concurrent-engineering',
                            'collective-intelligence',
                            'contextual-intelligence',
                            'continuous-intelligence',
                            'perpetual-wisdom'
                        )),
    user_id         TEXT        NOT NULL,
    transitioned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gpt_goal_id         ON goal_phase_transitions (goal_id);
CREATE INDEX IF NOT EXISTS idx_gpt_user_id         ON goal_phase_transitions (user_id);
CREATE INDEX IF NOT EXISTS idx_gpt_transitioned_at ON goal_phase_transitions (transitioned_at DESC);