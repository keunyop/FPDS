BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TEMP TABLE _source_document_identity_repair (
    old_source_document_id text PRIMARY KEY,
    new_source_document_id text NOT NULL UNIQUE,
    normalized_source_url text NOT NULL
) ON COMMIT DROP;

INSERT INTO _source_document_identity_repair (
    old_source_document_id,
    new_source_document_id,
    normalized_source_url
)
SELECT
    source_document_id,
    'src-'
        || lower(bank_code)
        || '-'
        || source_type
        || '-'
        || left(encode(digest(bank_code || '|' || normalized_source_url || '|' || source_type, 'sha1'), 'hex'), 16),
    normalized_source_url
FROM source_document
WHERE source_document_id <> (
    'src-'
        || lower(bank_code)
        || '-'
        || source_type
        || '-'
        || left(encode(digest(bank_code || '|' || normalized_source_url || '|' || source_type, 'sha1'), 'hex'), 16)
);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM _source_document_identity_repair AS repair
        JOIN source_document AS target
          ON target.source_document_id = repair.new_source_document_id
         AND target.source_document_id <> repair.old_source_document_id
    ) THEN
        RAISE EXCEPTION 'Canonical source document identity repair would collide with an existing source_document_id.';
    END IF;
END $$;

UPDATE source_document AS source
SET
    normalized_source_url = source.normalized_source_url || '#identity-repair-' || source.source_document_id,
    updated_at = now()
FROM _source_document_identity_repair AS repair
WHERE source.source_document_id = repair.old_source_document_id;

INSERT INTO source_document (
    source_document_id,
    bank_code,
    country_code,
    normalized_source_url,
    source_type,
    source_language,
    registry_managed_flag,
    source_metadata,
    discovered_at,
    created_at,
    updated_at
)
SELECT
    repair.new_source_document_id,
    source.bank_code,
    source.country_code,
    repair.normalized_source_url,
    source.source_type,
    source.source_language,
    source.registry_managed_flag,
    source.source_metadata,
    source.discovered_at,
    source.created_at,
    now()
FROM source_document AS source
JOIN _source_document_identity_repair AS repair
  ON repair.old_source_document_id = source.source_document_id;

UPDATE source_snapshot AS target
SET source_document_id = repair.new_source_document_id
FROM _source_document_identity_repair AS repair
WHERE target.source_document_id = repair.old_source_document_id;

UPDATE run_source_item AS target
SET
    source_document_id = repair.new_source_document_id,
    updated_at = now()
FROM _source_document_identity_repair AS repair
WHERE target.source_document_id = repair.old_source_document_id;

UPDATE model_execution AS target
SET source_document_id = repair.new_source_document_id
FROM _source_document_identity_repair AS repair
WHERE target.source_document_id = repair.old_source_document_id;

UPDATE normalized_candidate AS target
SET
    source_document_id = repair.new_source_document_id,
    updated_at = now()
FROM _source_document_identity_repair AS repair
WHERE target.source_document_id = repair.old_source_document_id;

UPDATE field_evidence_link AS target
SET source_document_id = repair.new_source_document_id
FROM _source_document_identity_repair AS repair
WHERE target.source_document_id = repair.old_source_document_id;

DELETE FROM source_document AS source
USING _source_document_identity_repair AS repair
WHERE source.source_document_id = repair.old_source_document_id;

INSERT INTO migration_history (migration_name)
VALUES ('0018_canonical_source_document_identity_repair.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
