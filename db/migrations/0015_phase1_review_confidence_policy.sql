BEGIN;

UPDATE processing_policy_config
SET active_flag = false
WHERE policy_key = 'AUTO_APPROVE_MIN_CONFIDENCE'
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
VALUES (
    'policy-auto-approve-min-confidence-v2',
    'AUTO_APPROVE_MIN_CONFIDENCE',
    2,
    '{"value": 0.82, "note": "Phase 1 clean-pass deposit candidates may auto-validate once validation errors and force-review issues are absent."}'::jsonb,
    true,
    'migration:0015_phase1_review_confidence_policy',
    'Lower Phase 1 confidence threshold after BMO deposit parser hardening while preserving force-review validation gates.'
)
ON CONFLICT (policy_config_id) DO UPDATE
SET policy_value = EXCLUDED.policy_value,
    active_flag = EXCLUDED.active_flag,
    notes = EXCLUDED.notes;

COMMIT;
