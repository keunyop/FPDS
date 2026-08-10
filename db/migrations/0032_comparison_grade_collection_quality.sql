BEGIN;

UPDATE product_type_registry
SET
    description = CASE product_type_code
        WHEN 'credit-card' THEN 'Retail credit cards with evidence-grounded annual fee and purchase interest rate for comparison.'
        WHEN 'mortgage' THEN 'Residential mortgage products with evidence-grounded rate or rate summary, rate type, and term for comparison.'
        WHEN 'personal-loan' THEN 'Personal installment loans with evidence-grounded APR or rate summary, amount, and term for comparison.'
        WHEN 'line-of-credit' THEN 'Personal lines of credit with an evidence-grounded rate or rate formula and credit limit for comparison.'
        ELSE description
    END,
    expected_fields = CASE product_type_code
        WHEN 'mortgage' THEN expected_fields ||
            CASE WHEN expected_fields ? 'interest_rate_summary' THEN '[]'::jsonb ELSE '["interest_rate_summary"]'::jsonb END
        WHEN 'personal-loan' THEN expected_fields ||
            CASE WHEN expected_fields ? 'interest_rate_summary' THEN '[]'::jsonb ELSE '["interest_rate_summary"]'::jsonb END
        WHEN 'line-of-credit' THEN expected_fields ||
            CASE WHEN expected_fields ? 'interest_rate_summary' THEN '[]'::jsonb ELSE '["interest_rate_summary"]'::jsonb END
        ELSE expected_fields
    END,
    updated_at = now()
WHERE product_family = 'lending'
  AND product_type_code IN ('credit-card', 'mortgage', 'personal-loan', 'line-of-credit');

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
        'policy-ai-auto-approve-min-verified-field-ratio-v3',
        'AI_AUTO_APPROVE_MIN_VERIFIED_FIELD_RATIO',
        3,
        '{"value": 0.80, "note": "Dynamic candidates need verified identity and every mandatory comparison requirement in the assessed-field denominator; missing rate, price, amount, or term blocks approval."}'::jsonb,
        true,
        'migration:0032_comparison_grade_collection_quality',
        'Supersedes the populated-only denominator. Optional marketing fields remain omissions, but mandatory comparison fields never are.'
    ),
    (
        'policy-collection-ai-review-auto-approval-min-pass-rate-v3',
        'COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE',
        3,
        '{"value": 0.80, "note": "Residual Review AI assesses product identity plus every mandatory comparison requirement and cannot approve an incomplete product."}'::jsonb,
        true,
        'migration:0032_comparison_grade_collection_quality',
        'Keeps the 80% grounding threshold while making comparison completeness an independent fail-closed approval gate.'
    )
ON CONFLICT (policy_config_id) DO UPDATE
SET policy_value = EXCLUDED.policy_value,
    active_flag = EXCLUDED.active_flag,
    notes = EXCLUDED.notes;

INSERT INTO migration_history (migration_name)
VALUES ('0032_comparison_grade_collection_quality.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
