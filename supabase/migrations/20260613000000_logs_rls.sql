-- Migration: Enable Row Level Security on log/transition tables
-- Date: 2026-06-13
--
-- WHY
-- ────
-- Same reasoning as 20260612000000_goals_rls.sql: the FastAPI backend
-- already scopes these tables by user_id, but RLS adds a second layer
-- in case a table is ever queried directly with a user's Supabase JWT.
--
-- goal_phase_transitions / user_activity_logs carry user_id (TEXT, the
-- Supabase auth user's UUID as a string), so users may read their own
-- rows. These tables are INSERT-only from the backend's perspective, so
-- no UPDATE/DELETE policies are defined for end users.
--
-- system_logs / request_logs are infrastructure-only and carry no
-- user_id — RLS is enabled with no policies, so only the service role
-- (which bypasses RLS) can access them.
--
-- BACKEND KEY REQUIREMENT
-- ─────────────────────────
-- The FastAPI backend (utils/logging.py) must use the Supabase SERVICE
-- ROLE key (SUPABASE_KEY), which bypasses RLS, since it is the trusted
-- server-side component that writes these rows.

ALTER TABLE goal_phase_transitions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own goal phase transitions"
    ON goal_phase_transitions FOR SELECT
    USING (auth.uid()::text = user_id);

ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own activity logs"
    ON user_activity_logs FOR SELECT
    USING (auth.uid()::text = user_id);

-- Infra-only tables: enable RLS, no policies — locked to service role.
ALTER TABLE system_logs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE request_logs ENABLE ROW LEVEL SECURITY;
