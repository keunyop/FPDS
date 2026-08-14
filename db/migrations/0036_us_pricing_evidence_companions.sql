BEGIN;

-- US issuers commonly disclose a purchase APR range plus introductory or
-- fallback conditions. Keep the exact source-language summary alongside the
-- existing numeric comparison field so Public never turns a range into an
-- unlabeled single rate.
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
    change_reason = 'us_purchase_apr_summary_2026_08_12',
    updated_at = now()
WHERE country_code = 'US'
  AND product_type = 'credit-card'
  AND status = 'active';

INSERT INTO migration_history (migration_name)
VALUES ('0036_us_pricing_evidence_companions.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
