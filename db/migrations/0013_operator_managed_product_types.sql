BEGIN;

DROP INDEX IF EXISTS idx_product_type_registry_lookup;

ALTER TABLE product_type_registry
    DROP COLUMN IF EXISTS built_in_flag;

CREATE INDEX IF NOT EXISTS idx_product_type_registry_lookup
    ON product_type_registry (product_family, status, display_name);

INSERT INTO migration_history (migration_name)
VALUES ('0013_operator_managed_product_types.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
