-- Migration: Create user_activity_logs and system_logs tables
-- Owner: Adil Islam / Yashika Verma (Phase 2)
-- Date: 2026-06-07
--
-- These two tables complete the dual-sync logging implementation.
-- goal_phase_transitions already created in 20260605 migration.
--
-- HOW TO VIEW LOGS
-- ─────────────────
-- Supabase Studio → Table Editor → select table name
-- NOT the Logs & Analytics tab — that shows infrastructure logs only.
--
-- QUERIES
-- ────────
-- SELECT * FROM user_activity_logs ORDER BY logged_at DESC LIMIT 50;
-- SELECT * FROM system_logs ORDER BY logged_at DESC LIMIT 50;

-- ── 1. User Activity Log ───────────────────────────────────────────────────────
-- Records every user-initiated mutation: goal_created, goal_updated, goal_deleted
-- Written by log_user_activity() in utils/logging.py

CREATE TABLE IF NOT EXISTS user_activity_logs (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     TEXT        NOT NULL,
    action      TEXT        NOT NULL
                    CHECK (action IN (
                        'goal_created',
                        'goal_updated',
                        'goal_deleted'
                    )),
    resource_id TEXT        NOT NULL,
    metadata    JSONB       NOT NULL DEFAULT '{}',
    logged_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ual_user_id   ON user_activity_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_ual_action    ON user_activity_logs (action);
CREATE INDEX IF NOT EXISTS idx_ual_logged_at ON user_activity_logs (logged_at DESC);


-- ── 2. System Event Log ────────────────────────────────────────────────────────
-- Records platform-level events: app startup, errors, warnings
-- Written by log_system_event() in utils/logging.py

CREATE TABLE IF NOT EXISTS system_logs (
    id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    event     TEXT        NOT NULL,
    level     TEXT        NOT NULL DEFAULT 'info'
                  CHECK (level IN ('info', 'warning', 'error')),
    detail    TEXT        NOT NULL DEFAULT '',
    metadata  JSONB       NOT NULL DEFAULT '{}',
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sl_level     ON system_logs (level);
CREATE INDEX IF NOT EXISTS idx_sl_logged_at ON system_logs (logged_at DESC);