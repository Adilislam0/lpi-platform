-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: Add goal_id FK to activity_signals + strict goal-scoped RLS
-- Date   : 2026-06-25
-- ─────────────────────────────────────────────────────────────────────────────
--
-- WHY THIS MIGRATION EXISTS
-- ──────────────────────────
-- activity_signals (20260611) and goals (20260604) have never been linked
-- at the schema level — a signal only carries `stream`/`event_type`, with
-- no pointer back to the goal it is evidence for. This adds that pointer
-- so signals can be scoped to a specific goal, not just to a user.
--
-- NULLABLE BY DESIGN
-- ────────────────────
-- goal_id is nullable, not NOT NULL. Rows already exist in activity_signals
-- from before this migration with no goal context, and there is no
-- sensible default goal to backfill them with. Making the column NOT NULL
-- here would fail against existing rows (or require an arbitrary backfill).
-- Callers that set goal_id get the new behavior; callers that don't are
-- unaffected.
--
-- ON DELETE SET NULL
-- ────────────────────
-- activity_signals is evidence of what a user actually did — it should
-- outlive the goal it was recorded against. Deleting a goal therefore
-- unlinks its signals (goal_id -> NULL) instead of deleting the signal
-- rows (ON DELETE CASCADE) or blocking the goal delete (default
-- RESTRICT/NO ACTION).
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE activity_signals
    ADD COLUMN IF NOT EXISTS goal_id TEXT REFERENCES goals(id) ON DELETE SET NULL;

-- Look up / filter signals by goal, and back the EXISTS check in the RLS
-- policies below.
CREATE INDEX IF NOT EXISTS idx_as_goal_id
    ON activity_signals (goal_id);


-- ── Strict goal-scoped RLS ───────────────────────────────────────────────────
-- The original policies (20260615000000_signals_rls_and_log_action.sql) only
-- checked auth.uid()::text = user_id on the signal row itself. That's not
-- enough once goal_id exists: a signal's user_id could match the caller
-- while goal_id points at a goal owned by someone else (bad data, or a
-- direct write that bypasses the backend). These replacements add: "if
-- goal_id is set, it must reference a goal this same caller owns."
-- goal_id IS NULL is still allowed, so signals with no goal — including
-- every row inserted before this migration — stay exactly as accessible to
-- their owner as before.

DROP POLICY IF EXISTS "Users read own signals" ON activity_signals;
CREATE POLICY "Users read own signals"
    ON activity_signals
    FOR SELECT
    USING (
        auth.uid()::text = user_id
        AND (
            goal_id IS NULL
            OR EXISTS (
                SELECT 1 FROM goals g
                WHERE g.id = activity_signals.goal_id
                  AND g.user_id = auth.uid()::text
            )
        )
    );

DROP POLICY IF EXISTS "Users insert own signals" ON activity_signals;
CREATE POLICY "Users insert own signals"
    ON activity_signals
    FOR INSERT
    WITH CHECK (
        auth.uid()::text = user_id
        AND (
            goal_id IS NULL
            OR EXISTS (
                SELECT 1 FROM goals g
                WHERE g.id = activity_signals.goal_id
                  AND g.user_id = auth.uid()::text
            )
        )
    );

DROP POLICY IF EXISTS "Users update own signals" ON activity_signals;
CREATE POLICY "Users update own signals"
    ON activity_signals
    FOR UPDATE
    USING (
        auth.uid()::text = user_id
        AND (
            goal_id IS NULL
            OR EXISTS (
                SELECT 1 FROM goals g
                WHERE g.id = activity_signals.goal_id
                  AND g.user_id = auth.uid()::text
            )
        )
    )
    WITH CHECK (
        auth.uid()::text = user_id
        AND (
            goal_id IS NULL
            OR EXISTS (
                SELECT 1 FROM goals g
                WHERE g.id = activity_signals.goal_id
                  AND g.user_id = auth.uid()::text
            )
        )
    );

DROP POLICY IF EXISTS "Users delete own signals" ON activity_signals;
CREATE POLICY "Users delete own signals"
    ON activity_signals
    FOR DELETE
    USING (
        auth.uid()::text = user_id
        AND (
            goal_id IS NULL
            OR EXISTS (
                SELECT 1 FROM goals g
                WHERE g.id = activity_signals.goal_id
                  AND g.user_id = auth.uid()::text
            )
        )
    );
