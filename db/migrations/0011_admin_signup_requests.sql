BEGIN;

ALTER TABLE user_account
    ADD COLUMN IF NOT EXISTS login_id text;

UPDATE user_account
SET login_id = lower(email)
WHERE login_id IS NULL
  AND email IS NOT NULL;

ALTER TABLE user_account
    ALTER COLUMN login_id SET NOT NULL;

ALTER TABLE user_account
    ADD CONSTRAINT user_account_login_id_lowercase
    CHECK (login_id = lower(login_id));

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_account_login_id
    ON user_account (login_id);

ALTER TABLE user_account
    ALTER COLUMN email DROP NOT NULL;

ALTER TABLE auth_login_attempt
    ADD COLUMN IF NOT EXISTS login_id text;

UPDATE auth_login_attempt
SET login_id = lower(email)
WHERE login_id IS NULL
  AND email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_auth_login_attempt_login_id_attempted_at
    ON auth_login_attempt (login_id, attempted_at DESC);

CREATE TABLE IF NOT EXISTS user_signup_request (
    signup_request_id text PRIMARY KEY,
    login_id text NOT NULL CHECK (login_id = lower(login_id)),
    display_name text NOT NULL,
    password_hash text NOT NULL,
    password_algorithm text NOT NULL DEFAULT 'scrypt',
    request_status text NOT NULL CHECK (request_status IN ('pending', 'approved', 'rejected')),
    reviewed_role text CHECK (reviewed_role IN ('admin', 'reviewer', 'read_only')),
    review_reason text,
    requested_at timestamptz NOT NULL DEFAULT now(),
    reviewed_at timestamptz,
    reviewed_by_user_id text REFERENCES user_account(user_id),
    approved_user_id text REFERENCES user_account(user_id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_signup_request_pending_login_id
    ON user_signup_request (login_id)
    WHERE request_status = 'pending';

CREATE INDEX IF NOT EXISTS idx_user_signup_request_status_requested_at
    ON user_signup_request (request_status, requested_at DESC);

INSERT INTO migration_history (migration_name)
VALUES ('0011_admin_signup_requests')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
