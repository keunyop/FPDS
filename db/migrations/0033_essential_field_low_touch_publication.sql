BEGIN;

UPDATE product_type_registry
SET
    description = CASE product_type_code
        WHEN 'chequing' THEN 'Chequing accounts collected for monthly fee, minimum balance, and included or unlimited transactions.'
        WHEN 'savings' THEN 'Savings accounts collected for ongoing rate, monthly fee, and minimum balance.'
        WHEN 'gic' THEN 'Guaranteed investment certificates collected for rate, term, minimum deposit, and redeemability.'
        WHEN 'credit-card' THEN 'Retail credit cards collected for annual fee and purchase interest rate.'
        WHEN 'mortgage' THEN 'Residential mortgages collected for rate or qualified rate summary, rate type, and term.'
        WHEN 'personal-loan' THEN 'Personal installment loans collected for rate or APR summary, amount, and term.'
        WHEN 'line-of-credit' THEN 'Personal lines of credit collected for rate or formula summary, credit limit, and security.'
        ELSE description
    END,
    expected_fields = CASE product_type_code
        WHEN 'chequing' THEN '["product_name","monthly_fee","public_display_fee","minimum_balance","included_transactions","unlimited_transactions_flag"]'::jsonb
        WHEN 'savings' THEN '["product_name","standard_rate","base_12_month_rate","public_display_rate","monthly_fee","public_display_fee","minimum_balance"]'::jsonb
        WHEN 'gic' THEN '["product_name","standard_rate","base_12_month_rate","public_display_rate","highest_rate","interest_rate_summary","term_rate_table","term_length_text","term_length_days","minimum_deposit","redeemable_flag","non_redeemable_flag"]'::jsonb
        WHEN 'credit-card' THEN '["product_name","annual_fee","purchase_interest_rate"]'::jsonb
        WHEN 'mortgage' THEN '["product_name","mortgage_rate","interest_rate_summary","rate_type","term_length_text"]'::jsonb
        WHEN 'personal-loan' THEN '["product_name","interest_rate","interest_rate_summary","loan_amount_text","term_length_text"]'::jsonb
        WHEN 'line-of-credit' THEN '["product_name","interest_rate","interest_rate_summary","credit_limit_text","secured_flag","security_requirement","collateral_text"]'::jsonb
        ELSE expected_fields
    END,
    updated_at = now()
WHERE product_type_code IN (
    'chequing',
    'savings',
    'gic',
    'credit-card',
    'mortgage',
    'personal-loan',
    'line-of-credit'
);

UPDATE source_registry_item
SET
    expected_fields = CASE product_type
        WHEN 'chequing' THEN '["product_name","monthly_fee","public_display_fee","minimum_balance","included_transactions","unlimited_transactions_flag"]'::jsonb
        WHEN 'savings' THEN '["product_name","standard_rate","base_12_month_rate","public_display_rate","monthly_fee","public_display_fee","minimum_balance"]'::jsonb
        WHEN 'gic' THEN '["product_name","standard_rate","base_12_month_rate","public_display_rate","highest_rate","interest_rate_summary","term_rate_table","term_length_text","term_length_days","minimum_deposit","redeemable_flag","non_redeemable_flag"]'::jsonb
        WHEN 'credit-card' THEN '["product_name","annual_fee","purchase_interest_rate"]'::jsonb
        WHEN 'mortgage' THEN '["product_name","mortgage_rate","interest_rate_summary","rate_type","term_length_text"]'::jsonb
        WHEN 'personal-loan' THEN '["product_name","interest_rate","interest_rate_summary","loan_amount_text","term_length_text"]'::jsonb
        WHEN 'line-of-credit' THEN '["product_name","interest_rate","interest_rate_summary","credit_limit_text","secured_flag","security_requirement","collateral_text"]'::jsonb
        ELSE expected_fields
    END,
    updated_at = now()
WHERE product_type IN (
    'chequing',
    'savings',
    'gic',
    'credit-card',
    'mortgage',
    'personal-loan',
    'line-of-credit'
)
  AND status = 'active';

UPDATE processing_policy_config
SET active_flag = false
WHERE policy_key IN (
    'AI_AUTO_APPROVE_MIN_VERIFIED_FIELD_RATIO',
    'COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE',
    'FORCE_REVIEW_ISSUE_CODES'
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
        'policy-ai-auto-approve-min-verified-field-ratio-v4',
        'AI_AUTO_APPROVE_MIN_VERIFIED_FIELD_RATIO',
        4,
        '{"value": 1.0, "note": "Dynamic collection verifies identity plus one fact for every essential comparison requirement; optional fields are outside the denominator."}'::jsonb,
        true,
        'migration:0033_essential_field_low_touch_publication',
        'Requires complete official grounding for the smaller essential-field contract.'
    ),
    (
        'policy-collection-ai-review-auto-approval-min-pass-rate-v4',
        'COLLECTION_AI_REVIEW_AUTO_APPROVAL_MIN_PASS_RATE',
        4,
        '{"value": 1.0, "note": "Residual Review AI may auto-approve only when identity and every requested essential fact are verified or safely corrected."}'::jsonb,
        true,
        'migration:0033_essential_field_low_touch_publication',
        'Removes optional fields from review work while requiring all remaining essentials.'
    ),
    (
        'policy-force-review-issue-codes-v2',
        'FORCE_REVIEW_ISSUE_CODES',
        2,
        '["ambiguous_product_boundary","required_field_missing","invalid_taxonomy_code","invalid_numeric_range","invalid_field_type","invalid_term_value","conflicting_evidence","ambiguous_mapping","inconsistent_cross_field_logic"]'::jsonb,
        true,
        'migration:0033_essential_field_low_touch_publication',
        'Partial-source and confidence warnings do not create Review work when all essential facts are valid and grounded.'
    )
ON CONFLICT (policy_config_id) DO UPDATE
SET
    policy_value = EXCLUDED.policy_value,
    active_flag = EXCLUDED.active_flag,
    notes = EXCLUDED.notes;

INSERT INTO migration_history (migration_name)
VALUES ('0033_essential_field_low_touch_publication.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
