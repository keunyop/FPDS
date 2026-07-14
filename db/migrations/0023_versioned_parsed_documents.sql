BEGIN;

-- Parser upgrades must preserve the prior parsed artifact and its evidence links.
-- A snapshot can therefore have one parsed document per parser version.
ALTER TABLE parsed_document
    DROP CONSTRAINT IF EXISTS parsed_document_snapshot_id_key;

ALTER TABLE parsed_document
    ADD CONSTRAINT parsed_document_snapshot_parser_version_key
    UNIQUE (snapshot_id, parser_version);

CREATE INDEX IF NOT EXISTS idx_parsed_document_snapshot_version
    ON parsed_document (snapshot_id, parser_version, parsed_at DESC);

INSERT INTO migration_history (migration_name)
VALUES ('0023_versioned_parsed_documents.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
