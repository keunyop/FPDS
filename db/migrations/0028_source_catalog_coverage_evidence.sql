BEGIN;

ALTER TABLE source_registry_catalog_item
    ADD COLUMN IF NOT EXISTS coverage_source_url text,
    ADD COLUMN IF NOT EXISTS normalized_coverage_source_url text;

ALTER TABLE source_registry_catalog_item
    DROP CONSTRAINT IF EXISTS source_registry_catalog_item_coverage_source_https_check;

ALTER TABLE source_registry_catalog_item
    ADD CONSTRAINT source_registry_catalog_item_coverage_source_https_check
    CHECK (
        coverage_source_url IS NULL
        OR coverage_source_url ~* '^https://'
    );

CREATE INDEX IF NOT EXISTS idx_source_registry_catalog_item_coverage_source
    ON source_registry_catalog_item (normalized_coverage_source_url)
    WHERE normalized_coverage_source_url IS NOT NULL;

INSERT INTO migration_history (migration_name)
VALUES ('0028_source_catalog_coverage_evidence.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
