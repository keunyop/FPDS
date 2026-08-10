BEGIN;

-- Existing registry rows are an auditable snapshot of the collection request.
-- Runtime truth remains the versioned executable market-profile catalog; this
-- backfill prevents stale US rows from requesting the former Canada-oriented
-- contract on the next collection.
UPDATE source_registry_item
SET
    expected_fields = CASE product_type
        WHEN 'chequing' THEN '["product_name","monthly_fee","public_display_fee","minimum_balance","minimum_deposit","fee_waiver_condition"]'::jsonb
        WHEN 'savings' THEN '["product_name","standard_rate","base_12_month_rate","public_display_rate","monthly_fee","public_display_fee","minimum_balance","minimum_deposit"]'::jsonb
        WHEN 'gic' THEN '["product_name","standard_rate","base_12_month_rate","public_display_rate","highest_rate","interest_rate_summary","term_rate_table","term_length_text","term_length_days","minimum_deposit","early_withdrawal_penalty"]'::jsonb
        WHEN 'credit-card' THEN '["product_name","annual_fee","purchase_interest_rate"]'::jsonb
        WHEN 'mortgage' THEN '["product_name","interest_rate_summary","rate_type","term_length_text"]'::jsonb
        WHEN 'personal-loan' THEN '["product_name","interest_rate_summary","interest_rate","loan_amount_text","term_length_text"]'::jsonb
        WHEN 'line-of-credit' THEN '["product_name","interest_rate","interest_rate_summary","credit_limit_text","secured_flag","security_requirement","collateral_text"]'::jsonb
        ELSE expected_fields
    END,
    discovery_metadata = discovery_metadata || jsonb_build_object(
        'market_profile_key', 'US:' || product_type,
        'market_profile_version', '2026-08-09',
        'market_profile_resolution', CASE
            WHEN product_type IN (
                'chequing', 'savings', 'gic', 'credit-card', 'mortgage',
                'personal-loan', 'line-of-credit'
            )
                THEN 'country_override'
            ELSE 'default_fallback'
        END
    ),
    change_reason = 'country_product_market_profile_2026_08_09',
    updated_at = now()
WHERE country_code = 'US'
  AND status = 'active'
  AND product_type IN (
      'chequing',
      'savings',
      'gic',
      'credit-card',
      'mortgage',
      'personal-loan',
      'line-of-credit'
  );

-- Legal/rate/fee documents can remain official supporting evidence, but never
-- standalone products. Service enrollment and calculator routes are neither
-- product details nor governing product evidence and leave active collection
-- scope. This is source-registry cleanup only; canonical status changes remain
-- in the audited remediation path.
UPDATE source_registry_item
SET
    discovery_role = CASE
        WHEN source_type = 'pdf' THEN 'supporting_pdf'
        ELSE 'supporting_html'
    END,
    change_reason = 'us_non_product_document_reclassified_as_supporting',
    updated_at = now()
WHERE country_code = 'US'
  AND status = 'active'
  AND discovery_role = 'detail'
  AND lower(source_name || ' ' || normalized_url) ~
      '(deposit|account|banking|cardholder|credit.card|rate|fee).*(agreement|disclosure|schedule)';

UPDATE source_registry_item
SET
    status = 'inactive',
    change_reason = 'us_non_product_action_or_calculator_removed',
    updated_at = now()
WHERE country_code = 'US'
  AND status = 'active'
  AND discovery_role = 'detail'
  AND lower(source_name || ' ' || normalized_url) ~
      '(calculator|enroll(ment)?|online.banking|service.agreement|short.term.savings.calculator)';

-- A bank may host multiple markets on one allowlisted domain. An explicit
-- Canada route is never a US source, even though the hostname is official.
UPDATE source_registry_item
SET
    status = 'inactive',
    change_reason = 'other_country_market_route',
    updated_at = now()
WHERE country_code = 'US'
  AND status = 'active'
  AND (
        lower(normalized_url) ~ '^https?://[^/]+/ca(/|$)'
        OR lower(normalized_url) ~ '^https?://[^/]+/[a-z]{2}-ca(/|$)'
        OR lower(normalized_url) ~ '^https?://[^/]*\.ca(/|$)'
      );

INSERT INTO migration_history (migration_name)
VALUES ('0034_country_product_market_profiles.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
