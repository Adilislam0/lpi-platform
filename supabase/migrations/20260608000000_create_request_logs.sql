-- Migration: Create request_logs table for API request timing telemetry

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS request_logs (
    id uuid NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    method text NOT NULL,
    path text NOT NULL,
    status_code integer NOT NULL,
    duration_ms double precision NOT NULL,
    request_id text NOT NULL,
    logged_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rl_path      ON request_logs (path);
CREATE INDEX IF NOT EXISTS idx_rl_status    ON request_logs (status_code);
CREATE INDEX IF NOT EXISTS idx_rl_logged_at ON request_logs (logged_at DESC);
