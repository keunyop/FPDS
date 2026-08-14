BEGIN;

-- US credit-card offers commonly disclose a creditworthiness-based variable
-- purchase APR range. The range-preserving summary is the preferred essential
-- comparison fact; an exact scalar remains a valid alternative in runtime
-- policy for cards that publish one fixed purchase APR.
UPDATE source_registry_item
SET
    expected_fields = CASE
        WHEN expected_fields ? 'purchase_interest_rate_summary' THEN expected_fields
        ELSE expected_fields || '["purchase_interest_rate_summary"]'::jsonb
    END,
    discovery_metadata = discovery_metadata || jsonb_build_object(
        'market_profile_key', 'US:credit-card',
        'market_profile_version', '2026-08-12-v2',
        'market_profile_resolution', 'country_override'
    ),
    change_reason = 'us_purchase_apr_range_contract_2026_08_12',
    updated_at = now()
WHERE country_code = 'US'
  AND product_type = 'credit-card'
  AND status = 'active';

INSERT INTO migration_history (migration_name)
VALUES ('0039_us_credit_card_apr_range_contract.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
