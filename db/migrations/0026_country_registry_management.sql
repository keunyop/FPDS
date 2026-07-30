BEGIN;

ALTER TABLE country_registry
    ADD COLUMN IF NOT EXISTS country_name text;

UPDATE country_registry
SET country_name = CASE
    WHEN country_code = 'CA' THEN 'Canada'
    ELSE country_code
END
WHERE country_name IS NULL
   OR btrim(country_name) = '';

ALTER TABLE country_registry
    ALTER COLUMN country_name SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_country_registry_status_name
    ON country_registry (status, country_name, country_code);

INSERT INTO migration_history (migration_name)
VALUES ('0026_country_registry_management.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
