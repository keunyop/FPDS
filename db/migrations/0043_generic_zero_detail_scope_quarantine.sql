BEGIN;

-- Persist current official routes for the named-bank scopes that have direct,
-- collectable product evidence. These are data facts; the recurrence control
-- below is intentionally bank- and Product-Type-agnostic.
WITH verified_routes(
    bank_code,
    product_type,
    coverage_source_url,
    current_offering_summary
) AS (
    VALUES
        ('FNBC', 'chequing', 'https://www.fnbc.ca/personal/banking/chequing-accounts', 'FNBC publishes current personal chequing accounts and account features.'),
        ('FNBC', 'gic', 'https://www.fnbc.ca/personal/investing/term-deposits', 'FNBC publishes current personal term deposits.'),
        ('FNBC', 'line-of-credit', 'https://www.fnbc.ca/personal/borrowing/lines-of-credit', 'FNBC publishes current personal lines of credit.'),
        ('FNBC', 'mortgage', 'https://www.fnbc.ca/personal/borrowing/mortgages-and-home-financing', 'FNBC publishes current mortgages and home-financing products.'),
        ('FNBC', 'personal-loan', 'https://www.fnbc.ca/personal/borrowing/personal-loans', 'FNBC publishes current personal loans.'),
        ('FNBC', 'savings', 'https://www.fnbc.ca/personal/banking/saving-accounts', 'FNBC publishes current personal savings accounts on an official product-family page.'),
        ('HAVENTREE', 'chequing', 'https://www.haventreebank.com/en-CA/accounts/everyday-growth-account', 'Haventree publishes the Everyday Growth Account as a hybrid account with traditional chequing functionality.'),
        ('HAVENTREE', 'gic', 'https://www.haventreebank.com/accounts/gic', 'Haventree publishes current GIC products and fixed-term features.'),
        ('HAVENTREE', 'mortgage', 'https://www.haventreebank.com/en-CA/mortgages', 'Haventree publishes current mortgage products and broker routes.'),
        ('HAVENTREE', 'savings', 'https://www.haventreebank.com/en-CA/accounts/everyday-growth-account', 'Haventree publishes the Everyday Growth Account as a hybrid high-interest savings and everyday account.'),
        ('HOMEEQUITY', 'gic', 'https://www.homeequitybank.ca/products/gic/', 'HomeEquity Bank publishes current broker-distributed GICs, terms, and rates.'),
        ('HOMEEQUITY', 'mortgage', 'https://www.homeequitybank.ca/products/chip-reverse-mortgage/', 'HomeEquity Bank publishes the current CHIP Reverse Mortgage product.')
)
UPDATE source_registry_catalog_item AS catalog
SET
    status = 'active',
    coverage_source_url = verified_routes.coverage_source_url,
    normalized_coverage_source_url = regexp_replace(verified_routes.coverage_source_url, '/+$', ''),
    coverage_source_metadata = jsonb_build_object(
        'verification_status', 'verified',
        'verification_method', 'official_site_and_persisted_run_evidence_audit',
        'verification_scope', 'current_directly_collectable_product_route',
        'current_offering_summary', verified_routes.current_offering_summary,
        'verified_at', '2026-08-26T00:00:00-07:00',
        'collection_eligibility', jsonb_build_object(
            'status', 'eligible',
            'reason', 'verified_official_coverage_route'
        )
    ),
    change_reason = 'named_bank_verified_route_hardening_2026_08_26',
    updated_at = now()
FROM verified_routes
WHERE catalog.country_code = 'CA'
  AND catalog.bank_code = verified_routes.bank_code
  AND catalog.product_type = verified_routes.product_type;

-- Official product inventories do not support repeatedly collecting these
-- exact scopes. This is an eligibility exclusion, not an assertion that a
-- previously offered product was formally retired.
WITH excluded_scopes(bank_code, product_type, exclusion_reason) AS (
    VALUES
        ('FNBC', 'credit-card', 'no_verified_direct_official_product_route'),
        ('HAVENTREE', 'credit-card', 'no_verified_direct_official_product_route'),
        ('HAVENTREE', 'line-of-credit', 'no_verified_direct_official_product_route'),
        ('HAVENTREE', 'personal-loan', 'no_verified_direct_official_product_route'),
        ('HOMEEQUITY', 'chequing', 'no_verified_direct_official_product_route'),
        ('HOMEEQUITY', 'credit-card', 'no_verified_direct_official_product_route'),
        ('HOMEEQUITY', 'line-of-credit', 'no_verified_direct_official_product_route'),
        ('HOMEEQUITY', 'personal-loan', 'no_verified_direct_official_product_route'),
        ('HOMEEQUITY', 'savings', 'no_verified_direct_official_product_route')
)
UPDATE source_registry_catalog_item AS catalog
SET
    status = 'inactive',
    coverage_source_url = NULL,
    normalized_coverage_source_url = NULL,
    coverage_source_metadata = jsonb_build_object(
        'verification_status', 'needs_coverage_review',
        'verification_method', 'official_site_and_repeated_zero_detail_run_audit',
        'verification_scope', 'directly_collectable_current_product_route',
        'scope_outcome', 'excluded_from_collection',
        'exclusion_reason', excluded_scopes.exclusion_reason,
        'not_currently_offered_asserted', false,
        'verified_at', '2026-08-26T00:00:00-07:00',
        'collection_eligibility', jsonb_build_object(
            'status', 'quarantined',
            'reason', 'structural_zero_detail_collection_result',
            'reactivation_requirement', 'verified_coverage_route_or_active_detail_source'
        )
    ),
    change_reason = 'named_bank_structural_scope_quarantined_2026_08_26:' || excluded_scopes.exclusion_reason,
    updated_at = now()
FROM excluded_scopes
WHERE catalog.country_code = 'CA'
  AND catalog.bank_code = excluded_scopes.bank_code
  AND catalog.product_type = excluded_scopes.product_type;

-- Migration 0020 cross-joined every recognized Canadian bank with every
-- active Product Type. Quarantine every still-unverified blanket row unless
-- persisted evidence now proves a real collection route. This also makes a
-- fresh migration replay fail closed instead of recreating broad active
-- coverage with no evidence.
UPDATE source_registry_catalog_item AS catalog
SET
    status = 'inactive',
    coverage_source_metadata = COALESCE(catalog.coverage_source_metadata, '{}'::jsonb)
        || jsonb_build_object(
            'verification_status', 'needs_coverage_review',
            'verification_method', 'generic_legacy_blanket_coverage_audit',
            'verification_scope', 'directly_collectable_current_product_route',
            'scope_outcome', 'excluded_from_collection',
            'not_currently_offered_asserted', false,
            'collection_eligibility', jsonb_build_object(
                'status', 'quarantined',
                'reason', 'legacy_blanket_coverage_without_collection_evidence',
                'reactivation_requirement', 'verified_coverage_route_or_active_detail_source'
            )
        ),
    change_reason = 'legacy_blanket_coverage_quarantined_without_evidence_2026_08_26',
    updated_at = now()
WHERE catalog.status = 'active'
  AND catalog.change_reason = 'Canada recognized bank full active Product Type coverage baseline'
  AND catalog.coverage_source_url IS NULL
  AND NOT EXISTS (
      SELECT 1
      FROM source_registry_item AS active_detail
      WHERE active_detail.bank_code = catalog.bank_code
        AND active_detail.country_code = catalog.country_code
        AND active_detail.product_type = catalog.product_type
        AND active_detail.status = 'active'
        AND active_detail.discovery_role = 'detail'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM ingestion_run AS successful_run
      WHERE successful_run.run_state = 'completed'
        AND successful_run.partial_completion_flag = false
        AND successful_run.source_scope_count > 0
        AND successful_run.source_success_count > 0
        AND COALESCE(successful_run.run_metadata ->> 'country_code', successful_run.country_code) = catalog.country_code
        AND COALESCE(successful_run.run_metadata ->> 'bank_code', '') = catalog.bank_code
        AND COALESCE(successful_run.run_metadata ->> 'product_type', '') = catalog.product_type
  );

-- Preserve history while keeping any source-only scheduler path aligned with
-- the quarantined catalog eligibility state.
UPDATE source_registry_item AS source
SET
    status = 'inactive',
    change_reason = 'catalog_scope_quarantined_by_generic_coverage_gate_2026_08_26',
    updated_at = now()
FROM source_registry_catalog_item AS catalog
WHERE catalog.bank_code = source.bank_code
  AND catalog.country_code = source.country_code
  AND catalog.product_type = source.product_type
  AND catalog.status = 'inactive'
  AND catalog.coverage_source_metadata #>> '{collection_eligibility,status}' = 'quarantined'
  AND source.status = 'active';

INSERT INTO migration_history (migration_name)
VALUES ('0043_generic_zero_detail_scope_quarantine.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
