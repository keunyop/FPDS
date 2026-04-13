BEGIN;

CREATE TABLE IF NOT EXISTS user_account (
    user_id text PRIMARY KEY,
    email text NOT NULL UNIQUE CHECK (email = lower(email)),
    display_name text NOT NULL,
    role text NOT NULL CHECK (role IN ('admin', 'reviewer', 'read_only')),
    account_status text NOT NULL CHECK (account_status IN ('active', 'disabled')),
    password_hash text NOT NULL,
    password_algorithm text NOT NULL DEFAULT 'scrypt',
    failed_login_count integer NOT NULL DEFAULT 0,
    last_login_failed_at timestamptz,
    locked_until timestamptz,
    last_login_succeeded_at timestamptz,
    password_changed_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS admin_auth_session (
    auth_session_id text PRIMARY KEY,
    user_id text NOT NULL REFERENCES user_account(user_id),
    session_token_hash text NOT NULL UNIQUE,
    csrf_token text,
    session_status text NOT NULL CHECK (session_status IN ('active', 'revoked', 'expired')),
    issued_at timestamptz NOT NULL,
    last_seen_at timestamptz NOT NULL,
    idle_expires_at timestamptz NOT NULL,
    absolute_expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    revoked_reason text,
    ip_address text,
    user_agent text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS auth_login_attempt (
    login_attempt_id text PRIMARY KEY,
    email text NOT NULL,
    user_id text REFERENCES user_account(user_id),
    ip_address text,
    attempt_outcome text NOT NULL CHECK (attempt_outcome IN ('succeeded', 'failed', 'rate_limited', 'locked_out')),
    failure_reason_code text,
    attempted_at timestamptz NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_account_role_status
    ON user_account (role, account_status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_admin_auth_session_user_status
    ON admin_auth_session (user_id, session_status, absolute_expires_at DESC);

CREATE INDEX IF NOT EXISTS idx_admin_auth_session_lookup
    ON admin_auth_session (session_token_hash, session_status, absolute_expires_at DESC);

CREATE INDEX IF NOT EXISTS idx_auth_login_attempt_email_attempted_at
    ON auth_login_attempt (email, attempted_at DESC);

CREATE INDEX IF NOT EXISTS idx_auth_login_attempt_ip_attempted_at
    ON auth_login_attempt (ip_address, attempted_at DESC);

INSERT INTO migration_history (migration_name)
VALUES ('0002_admin_auth')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
