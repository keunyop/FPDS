BEGIN;

CREATE TABLE IF NOT EXISTS product_type_registry (
    product_type_code text PRIMARY KEY,
    product_family text NOT NULL DEFAULT 'deposit',
    display_name text NOT NULL,
    description text NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'inactive')),
    managed_flag boolean NOT NULL DEFAULT true,
    discovery_keywords jsonb NOT NULL DEFAULT '[]'::jsonb,
    expected_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
    fallback_policy text NOT NULL DEFAULT 'generic_ai_review',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_type_registry_lookup
    ON product_type_registry (product_family, status, display_name);

INSERT INTO migration_history (migration_name)
VALUES ('0007_dynamic_product_type_onboarding.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
