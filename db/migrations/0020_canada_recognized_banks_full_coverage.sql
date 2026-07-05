BEGIN;

ALTER TABLE bank
    ADD COLUMN IF NOT EXISTS logo_url text,
    ADD COLUMN IF NOT EXISTS logo_alt_text text;

WITH recognized_bank_seed(
    bank_code,
    bank_name,
    homepage_url,
    normalized_homepage_url,
    logo_url,
    logo_alt_text,
    change_reason
) AS (
    VALUES
        ('RBC', 'Royal Bank of Canada', 'https://www.rbcroyalbank.com/', 'https://www.rbcroyalbank.com/', 'https://www.rbcroyalbank.com/favicon.ico', 'Royal Bank of Canada logo', 'Canada recognized bank logo and coverage baseline'),
        ('TD', 'TD Bank', 'https://www.td.com/ca/en/personal-banking/', 'https://www.td.com/ca/en/personal-banking/', 'https://www.td.com/favicon.ico', 'TD Bank logo', 'Canada recognized bank logo and coverage baseline'),
        ('BMO', 'BMO', 'https://www.bmo.com/main/personal', 'https://www.bmo.com/main/personal', 'https://www.bmo.com/favicon.ico', 'BMO logo', 'Canada recognized bank logo and coverage baseline'),
        ('SCOTIA', 'Scotiabank', 'https://www.scotiabank.com/ca/en/personal.html', 'https://www.scotiabank.com/ca/en/personal.html', 'https://www.scotiabank.com/favicon.ico', 'Scotiabank logo', 'Canada recognized bank logo and coverage baseline'),
        ('CIBC', 'CIBC', 'https://www.cibc.com/en/personal-banking.html', 'https://www.cibc.com/en/personal-banking.html', 'https://www.cibc.com/favicon.ico', 'CIBC logo', 'Canada recognized bank logo and coverage baseline'),
        ('NATIONAL', 'National Bank of Canada', 'https://www.nbc.ca/', 'https://www.nbc.ca/', 'https://www.nbc.ca/favicon.ico', 'National Bank of Canada logo', 'Canada recognized bank onboarding'),
        ('LAURENTIAN', 'Laurentian Bank of Canada', 'https://www.laurentianbank.ca/', 'https://www.laurentianbank.ca/', 'https://www.laurentianbank.ca/favicon.ico', 'Laurentian Bank of Canada logo', 'Canada recognized bank onboarding'),
        ('TANGERINE', 'Tangerine Bank', 'https://www.tangerine.ca/en/personal', 'https://www.tangerine.ca/en/personal', 'https://www.tangerine.ca/favicon.ico', 'Tangerine Bank logo', 'Canada recognized bank onboarding'),
        ('SIMPLII', 'Simplii Financial', 'https://www.simplii.com/en/home.html', 'https://www.simplii.com/en/home.html', 'https://www.simplii.com/favicon.ico', 'Simplii Financial logo', 'Canada recognized bank onboarding'),
        ('EQBANK', 'EQ Bank (Equitable Bank)', 'https://www.eqbank.ca/', 'https://www.eqbank.ca/', 'https://www.eqbank.ca/favicon.ico', 'EQ Bank logo', 'Canada recognized bank onboarding'),
        ('MANULIFE', 'Manulife Bank of Canada', 'https://www.manulifebank.ca/personal-banking.html', 'https://www.manulifebank.ca/personal-banking.html', 'https://www.manulifebank.ca/favicon.ico', 'Manulife Bank of Canada logo', 'Canada recognized bank onboarding'),
        ('ALTERNA', 'Alterna Bank', 'https://www.alternabank.ca/en/personal', 'https://www.alternabank.ca/en/personal', 'https://www.alternabank.ca/favicon.ico', 'Alterna Bank logo', 'Canada recognized bank onboarding'),
        ('MOTUS', 'motusbank', 'https://www.motusbank.ca/', 'https://www.motusbank.ca/', 'https://www.motusbank.ca/favicon.ico', 'motusbank logo', 'Canada recognized bank onboarding'),
        ('CTBANK', 'Canadian Tire Bank', 'https://www.ctfs.com/content/ctfs/en.html', 'https://www.ctfs.com/content/ctfs/en.html', 'https://www.ctfs.com/favicon.ico', 'Canadian Tire Bank logo', 'Canada recognized bank onboarding'),
        ('PCFIN', 'PC Financial (President''s Choice Bank)', 'https://www.pcfinancial.ca/en/', 'https://www.pcfinancial.ca/en/', 'https://www.pcfinancial.ca/favicon.ico', 'PC Financial logo', 'Canada recognized bank onboarding'),
        ('ROGERSBANK', 'Rogers Bank', 'https://www.rogersbank.com/', 'https://www.rogersbank.com/', 'https://www.rogersbank.com/favicon.ico', 'Rogers Bank logo', 'Canada recognized bank onboarding'),
        ('FNBC', 'First Nations Bank of Canada', 'https://www.fnbc.ca/', 'https://www.fnbc.ca/', 'https://www.fnbc.ca/favicon.ico', 'First Nations Bank of Canada logo', 'Canada recognized bank onboarding'),
        ('OAKEN', 'Oaken Financial (Home Bank)', 'https://www.oaken.com/', 'https://www.oaken.com/', 'https://www.oaken.com/favicon.ico', 'Oaken Financial logo', 'Canada recognized bank onboarding'),
        ('HOMEEQUITY', 'HomeEquity Bank', 'https://www.homeequitybank.ca/', 'https://www.homeequitybank.ca/', 'https://www.homeequitybank.ca/favicon.ico', 'HomeEquity Bank logo', 'Canada recognized bank onboarding'),
        ('FAIRSTONE', 'Fairstone Bank of Canada', 'https://www.fairstone.ca/', 'https://www.fairstone.ca/', 'https://www.fairstone.ca/favicon.ico', 'Fairstone Bank of Canada logo', 'Canada recognized bank onboarding'),
        ('PEOPLES', 'Peoples Bank of Canada', 'https://www.peoplesbank.ca/', 'https://www.peoplesbank.ca/', 'https://www.peoplesbank.ca/favicon.ico', 'Peoples Bank of Canada logo', 'Canada recognized bank onboarding'),
        ('WEALTHONE', 'Wealth One Bank of Canada', 'https://www.wealthonebankofcanada.com/', 'https://www.wealthonebankofcanada.com/', 'https://www.wealthonebankofcanada.com/favicon.ico', 'Wealth One Bank of Canada logo', 'Canada recognized bank onboarding'),
        ('HAVENTREE', 'Haventree Bank', 'https://www.haventreebank.com/', 'https://www.haventreebank.com/', 'https://www.haventreebank.com/favicon.ico', 'Haventree Bank logo', 'Canada recognized bank onboarding'),
        ('RFA', 'RFA Bank of Canada', 'https://www.rfa.ca/', 'https://www.rfa.ca/', 'https://www.rfa.ca/favicon.ico', 'RFA Bank of Canada logo', 'Canada recognized bank onboarding'),
        ('BRIDGEWATER', 'Bridgewater Bank', 'https://www.bridgewaterbank.ca/', 'https://www.bridgewaterbank.ca/', 'https://www.bridgewaterbank.ca/favicon.ico', 'Bridgewater Bank logo', 'Canada recognized bank onboarding'),
        ('B2B', 'B2B Bank', 'https://b2bbank.com/', 'https://b2bbank.com/', 'https://b2bbank.com/favicon.ico', 'B2B Bank logo', 'Canada recognized bank onboarding'),
        ('VERSABANK', 'VersaBank', 'https://www.versabank.com/', 'https://www.versabank.com/', 'https://www.versabank.com/favicon.ico', 'VersaBank logo', 'Canada recognized bank onboarding')
)
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
SELECT
    bank_code,
    'CA',
    bank_name,
    'active',
    homepage_url,
    normalized_homepage_url,
    logo_url,
    logo_alt_text,
    'en',
    true,
    change_reason,
    now(),
    now()
FROM recognized_bank_seed
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

WITH active_bank_product_scope AS (
    SELECT
        bank.bank_code,
        bank.country_code,
        product_type_registry.product_type_code AS product_type
    FROM bank
    CROSS JOIN product_type_registry
    WHERE bank.country_code = 'CA'
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
    'catalog-' || lower(active_bank_product_scope.country_code) || '-' || lower(active_bank_product_scope.bank_code) || '-' || active_bank_product_scope.product_type,
    active_bank_product_scope.bank_code,
    active_bank_product_scope.country_code,
    active_bank_product_scope.product_type,
    'active',
    'Canada recognized bank full active Product Type coverage baseline',
    now(),
    now()
FROM active_bank_product_scope
ON CONFLICT (bank_code, country_code, product_type) DO UPDATE SET
    status = 'active',
    change_reason = EXCLUDED.change_reason,
    updated_at = now();

INSERT INTO migration_history (migration_name)
VALUES ('0020_canada_recognized_banks_full_coverage.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
