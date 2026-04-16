BEGIN;

ALTER TABLE bank
    ADD COLUMN IF NOT EXISTS homepage_url text,
    ADD COLUMN IF NOT EXISTS normalized_homepage_url text,
    ADD COLUMN IF NOT EXISTS source_language text NOT NULL DEFAULT 'en',
    ADD COLUMN IF NOT EXISTS managed_flag boolean NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS change_reason text;

CREATE UNIQUE INDEX IF NOT EXISTS idx_bank_normalized_homepage_url_unique
    ON bank (normalized_homepage_url)
    WHERE normalized_homepage_url IS NOT NULL;

CREATE TABLE IF NOT EXISTS source_registry_catalog_item (
    catalog_item_id text PRIMARY KEY,
    bank_code text NOT NULL REFERENCES bank(bank_code),
    country_code text NOT NULL,
    product_type text NOT NULL,
    status text NOT NULL CHECK (status IN ('active', 'inactive')),
    change_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bank_code, country_code, product_type)
);

CREATE INDEX IF NOT EXISTS idx_source_registry_catalog_item_scope
    ON source_registry_catalog_item (bank_code, country_code, product_type, status, updated_at DESC);

INSERT INTO migration_history (migration_name)
VALUES ('0006_bank_catalog_management.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
