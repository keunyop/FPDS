BEGIN;

ALTER TABLE aggregate_refresh_request
    DROP CONSTRAINT IF EXISTS aggregate_refresh_request_trigger_reason_check;

ALTER TABLE aggregate_refresh_request
    ADD CONSTRAINT aggregate_refresh_request_trigger_reason_check
    CHECK (trigger_reason IN ('review_approval', 'manual_retry', 'auto_promotion'));

INSERT INTO migration_history (migration_name)
VALUES ('0016_auto_promotion_aggregate_trigger.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
