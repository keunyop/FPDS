BEGIN;

CREATE TABLE IF NOT EXISTS country_registry (
    country_code text PRIMARY KEY CHECK (country_code ~ '^[A-Z]{2}$'),
    status text NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    display_order integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO country_registry (country_code, status, display_order)
VALUES ('CA', 'active', 10)
ON CONFLICT (country_code) DO NOTHING;

INSERT INTO country_registry (country_code, status, display_order)
SELECT DISTINCT upper(country_code), 'active', 100
FROM bank
WHERE country_code ~* '^[a-z]{2}$'
ON CONFLICT (country_code) DO NOTHING;

ALTER TABLE admin_auth_session
    ADD COLUMN IF NOT EXISTS country_code text;

UPDATE admin_auth_session
SET country_code = 'CA'
WHERE country_code IS NULL;

ALTER TABLE admin_auth_session
    ALTER COLUMN country_code SET NOT NULL;

ALTER TABLE admin_auth_session
    DROP CONSTRAINT IF EXISTS admin_auth_session_country_code_fkey;

ALTER TABLE admin_auth_session
    ADD CONSTRAINT admin_auth_session_country_code_fkey
    FOREIGN KEY (country_code) REFERENCES country_registry(country_code);

CREATE INDEX IF NOT EXISTS idx_admin_auth_session_country_status
    ON admin_auth_session (country_code, session_status, absolute_expires_at DESC);

ALTER TABLE ingestion_run
    ADD COLUMN IF NOT EXISTS country_code text;

UPDATE ingestion_run
SET country_code = upper(COALESCE(NULLIF(run_metadata ->> 'country_code', ''), 'CA'))
WHERE country_code IS NULL;

ALTER TABLE ingestion_run
    ALTER COLUMN country_code SET NOT NULL;

ALTER TABLE ingestion_run
    DROP CONSTRAINT IF EXISTS ingestion_run_country_code_fkey;

ALTER TABLE ingestion_run
    ADD CONSTRAINT ingestion_run_country_code_fkey
    FOREIGN KEY (country_code) REFERENCES country_registry(country_code);

CREATE INDEX IF NOT EXISTS idx_ingestion_run_country_started_at
    ON ingestion_run (country_code, started_at DESC);

ALTER TABLE bank
    ADD CONSTRAINT bank_country_code_bank_code_key
    UNIQUE (country_code, bank_code);

ALTER TABLE bank
    DROP CONSTRAINT IF EXISTS bank_country_code_fkey;
ALTER TABLE bank
    ADD CONSTRAINT bank_country_code_fkey
    FOREIGN KEY (country_code) REFERENCES country_registry(country_code);

ALTER TABLE source_document
    DROP CONSTRAINT IF EXISTS source_document_country_bank_fkey;
ALTER TABLE source_document
    ADD CONSTRAINT source_document_country_bank_fkey
    FOREIGN KEY (country_code, bank_code) REFERENCES bank(country_code, bank_code);

ALTER TABLE normalized_candidate
    DROP CONSTRAINT IF EXISTS normalized_candidate_country_bank_fkey;
ALTER TABLE normalized_candidate
    ADD CONSTRAINT normalized_candidate_country_bank_fkey
    FOREIGN KEY (country_code, bank_code) REFERENCES bank(country_code, bank_code);

ALTER TABLE canonical_product
    DROP CONSTRAINT IF EXISTS canonical_product_country_bank_fkey;
ALTER TABLE canonical_product
    ADD CONSTRAINT canonical_product_country_bank_fkey
    FOREIGN KEY (country_code, bank_code) REFERENCES bank(country_code, bank_code);

ALTER TABLE source_registry_item
    DROP CONSTRAINT IF EXISTS source_registry_item_country_bank_fkey;
ALTER TABLE source_registry_item
    ADD CONSTRAINT source_registry_item_country_bank_fkey
    FOREIGN KEY (country_code, bank_code) REFERENCES bank(country_code, bank_code);

ALTER TABLE source_registry_catalog_item
    DROP CONSTRAINT IF EXISTS source_registry_catalog_item_country_bank_fkey;
ALTER TABLE source_registry_catalog_item
    ADD CONSTRAINT source_registry_catalog_item_country_bank_fkey
    FOREIGN KEY (country_code, bank_code) REFERENCES bank(country_code, bank_code);

ALTER TABLE public_product_projection
    DROP CONSTRAINT IF EXISTS public_product_projection_country_bank_fkey;
ALTER TABLE public_product_projection
    ADD CONSTRAINT public_product_projection_country_bank_fkey
    FOREIGN KEY (country_code, bank_code) REFERENCES bank(country_code, bank_code);

ALTER TABLE source_document
    DROP CONSTRAINT IF EXISTS source_document_bank_code_normalized_source_url_source_type_key;
ALTER TABLE source_document
    ADD CONSTRAINT source_document_country_bank_url_type_key
    UNIQUE (country_code, bank_code, normalized_source_url, source_type);

ALTER TABLE source_registry_item
    DROP CONSTRAINT IF EXISTS source_registry_item_bank_code_product_type_normalized_url_source_type_key;
ALTER TABLE source_registry_item
    ADD CONSTRAINT source_registry_item_country_bank_product_url_type_key
    UNIQUE (country_code, bank_code, product_type, normalized_url, source_type);

UPDATE source_registry_item
SET
    product_key = upper(country_code) || ':' || upper(bank_code) || ':' || lower(product_type),
    updated_at = now()
WHERE product_key IS DISTINCT FROM upper(country_code) || ':' || upper(bank_code) || ':' || lower(product_type);

CREATE INDEX IF NOT EXISTS idx_normalized_candidate_country_identity
    ON normalized_candidate (
        country_code,
        bank_code,
        product_family,
        product_type,
        subtype_code,
        lower(product_name),
        updated_at DESC
    );

CREATE INDEX IF NOT EXISTS idx_canonical_product_country_identity
    ON canonical_product (
        country_code,
        bank_code,
        product_family,
        product_type,
        subtype_code,
        lower(product_name),
        status,
        updated_at DESC
    );

INSERT INTO migration_history (migration_name)
VALUES ('0025_country_scoped_admin.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
