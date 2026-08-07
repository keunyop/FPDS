BEGIN;

ALTER TABLE source_registry_catalog_item
    ADD COLUMN IF NOT EXISTS coverage_source_metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE source_registry_catalog_item
    DROP CONSTRAINT IF EXISTS source_registry_catalog_item_coverage_source_metadata_object_check;

ALTER TABLE source_registry_catalog_item
    ADD CONSTRAINT source_registry_catalog_item_coverage_source_metadata_object_check
    CHECK (jsonb_typeof(coverage_source_metadata) = 'object');

INSERT INTO migration_history (migration_name)
VALUES ('0031_catalog_coverage_route_evidence.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
