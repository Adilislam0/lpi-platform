-- Migration: Enable Row Level Security on goals
-- Date: 2026-06-12
--
-- WHY
-- ────
-- Email/password auth (Supabase Auth) is now required for the goals API.
-- The FastAPI backend enforces per-user ownership in routers/goals.py,
-- but RLS adds a second layer: even if a row is queried with a user's
-- own Supabase JWT (e.g. directly from the frontend), Postgres itself
-- will only return/allow rows where user_id matches auth.uid().
--
-- user_id is stored as TEXT (the Supabase auth user's UUID as a string),
-- so auth.uid() (uuid) is cast to text for comparison.
--
-- BACKEND KEY REQUIREMENT
-- ─────────────────────────
-- The FastAPI backend (store.py) must use the Supabase SERVICE ROLE key
-- (SUPABASE_KEY), which bypasses RLS, since it is the trusted server-side
-- component that already enforces ownership checks itself.

ALTER TABLE goals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own goals"
    ON goals FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own goals"
    ON goals FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own goals"
    ON goals FOR UPDATE
    USING (auth.uid()::text = user_id)
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own goals"
    ON goals FOR DELETE
    USING (auth.uid()::text = user_id);
