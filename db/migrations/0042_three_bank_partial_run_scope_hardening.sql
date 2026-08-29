BEGIN;

-- Migration 0020 intentionally bootstrapped every recognized Canadian bank
-- against every active Product Type. That broad onboarding baseline is not
-- evidence that each bank currently exposes a directly collectable retail
-- product. Pin the verified current routes for the three audited banks.
WITH verified_routes(
    bank_code,
    product_type,
    coverage_source_url,
    homepage_domain,
    current_offering_summary,
    relationship_summary
) AS (
    VALUES
        (
            'BRIDGEWATER',
            'gic',
            'https://bridgewaterbank.ca/investments/gic-accounts/',
            'bridgewaterbank.ca',
            'Bridgewater publishes current GIC accounts and rate features on its official retail site.',
            'Direct Bridgewater Bank retail product.'
        ),
        (
            'BRIDGEWATER',
            'mortgage',
            'https://bridgewaterbank.ca/mortgages/my-mortgage-solution/',
            'bridgewaterbank.ca',
            'Bridgewater publishes current residential mortgage solutions on its official retail site.',
            'Direct Bridgewater Bank retail product.'
        ),
        (
            'BRIDGEWATER',
            'savings',
            'https://bridgewaterbank.ca/savings/my-savings-acccount/',
            'bridgewaterbank.ca',
            'Bridgewater publishes its current Smart eSavings account on its official retail site.',
            'Direct Bridgewater Bank retail product.'
        ),
        (
            'EQBANK',
            'chequing',
            'https://www.eqbank.ca/personal-banking/personal-account',
            'eqbank.ca',
            'EQ Bank describes Personal Account as acting like chequing for everyday transactions.',
            'Direct EQ Bank retail product.'
        ),
        (
            'EQBANK',
            'gic',
            'https://www.eqbank.ca/personal-banking/gics',
            'eqbank.ca',
            'EQ Bank publishes current GIC products and terms on its official retail site.',
            'Direct EQ Bank retail product.'
        ),
        (
            'EQBANK',
            'line-of-credit',
            'https://www.eqbank.ca/residential/heloc',
            'eqbank.ca',
            'EQ Bank publishes a current home equity line of credit route.',
            'Direct EQ Bank retail product.'
        ),
        (
            'EQBANK',
            'mortgage',
            'https://www.eqbank.ca/reverse-mortgage',
            'eqbank.ca',
            'EQ Bank publishes a current reverse mortgage product route.',
            'Direct EQ Bank retail product.'
        ),
        (
            'EQBANK',
            'savings',
            'https://www.eqbank.ca/personal-banking/notice-savings-account',
            'eqbank.ca',
            'EQ Bank publishes current Notice Savings Account products on its official retail site.',
            'Direct EQ Bank retail product.'
        ),
        (
            'FAIRSTONE',
            'mortgage',
            'https://www.fairstone.ca/en/home-equity-loans/second-mortgage',
            'fairstone.ca',
            'Fairstone publishes current second-mortgage and mortgage-refinancing routes.',
            'Fairstone Financial Inc. is the operating subsidiary of Fairstone Bank of Canada for this retail product.'
        ),
        (
            'FAIRSTONE',
            'personal-loan',
            'https://www.fairstone.ca/en/loans/personal-loans',
            'fairstone.ca',
            'Fairstone publishes current secured and unsecured personal loans.',
            'Fairstone Financial Inc. is the operating subsidiary of Fairstone Bank of Canada for this retail product.'
        )
)
UPDATE source_registry_catalog_item AS catalog
SET
    status = 'active',
    coverage_source_url = verified_routes.coverage_source_url,
    normalized_coverage_source_url = verified_routes.coverage_source_url,
    coverage_source_metadata = jsonb_build_object(
        'verification_status', 'verified',
        'verification_method', 'official_site_route_and_run_evidence_audit',
        'verification_scope', 'current_retail_product_detail_or_hub',
        'homepage_domain', verified_routes.homepage_domain,
        'coverage_domain', verified_routes.homepage_domain,
        'current_offering_summary', verified_routes.current_offering_summary,
        'relationship_summary', verified_routes.relationship_summary,
        'verified_at', '2026-08-26T00:00:00-07:00'
    ),
    change_reason = 'three_bank_verified_product_route_hardening_2026_08_26',
    updated_at = now()
FROM verified_routes
WHERE catalog.country_code = 'CA'
  AND catalog.bank_code = verified_routes.bank_code
  AND catalog.product_type = verified_routes.product_type;

-- These exact scopes repeatedly produced zero-detail partial runs because the
-- blanket bank x Product Type bootstrap was wider than current directly
-- collectable official retail coverage. Group-level subsidiary disclosures
-- are not enough to attribute a product to this bank/brand catalog row.
WITH excluded_scopes(bank_code, product_type, exclusion_reason) AS (
    VALUES
        ('BRIDGEWATER', 'chequing', 'no_direct_collectible_offering'),
        ('BRIDGEWATER', 'credit-card', 'no_direct_collectible_offering'),
        ('BRIDGEWATER', 'line-of-credit', 'no_direct_collectible_offering'),
        ('BRIDGEWATER', 'personal-loan', 'no_direct_collectible_offering'),
        ('EQBANK', 'credit-card', 'prepaid_card_not_credit_card'),
        ('EQBANK', 'personal-loan', 'no_direct_collectible_offering'),
        ('FAIRSTONE', 'chequing', 'no_direct_collectible_offering'),
        ('FAIRSTONE', 'credit-card', 'group_only_without_attributable_detail_route'),
        ('FAIRSTONE', 'gic', 'group_only_without_attributable_detail_route'),
        ('FAIRSTONE', 'line-of-credit', 'no_direct_collectible_offering'),
        ('FAIRSTONE', 'savings', 'group_only_without_attributable_detail_route')
)
UPDATE source_registry_catalog_item AS catalog
SET
    status = 'inactive',
    coverage_source_url = NULL,
    normalized_coverage_source_url = NULL,
    coverage_source_metadata = jsonb_build_object(
        'verification_status', 'excluded',
        'verification_method', 'official_site_route_and_repeated_run_evidence_audit',
        'verification_scope', 'directly_collectable_current_retail_product',
        'scope_outcome', 'excluded_from_collection',
        'exclusion_reason', excluded_scopes.exclusion_reason,
        'verified_at', '2026-08-26T00:00:00-07:00'
    ),
    change_reason = 'three_bank_partial_run_scope_excluded_2026_08_26:' || excluded_scopes.exclusion_reason,
    updated_at = now()
FROM excluded_scopes
WHERE catalog.country_code = 'CA'
  AND catalog.bank_code = excluded_scopes.bank_code
  AND catalog.product_type = excluded_scopes.product_type;

-- Keep historical source rows, but stop any older generated/supporting rows in
-- the excluded scopes from entering operator-initiated source collection.
WITH excluded_scopes(bank_code, product_type, exclusion_reason) AS (
    VALUES
        ('BRIDGEWATER', 'chequing', 'no_direct_collectible_offering'),
        ('BRIDGEWATER', 'credit-card', 'no_direct_collectible_offering'),
        ('BRIDGEWATER', 'line-of-credit', 'no_direct_collectible_offering'),
        ('BRIDGEWATER', 'personal-loan', 'no_direct_collectible_offering'),
        ('EQBANK', 'credit-card', 'prepaid_card_not_credit_card'),
        ('EQBANK', 'personal-loan', 'no_direct_collectible_offering'),
        ('FAIRSTONE', 'chequing', 'no_direct_collectible_offering'),
        ('FAIRSTONE', 'credit-card', 'group_only_without_attributable_detail_route'),
        ('FAIRSTONE', 'gic', 'group_only_without_attributable_detail_route'),
        ('FAIRSTONE', 'line-of-credit', 'no_direct_collectible_offering'),
        ('FAIRSTONE', 'savings', 'group_only_without_attributable_detail_route')
)
UPDATE source_registry_item AS source
SET
    status = 'inactive',
    change_reason = 'catalog_scope_excluded_2026_08_26:' || excluded_scopes.exclusion_reason,
    updated_at = now()
FROM excluded_scopes
WHERE source.country_code = 'CA'
  AND source.bank_code = excluded_scopes.bank_code
  AND source.product_type = excluded_scopes.product_type
  AND source.status = 'active';

INSERT INTO migration_history (migration_name)
VALUES ('0042_three_bank_partial_run_scope_hardening.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
