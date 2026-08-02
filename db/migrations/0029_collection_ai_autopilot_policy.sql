BEGIN;

UPDATE processing_policy_config
SET active_flag = false
WHERE policy_key IN (
    'AI_AUTO_APPROVE_MIN_VERIFIED_FIELD_RATIO',
    'COLLECTION_AI_REVIEW_AUTOPILOT_ENABLED',
    'COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE',
    'COLLECTION_AI_REVIEW_AUTOPILOT_MAX_CANDIDATES'
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
        'policy-ai-auto-approve-min-verified-field-ratio-v1',
        'AI_AUTO_APPROVE_MIN_VERIFIED_FIELD_RATIO',
        1,
        '{"value": 0.80, "note": "Dynamic candidates need verified official identity and at least 80% decision-field grounding before normal auto-validation."}'::jsonb,
        true,
        'migration:0029_collection_ai_autopilot_policy',
        'Replaces unconditional dynamic-product manual review with official-source AI eligibility plus existing validation gates.'
    ),
    (
        'policy-collection-ai-review-autopilot-enabled-v1',
        'COLLECTION_AI_REVIEW_AUTOPILOT_ENABLED',
        1,
        '{"value": true, "note": "Run bounded official-domain AI remediation for active review tasks left by a product collection."}'::jsonb,
        true,
        'migration:0029_collection_ai_autopilot_policy',
        'Product Owner-approved low-touch collection default with a reversible operational kill switch.'
    ),
    (
        'policy-collection-ai-review-auto-approval-min-pass-rate-v1',
        'COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE',
        1,
        '{"value": 0.80, "note": "Every requested review field remains in the denominator; product identity and an official source are mandatory."}'::jsonb,
        true,
        'migration:0029_collection_ai_autopilot_policy',
        'Keeps collection-generated Review AI approval aligned with the approved full-field threshold.'
    ),
    (
        'policy-collection-ai-review-autopilot-max-candidates-v1',
        'COLLECTION_AI_REVIEW_AUTOPILOT_MAX_CANDIDATES',
        1,
        '{"value": 200, "note": "Bound automatic review AI calls per collection run."}'::jsonb,
        true,
        'migration:0029_collection_ai_autopilot_policy',
        'Limits cost and blast radius while covering normal Admin collection batches.'
    )
ON CONFLICT (policy_config_id) DO UPDATE
SET policy_value = EXCLUDED.policy_value,
    active_flag = EXCLUDED.active_flag,
    notes = EXCLUDED.notes;

INSERT INTO migration_history (migration_name)
VALUES ('0029_collection_ai_autopilot_policy')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
