BEGIN;

WITH lending_product_type_seed(
    product_type_code,
    display_name,
    description,
    discovery_keywords,
    expected_fields
) AS (
    VALUES
        (
            'credit-card',
            'Credit Card',
            'Canadian retail credit cards, including rewards, cash back, low-interest, no-fee, student, newcomer, travel, and business-card variants when banks publish them in the same retail credit-card family.',
            '["credit cards", "cash back", "rewards", "annual fee", "purchase interest rate", "balance transfer", "travel rewards", "low interest credit card", "no fee credit card", "student credit card"]'::jsonb,
            '["product_name", "description_short", "annual_fee", "purchase_interest_rate", "cash_advance_rate", "balance_transfer_rate", "rewards_summary", "eligibility_text", "application_method", "credit_limit_text", "notes"]'::jsonb
        ),
        (
            'mortgage',
            'Mortgage',
            'Canadian residential mortgage products, including fixed-rate, variable-rate, refinance, renewal, switch, and home-equity-adjacent mortgage products when treated as mortgage products by the bank.',
            '["mortgages", "mortgage rates", "fixed rate mortgage", "variable rate mortgage", "amortization", "prepayment privileges", "mortgage renewal", "mortgage refinance", "home equity"]'::jsonb,
            '["product_name", "description_short", "mortgage_rate", "rate_type", "term_length_text", "amortization_text", "payment_frequency", "prepayment_privileges", "eligibility_text", "application_method", "notes"]'::jsonb
        ),
        (
            'personal-loan',
            'Personal Loan',
            'Canadian personal loan products, including unsecured loans, car or vehicle loans, RRSP loans, home improvement loans, and other installment-loan variants.',
            '["personal loans", "loan rates", "fixed rate loan", "vehicle loan", "car loan", "rrsp loan", "monthly payments", "installment loan", "borrow money"]'::jsonb,
            '["product_name", "description_short", "interest_rate", "loan_amount_text", "term_length_text", "monthly_payment_text", "security_requirement", "eligibility_text", "application_method", "fees_text", "notes"]'::jsonb
        ),
        (
            'line-of-credit',
            'Line of Credit',
            'Canadian personal lines of credit, including unsecured, student, professional student, and home-equity lines of credit.',
            '["lines of credit", "line of credit", "home equity line of credit", "student line of credit", "personal line of credit", "credit limit", "variable interest rate", "minimum payment"]'::jsonb,
            '["product_name", "description_short", "interest_rate", "credit_limit_text", "secured_flag", "collateral_text", "minimum_payment_text", "eligibility_text", "application_method", "fees_text", "notes"]'::jsonb
        )
)
INSERT INTO product_type_registry (
    product_type_code,
    product_family,
    display_name,
    description,
    status,
    managed_flag,
    discovery_keywords,
    expected_fields,
    fallback_policy,
    created_at,
    updated_at
)
SELECT
    product_type_code,
    'lending',
    display_name,
    description,
    'active',
    true,
    discovery_keywords,
    expected_fields,
    'generic_ai_review',
    now(),
    now()
FROM lending_product_type_seed
ON CONFLICT (product_type_code) DO UPDATE SET
    product_family = 'lending',
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    status = 'active',
    managed_flag = true,
    discovery_keywords = EXCLUDED.discovery_keywords,
    expected_fields = EXCLUDED.expected_fields,
    fallback_policy = 'generic_ai_review',
    updated_at = now();

DELETE FROM taxonomy_registry
WHERE country_code = 'CA'
  AND product_family <> 'lending'
  AND product_type IN ('credit-card', 'mortgage', 'personal-loan', 'line-of-credit');

WITH taxonomy_seed(product_type, subtype_code, display_order, notes) AS (
    VALUES
        ('credit-card', 'other', 999, 'Canada lending taxonomy v1 generic fallback'),
        ('mortgage', 'other', 999, 'Canada lending taxonomy v1 generic fallback'),
        ('personal-loan', 'other', 999, 'Canada lending taxonomy v1 generic fallback'),
        ('line-of-credit', 'other', 999, 'Canada lending taxonomy v1 generic fallback')
)
INSERT INTO taxonomy_registry (
    taxonomy_id,
    country_code,
    product_family,
    product_type,
    subtype_code,
    display_order,
    active_flag,
    notes,
    created_at,
    updated_at
)
SELECT
    'tax-ca-lending-' || taxonomy_seed.product_type || '-' || replace(taxonomy_seed.subtype_code, '_', '-'),
    'CA',
    'lending',
    taxonomy_seed.product_type,
    taxonomy_seed.subtype_code,
    taxonomy_seed.display_order,
    product_type_registry.status = 'active',
    taxonomy_seed.notes,
    now(),
    now()
FROM taxonomy_seed
JOIN product_type_registry
  ON product_type_registry.product_family = 'lending'
 AND product_type_registry.product_type_code = taxonomy_seed.product_type
ON CONFLICT (country_code, product_family, product_type, subtype_code) DO UPDATE SET
    display_order = EXCLUDED.display_order,
    active_flag = EXCLUDED.active_flag,
    notes = EXCLUDED.notes,
    updated_at = EXCLUDED.updated_at;

INSERT INTO migration_history (migration_name)
VALUES ('0019_canada_lending_product_types.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
