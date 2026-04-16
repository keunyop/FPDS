BEGIN;

CREATE TABLE IF NOT EXISTS source_registry_item (
    source_id text PRIMARY KEY,
    bank_code text NOT NULL REFERENCES bank(bank_code),
    country_code text NOT NULL,
    product_type text NOT NULL,
    product_key text,
    source_name text NOT NULL,
    source_url text NOT NULL,
    normalized_url text NOT NULL,
    source_type text NOT NULL CHECK (source_type IN ('html', 'pdf')),
    discovery_role text NOT NULL CHECK (discovery_role IN ('entry', 'detail', 'supporting_html', 'supporting_pdf', 'linked_pdf')),
    status text NOT NULL CHECK (status IN ('active', 'inactive', 'deprecated', 'removed')),
    priority text NOT NULL DEFAULT 'P1',
    source_language text NOT NULL DEFAULT 'en',
    purpose text NOT NULL DEFAULT '',
    expected_fields jsonb NOT NULL DEFAULT '[]'::jsonb,
    seed_source_flag boolean NOT NULL DEFAULT false,
    last_verified_at timestamptz,
    last_seen_at timestamptz,
    redirect_target_url text,
    alias_urls jsonb NOT NULL DEFAULT '[]'::jsonb,
    change_reason text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (bank_code, product_type, normalized_url, source_type)
);

CREATE INDEX IF NOT EXISTS idx_source_registry_item_scope
    ON source_registry_item (bank_code, country_code, product_type, status, discovery_role, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_source_registry_item_normalized_url
    ON source_registry_item (normalized_url);

INSERT INTO migration_history (migration_name)
VALUES ('0004_source_registry_admin.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
