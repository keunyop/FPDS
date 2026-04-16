BEGIN;

ALTER TABLE source_registry_item
    DROP CONSTRAINT IF EXISTS source_registry_item_bank_code_normalized_url_source_type_key;

ALTER TABLE source_registry_item
    ADD CONSTRAINT source_registry_item_bank_code_product_type_normalized_url_source_type_key
    UNIQUE (bank_code, product_type, normalized_url, source_type);

INSERT INTO migration_history (migration_name)
VALUES ('0005_source_registry_unique_scope_fix.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
