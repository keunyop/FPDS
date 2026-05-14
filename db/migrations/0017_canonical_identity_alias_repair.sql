BEGIN;

DO $$
BEGIN
    IF EXISTS (
        WITH bank_alias(alias_code, canonical_code) AS (
            VALUES
                ('RBOC'::text, 'RBC'::text),
                ('TB'::text, 'TD'::text),
                ('SCOTIABANK'::text, 'SCOTIA'::text)
        )
        SELECT 1
        FROM source_document AS alias_doc
        JOIN bank_alias
          ON bank_alias.alias_code = alias_doc.bank_code
        JOIN source_document AS canonical_doc
          ON canonical_doc.bank_code = bank_alias.canonical_code
         AND canonical_doc.normalized_source_url = alias_doc.normalized_source_url
         AND canonical_doc.source_type = alias_doc.source_type
    ) THEN
        RAISE EXCEPTION 'Bank alias repair found duplicate source_document rows. Merge source lineage manually before applying this migration.';
    END IF;
END $$;

WITH bank_alias(alias_code, canonical_code, canonical_name, canonical_homepage_url) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text, 'Royal Bank of Canada'::text, 'https://www.rbcroyalbank.com/'::text),
        ('TB'::text, 'TD'::text, 'TD Bank'::text, 'https://www.td.com/ca/en/personal-banking'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text, 'Scotiabank'::text, 'https://www.scotiabank.com/ca/en/personal.html'::text)
)
INSERT INTO bank (
    bank_code,
    country_code,
    bank_name,
    status,
    homepage_url,
    normalized_homepage_url,
    source_language,
    managed_flag,
    change_reason,
    created_at,
    updated_at
)
SELECT
    bank_alias.canonical_code,
    COALESCE(alias_bank.country_code, 'CA'),
    bank_alias.canonical_name,
    COALESCE(alias_bank.status, 'active'),
    bank_alias.canonical_homepage_url,
    NULL,
    COALESCE(alias_bank.source_language, 'en'),
    true,
    'canonical_identity_alias_repair',
    COALESCE(alias_bank.created_at, now()),
    now()
FROM bank_alias
LEFT JOIN bank AS alias_bank
  ON alias_bank.bank_code = bank_alias.alias_code
ON CONFLICT (bank_code) DO UPDATE SET
    bank_name = EXCLUDED.bank_name,
    status = CASE
        WHEN bank.status = 'inactive' AND EXCLUDED.status = 'active' THEN 'active'
        ELSE bank.status
    END,
    homepage_url = COALESCE(bank.homepage_url, EXCLUDED.homepage_url),
    normalized_homepage_url = bank.normalized_homepage_url,
    source_language = COALESCE(bank.source_language, EXCLUDED.source_language),
    managed_flag = bank.managed_flag OR EXCLUDED.managed_flag,
    change_reason = EXCLUDED.change_reason,
    updated_at = now();

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE source_document AS target
SET
    bank_code = bank_alias.canonical_code,
    source_metadata = CASE
        WHEN target.source_metadata ? 'bank_code'
            THEN jsonb_set(target.source_metadata, '{bank_code}', to_jsonb(bank_alias.canonical_code), false)
        ELSE target.source_metadata
    END,
    updated_at = now()
FROM bank_alias
WHERE target.bank_code = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE normalized_candidate AS target
SET
    bank_code = bank_alias.canonical_code,
    candidate_payload = CASE
        WHEN target.candidate_payload ? 'bank_code'
            THEN jsonb_set(target.candidate_payload, '{bank_code}', to_jsonb(bank_alias.canonical_code), false)
        ELSE target.candidate_payload
    END,
    updated_at = now()
FROM bank_alias
WHERE target.bank_code = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE canonical_product AS target
SET
    bank_code = bank_alias.canonical_code,
    current_snapshot_payload = CASE
        WHEN target.current_snapshot_payload ? 'bank_code'
            THEN jsonb_set(target.current_snapshot_payload, '{bank_code}', to_jsonb(bank_alias.canonical_code), false)
        ELSE target.current_snapshot_payload
    END,
    updated_at = now()
FROM bank_alias
WHERE target.bank_code = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE source_registry_catalog_item AS target
SET
    bank_code = bank_alias.canonical_code,
    change_reason = 'canonical_identity_alias_repair',
    updated_at = now()
FROM bank_alias
WHERE target.bank_code = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE source_registry_item AS target
SET
    bank_code = bank_alias.canonical_code,
    product_key = bank_alias.canonical_code || ':' || target.product_type,
    discovery_metadata = CASE
        WHEN target.discovery_metadata ? 'bank_code'
            THEN jsonb_set(target.discovery_metadata, '{bank_code}', to_jsonb(bank_alias.canonical_code), false)
        ELSE target.discovery_metadata
    END,
    change_reason = 'canonical_identity_alias_repair',
    updated_at = now()
FROM bank_alias
WHERE target.bank_code = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE public_product_projection AS target
SET bank_code = bank_alias.canonical_code
FROM bank_alias
WHERE target.bank_code = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE dashboard_ranking_snapshot AS target
SET bank_code = bank_alias.canonical_code
FROM bank_alias
WHERE target.bank_code = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE dashboard_scatter_snapshot AS target
SET bank_code = bank_alias.canonical_code
FROM bank_alias
WHERE target.bank_code = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE ingestion_run AS target
SET run_metadata = jsonb_set(target.run_metadata, '{bank_code}', to_jsonb(bank_alias.canonical_code), false)
FROM bank_alias
WHERE target.run_metadata ->> 'bank_code' = bank_alias.alias_code;

WITH bank_alias(alias_code, canonical_code) AS (
    VALUES
        ('RBOC'::text, 'RBC'::text),
        ('TB'::text, 'TD'::text),
        ('SCOTIABANK'::text, 'SCOTIA'::text)
)
UPDATE product_version AS target
SET normalized_payload = jsonb_set(target.normalized_payload, '{bank_code}', to_jsonb(bank_alias.canonical_code), false)
FROM bank_alias
WHERE target.normalized_payload ->> 'bank_code' = bank_alias.alias_code;

WITH bank_alias(alias_code) AS (
    VALUES ('RBOC'::text), ('TB'::text), ('SCOTIABANK'::text)
)
DELETE FROM bank
USING bank_alias
WHERE bank.bank_code = bank_alias.alias_code;

WITH bank_alias(canonical_code, canonical_homepage_url) AS (
    VALUES
        ('RBC'::text, 'https://www.rbcroyalbank.com/'::text),
        ('TD'::text, 'https://www.td.com/ca/en/personal-banking'::text),
        ('SCOTIA'::text, 'https://www.scotiabank.com/ca/en/personal.html'::text)
)
UPDATE bank
SET
    normalized_homepage_url = bank_alias.canonical_homepage_url,
    homepage_url = COALESCE(bank.homepage_url, bank_alias.canonical_homepage_url),
    updated_at = now()
FROM bank_alias
WHERE bank.bank_code = bank_alias.canonical_code;

INSERT INTO product_type_registry (
    product_type_code,
    product_family,
    display_name,
    description,
    status,
    managed_flag,
    discovery_keywords,
    expected_fields,
    fallback_policy,
    created_at,
    updated_at
)
VALUES (
    'gic',
    'deposit',
    'GIC',
    'Guaranteed investment certificate and term deposit products.',
    'active',
    true,
    '["gic", "guaranteed investment certificate", "term deposit", "maturity", "redeemable", "minimum deposit"]'::jsonb,
    '["product_name", "description_short", "standard_rate", "promotional_rate", "minimum_deposit", "term_length_text", "term_length_days", "eligibility_text", "notes"]'::jsonb,
    'generic_ai_review',
    now(),
    now()
)
ON CONFLICT (product_type_code) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    description = EXCLUDED.description,
    status = 'active',
    discovery_keywords = EXCLUDED.discovery_keywords,
    expected_fields = EXCLUDED.expected_fields,
    updated_at = now();

UPDATE source_registry_catalog_item
SET
    product_type = 'gic',
    change_reason = 'canonical_identity_alias_repair',
    updated_at = now()
WHERE product_type = 'gic-term-deposit';

UPDATE source_registry_item
SET
    product_type = 'gic',
    product_key = bank_code || ':gic',
    discovery_metadata = CASE
        WHEN discovery_metadata ? 'product_type'
            THEN jsonb_set(discovery_metadata, '{product_type}', to_jsonb('gic'::text), false)
        ELSE discovery_metadata
    END,
    change_reason = 'canonical_identity_alias_repair',
    updated_at = now()
WHERE product_type = 'gic-term-deposit';

UPDATE normalized_candidate
SET
    product_type = 'gic',
    candidate_payload = CASE
        WHEN candidate_payload ? 'product_type'
            THEN jsonb_set(candidate_payload, '{product_type}', to_jsonb('gic'::text), false)
        ELSE candidate_payload
    END,
    updated_at = now()
WHERE product_type = 'gic-term-deposit';

UPDATE canonical_product
SET
    product_type = 'gic',
    current_snapshot_payload = CASE
        WHEN current_snapshot_payload ? 'product_type'
            THEN jsonb_set(current_snapshot_payload, '{product_type}', to_jsonb('gic'::text), false)
        ELSE current_snapshot_payload
    END,
    updated_at = now()
WHERE product_type = 'gic-term-deposit';

UPDATE public_product_projection
SET product_type = 'gic'
WHERE product_type = 'gic-term-deposit';

UPDATE dashboard_ranking_snapshot
SET product_type = 'gic'
WHERE product_type = 'gic-term-deposit';

UPDATE dashboard_scatter_snapshot
SET product_type = 'gic'
WHERE product_type = 'gic-term-deposit';

UPDATE source_document
SET
    source_metadata = jsonb_set(source_metadata, '{product_type}', to_jsonb('gic'::text), false),
    updated_at = now()
WHERE source_metadata ->> 'product_type' = 'gic-term-deposit';

UPDATE ingestion_run
SET run_metadata = jsonb_set(run_metadata, '{product_type}', to_jsonb('gic'::text), false)
WHERE run_metadata ->> 'product_type' = 'gic-term-deposit';

UPDATE product_version
SET normalized_payload = jsonb_set(normalized_payload, '{product_type}', to_jsonb('gic'::text), false)
WHERE normalized_payload ->> 'product_type' = 'gic-term-deposit';

DELETE FROM taxonomy_registry
WHERE product_type = 'gic-term-deposit';

DELETE FROM product_type_registry
WHERE product_type_code = 'gic-term-deposit';

UPDATE public_product_projection AS projection
SET bank_name = bank.bank_name
FROM bank
WHERE projection.bank_code = bank.bank_code;

UPDATE dashboard_ranking_snapshot AS ranking
SET bank_name = bank.bank_name
FROM bank
WHERE ranking.bank_code = bank.bank_code;

UPDATE dashboard_scatter_snapshot AS scatter
SET bank_name = bank.bank_name
FROM bank
WHERE scatter.bank_code = bank.bank_code;

INSERT INTO migration_history (migration_name)
VALUES ('0017_canonical_identity_alias_repair.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
