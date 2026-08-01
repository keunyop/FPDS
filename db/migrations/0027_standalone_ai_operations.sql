BEGIN;

-- Registry and other operator workflows can use a model without belonging to
-- an ingestion run. Country ownership for these records is carried in the
-- execution/usage metadata and enforced by the calling Admin operation.
ALTER TABLE model_execution
    ALTER COLUMN run_id DROP NOT NULL;

ALTER TABLE llm_usage_record
    ALTER COLUMN run_id DROP NOT NULL;

INSERT INTO migration_history (migration_name)
VALUES ('0027_standalone_ai_operations.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
