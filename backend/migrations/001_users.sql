-- Personality Playground auth + allowlist schema

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email_hash TEXT NOT NULL UNIQUE,
    email_enc TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT,
    oauth_provider TEXT,
    oauth_sub TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'denied', 'revoked')),
    role TEXT NOT NULL DEFAULT 'user'
        CHECK (role IN ('user', 'admin')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_oauth
    ON users (oauth_provider, oauth_sub)
    WHERE oauth_provider IS NOT NULL AND oauth_sub IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_status ON users (status);
