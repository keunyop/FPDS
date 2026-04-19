BEGIN;

ALTER TABLE source_registry_item
    ADD COLUMN IF NOT EXISTS discovery_metadata jsonb NOT NULL DEFAULT '{}'::jsonb;

INSERT INTO migration_history (migration_name)
VALUES ('0008_discovery_metadata_persistence.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
