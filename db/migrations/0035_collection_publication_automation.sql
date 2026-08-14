BEGIN;

UPDATE processing_policy_config
SET active_flag = false
WHERE policy_key IN (
    'COLLECTION_AUTOMATION_ENABLED',
    'COLLECTION_AUTOMATION_INTERVAL_HOURS',
    'COLLECTION_AUTOMATION_RETRY_HOURS',
    'COLLECTION_AUTOMATION_BATCH_SIZE',
    'COLLECTION_AUTOMATION_REVIEW_RECOVERY_LIMIT',
    'COLLECTION_AUTOMATION_STALE_RUN_HOURS'
)
  AND active_flag = true;

INSERT INTO processing_policy_config (
    policy_config_id,
    policy_key,
    version_no,
    policy_value,
    active_flag,
    created_by,
    notes
)
VALUES
    (
        'policy-collection-automation-enabled-v1',
        'COLLECTION_AUTOMATION_ENABLED',
        1,
        '{"value": true}'::jsonb,
        true,
        'migration:0035_collection_publication_automation',
        'Enables the auditable scheduler path for collection, recovery, and Public refresh.'
    ),
    (
        'policy-collection-automation-interval-hours-v1',
        'COLLECTION_AUTOMATION_INTERVAL_HOURS',
        1,
        '{"value": 168}'::jsonb,
        true,
        'migration:0035_collection_publication_automation',
        'Recollect each active bank and Product Type at least weekly.'
    ),
    (
        'policy-collection-automation-batch-size-v1',
        'COLLECTION_AUTOMATION_BATCH_SIZE',
        1,
        '{"value": 6}'::jsonb,
        true,
        'migration:0035_collection_publication_automation',
        'Bounds each sequential source-catalog collection launch.'
    ),
    (
        'policy-collection-automation-retry-hours-v1',
        'COLLECTION_AUTOMATION_RETRY_HOURS',
        1,
        '{"value": 24}'::jsonb,
        true,
        'migration:0035_collection_publication_automation',
        'Retries failed or partial catalog coverage after a bounded backoff.'
    ),
    (
        'policy-collection-automation-review-recovery-limit-v1',
        'COLLECTION_AUTOMATION_REVIEW_RECOVERY_LIMIT',
        1,
        '{"value": 10}'::jsonb,
        true,
        'migration:0035_collection_publication_automation',
        'Bounds official-domain AI recovery work in each scheduler cycle.'
    ),
    (
        'policy-collection-automation-stale-run-hours-v1',
        'COLLECTION_AUTOMATION_STALE_RUN_HOURS',
        1,
        '{"value": 12}'::jsonb,
        true,
        'migration:0035_collection_publication_automation',
        'Allows abandoned source-catalog runs to stop blocking future scheduled collection.'
    )
ON CONFLICT (policy_config_id) DO UPDATE
SET
    policy_value = EXCLUDED.policy_value,
    active_flag = EXCLUDED.active_flag,
    notes = EXCLUDED.notes;

INSERT INTO migration_history (migration_name)
VALUES ('0035_collection_publication_automation.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
