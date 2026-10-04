-- Country-owned required/optional collection targets; financial baselines stay in code.
BEGIN;

ALTER TABLE product_type_registry
    ADD COLUMN IF NOT EXISTS collection_field_policy jsonb NOT NULL DEFAULT '{}'::jsonb;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'product_type_collection_field_policy_object'
          AND conrelid = 'product_type_registry'::regclass
    ) THEN
        ALTER TABLE product_type_registry
            ADD CONSTRAINT product_type_collection_field_policy_object
            CHECK (jsonb_typeof(collection_field_policy) = 'object');
    END IF;
END;
$$;

COMMENT ON COLUMN product_type_registry.collection_field_policy IS
    'Country-keyed typed required/optional collection targets; protected financial essentials remain executable.';

INSERT INTO migration_history (migration_name)
VALUES ('0047_product_type_collection_fields.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
