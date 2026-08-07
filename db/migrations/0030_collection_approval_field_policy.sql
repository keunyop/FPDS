BEGIN;

UPDATE processing_policy_config
SET active_flag = false
WHERE policy_key IN (
    'AI_AUTO_APPROVE_MIN_VERIFIED_FIELD_RATIO',
    'COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE'
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
        'policy-ai-auto-approve-min-verified-field-ratio-v2',
        'AI_AUTO_APPROVE_MIN_VERIFIED_FIELD_RATIO',
        2,
        '{"value": 0.80, "note": "Dynamic candidates need verified official identity and at least 80% grounding across populated decision fields; empty optional fields are omissions."}'::jsonb,
        true,
        'migration:0030_collection_approval_field_policy',
        'Requires official identity plus at least one product-defining fact without treating every empty optional field as a validation failure.'
    ),
    (
        'policy-collection-ai-review-auto-approval-min-pass-rate-v2',
        'COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE',
        2,
        '{"value": 0.80, "note": "Only identity and populated or blocking decision fields are in the approval denominator; empty optional fields are omissions."}'::jsonb,
        true,
        'migration:0030_collection_approval_field_policy',
        'Aligns residual Review AI approval with the executable approval-field contract while preserving hard validation blockers.'
    )
ON CONFLICT (policy_config_id) DO UPDATE
SET policy_value = EXCLUDED.policy_value,
    active_flag = EXCLUDED.active_flag,
    notes = EXCLUDED.notes;

INSERT INTO migration_history (migration_name)
VALUES ('0030_collection_approval_field_policy')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
