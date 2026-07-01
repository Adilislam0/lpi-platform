-- supabase/migrations/20260630000002_create_users.sql
CREATE TABLE IF NOT EXISTS users (
    id          UUID        PRIMARY KEY, -- Maps to auth.users
    name        TEXT,
    email       TEXT        UNIQUE NOT NULL,
    dob         DATE,
    gender      TEXT,
    bio         TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- Basic RLS so users can only read/update their own profile
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" 
    ON users FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" 
    ON users FOR UPDATE USING (auth.uid()::text = id::text);