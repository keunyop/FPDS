BEGIN;

CREATE TABLE IF NOT EXISTS aggregate_refresh_request (
    aggregate_refresh_request_id text PRIMARY KEY,
    refresh_scope text NOT NULL,
    country_code text NOT NULL,
    request_status text NOT NULL CHECK (request_status IN ('queued', 'started', 'completed', 'failed')),
    trigger_reason text NOT NULL CHECK (trigger_reason IN ('review_approval', 'manual_retry')),
    requested_by_user_id text REFERENCES user_account(user_id),
    requested_by_label text,
    review_task_id text REFERENCES review_task(review_task_id),
    product_id text REFERENCES canonical_product(product_id),
    request_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    requested_at timestamptz NOT NULL,
    started_at timestamptz,
    completed_at timestamptz,
    snapshot_id text REFERENCES aggregate_refresh_run(snapshot_id),
    error_summary text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_aggregate_refresh_request_scope_status_requested_at
    ON aggregate_refresh_request (refresh_scope, country_code, request_status, requested_at DESC);

CREATE INDEX IF NOT EXISTS idx_aggregate_refresh_request_snapshot_id
    ON aggregate_refresh_request (snapshot_id);

INSERT INTO migration_history (migration_name)
VALUES ('0010_aggregate_refresh_queue.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
