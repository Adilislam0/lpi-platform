-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: Add ZeroClaw event types to user_activity_logs CHECK constraint
-- Owner  : Daksh Garg
-- Date   : 2026-06-27
-- ─────────────────────────────────────────────────────────────────────────────
--
-- WHY THIS MIGRATION EXISTS
-- ──────────────────────────
-- The ZeroClaw webhook receiver (POST /api/v1/signals/zeroclaw) stores signals
-- with the following event_types in activity_signals:
--   zeroclaw_scan_started
--   zeroclaw_scan_completed
--   zeroclaw_scan_failed
--   vulnerability_detected
--
-- activity_signals has NO CHECK constraint on event_type (intentional — new
-- streams can be added without migrations). So no change is needed there.
--
-- However, user_activity_logs DOES have a CHECK constraint on the `action`
-- column. If we ever log ZeroClaw signal ingestion via log_user_activity(),
-- the action value must be in the allowed list. This migration adds
-- 'zeroclaw_signal_ingested' to prevent silent insert failures (the same
-- class of bug that hit the signals router in Phase 3 before migration
-- 20260615000000 was applied).
--
-- Also adds 'github_signal_synced' which was missing and caused insert
-- failures in the GitHub dynamic sync endpoint (sync-github/{goal_id}).
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE user_activity_logs
    DROP CONSTRAINT IF EXISTS user_activity_logs_action_check;

ALTER TABLE user_activity_logs
    ADD CONSTRAINT user_activity_logs_action_check
    CHECK (action IN (
        'goal_created',
        'goal_updated',
        'goal_deleted',
        'signal_ingested',
        'recommendation_accepted',
        'recommendation_dismissed',
        'github_signal_synced',          -- Phase 4: dynamic GitHub sync endpoint
        'zeroclaw_signal_ingested'       -- ZeroClaw: security scan signals
    ));
