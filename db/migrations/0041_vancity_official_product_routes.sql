BEGIN;

-- The generic coverage resolver previously assigned some Vancity catalog
-- rows to a sibling product-family route (notably Credit Card -> Loans and
-- Lines of Credit). Pin each active Product Type to the official audited hub;
-- the curated source registry expands these hubs into exact product details.
WITH official_routes (product_type, coverage_source_url) AS (
    VALUES
        ('chequing', 'https://www.vancity.com/bank/accounts'),
        ('savings', 'https://www.vancity.com/bank/accounts'),
        ('gic', 'https://www.vancity.com/invest/term-deposit-gic'),
        ('credit-card', 'https://www.vancity.com/bank/credit-cards'),
        ('mortgage', 'https://www.vancity.com/borrow/mortgages'),
        ('personal-loan', 'https://www.vancity.com/borrow/loans-lines-of-credit'),
        ('line-of-credit', 'https://www.vancity.com/borrow/loans-lines-of-credit')
)
UPDATE source_registry_catalog_item AS catalog
SET
    status = 'active',
    coverage_source_url = official_routes.coverage_source_url,
    normalized_coverage_source_url = official_routes.coverage_source_url,
    coverage_source_metadata = jsonb_build_object(
        'verification_status', 'verified',
        'verification_method', 'product_owner_directed_official_site_audit',
        'homepage_domain', 'vancity.com',
        'coverage_domain', 'vancity.com',
        'verification_scope', 'retail_product_type_hub',
        'verified_at', '2026-08-15T00:00:00-07:00'
    ),
    change_reason = 'vancity_official_product_route_audit_2026_08_15',
    updated_at = now()
FROM official_routes
WHERE catalog.bank_code = 'VANCITY'
  AND catalog.country_code = 'CA'
  AND catalog.product_type = official_routes.product_type;

INSERT INTO migration_history (migration_name)
VALUES ('0041_vancity_official_product_routes.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
