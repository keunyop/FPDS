BEGIN;

CREATE TABLE IF NOT EXISTS product_type_registry (
    product_type_code text PRIMARY KEY,
    product_family text NOT NULL DEFAULT 'deposit',
    display_name text NOT NULL,
    description text NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'inactive')),
    built_in_flag boolean NOT NULL DEFAULT false,
    managed_flag boolean NOT NULL DEFAULT true,
    discovery_keywords jsonb NOT NULL DEFAULT '[]'::jsonb,
    expected_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
    fallback_policy text NOT NULL DEFAULT 'generic_ai_review',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_type_registry_lookup
    ON product_type_registry (product_family, status, built_in_flag, display_name);

INSERT INTO product_type_registry (
    product_type_code,
    product_family,
    display_name,
    description,
    status,
    built_in_flag,
    managed_flag,
    discovery_keywords,
    expected_fields,
    fallback_policy
)
VALUES
    (
        'chequing',
        'deposit',
        'Chequing',
        'Daily transaction account with monthly fee, transaction bundle, debit, and banking-plan benefits.',
        'active',
        true,
        true,
        '["chequing", "checking", "bank account", "banking plan", "daily banking"]'::jsonb,
        '["product_name", "monthly_fee", "included_transactions", "interac_e_transfer_included", "overdraft_available"]'::jsonb,
        'canonical_parser'
    ),
    (
        'savings',
        'deposit',
        'Savings',
        'Savings deposit account focused on interest rate, promotional offer, balance tier, and withdrawal rules.',
        'active',
        true,
        true,
        '["savings", "save", "high interest", "interest"]'::jsonb,
        '["product_name", "standard_rate", "promotional_rate", "monthly_fee", "interest_payment_frequency"]'::jsonb,
        'canonical_parser'
    ),
    (
        'gic',
        'deposit',
        'GIC',
        'Guaranteed investment certificate or term deposit with rate, term, redeemability, and minimum deposit details.',
        'active',
        true,
        true,
        '["gic", "term deposit", "certificate", "investment", "non-redeemable"]'::jsonb,
        '["product_name", "standard_rate", "minimum_deposit", "term_length_text", "redeemable_flag"]'::jsonb,
        'canonical_parser'
    )
ON CONFLICT (product_type_code) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    status = EXCLUDED.status,
    built_in_flag = EXCLUDED.built_in_flag,
    managed_flag = EXCLUDED.managed_flag,
    discovery_keywords = EXCLUDED.discovery_keywords,
    expected_fields = EXCLUDED.expected_fields,
    fallback_policy = EXCLUDED.fallback_policy,
    updated_at = now();

INSERT INTO migration_history (migration_name)
VALUES ('0007_dynamic_product_type_onboarding.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
