BEGIN;

ALTER TABLE bank
    ADD COLUMN IF NOT EXISTS logo_url text,
    ADD COLUMN IF NOT EXISTS logo_alt_text text;

INSERT INTO bank (
    bank_code,
    country_code,
    bank_name,
    status,
    homepage_url,
    normalized_homepage_url,
    logo_url,
    logo_alt_text,
    source_language,
    managed_flag,
    change_reason,
    created_at,
    updated_at
)
VALUES (
    'VANCITY',
    'CA',
    'Vancity',
    'active',
    'https://www.vancity.com/',
    'https://www.vancity.com/',
    'https://www.vancity.com/favicon.ico',
    'Vancity logo',
    'en',
    true,
    'Product Owner requested Vancity onboarding',
    now(),
    now()
)
ON CONFLICT (bank_code) DO UPDATE SET
    country_code = 'CA',
    bank_name = EXCLUDED.bank_name,
    status = 'active',
    homepage_url = EXCLUDED.homepage_url,
    normalized_homepage_url = EXCLUDED.normalized_homepage_url,
    logo_url = EXCLUDED.logo_url,
    logo_alt_text = EXCLUDED.logo_alt_text,
    source_language = EXCLUDED.source_language,
    managed_flag = true,
    change_reason = EXCLUDED.change_reason,
    updated_at = now();

WITH vancity_product_scope AS (
    SELECT
        bank.bank_code,
        bank.country_code,
        product_type_registry.product_type_code AS product_type
    FROM bank
    CROSS JOIN product_type_registry
    WHERE bank.bank_code = 'VANCITY'
      AND bank.country_code = 'CA'
      AND bank.status = 'active'
      AND product_type_registry.status = 'active'
)
INSERT INTO source_registry_catalog_item (
    catalog_item_id,
    bank_code,
    country_code,
    product_type,
    status,
    change_reason,
    created_at,
    updated_at
)
SELECT
    'catalog-' || lower(vancity_product_scope.country_code) || '-' || lower(vancity_product_scope.bank_code) || '-' || vancity_product_scope.product_type,
    vancity_product_scope.bank_code,
    vancity_product_scope.country_code,
    vancity_product_scope.product_type,
    'active',
    'Product Owner requested Vancity full active Product Type coverage',
    now(),
    now()
FROM vancity_product_scope
ON CONFLICT (bank_code, country_code, product_type) DO UPDATE SET
    status = 'active',
    change_reason = EXCLUDED.change_reason,
    updated_at = now();

INSERT INTO migration_history (migration_name)
VALUES ('0021_vancity_credit_union_full_coverage.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
