BEGIN;

-- Historical broad supporting-source expansion attached auto-loan pages to a
-- US credit-card scope. They remain visible in history but must not be fetched
-- or considered as card pricing evidence.
UPDATE source_registry_item
SET
    status = 'inactive',
    change_reason = 'excluded_cross_product_support_2026_08_12',
    updated_at = now()
WHERE country_code = 'US'
  AND product_type = 'credit-card'
  AND status = 'active'
  AND discovery_role IN ('supporting_html', 'linked_pdf')
  AND (
      lower(normalized_url) LIKE '%/auto-loan%'
      OR lower(normalized_url) LIKE '%/vehicle-loan%'
      OR lower(source_name) LIKE '%auto loan%'
      OR lower(purpose) LIKE '%auto loan%'
  );

INSERT INTO migration_history (migration_name)
VALUES ('0038_us_cross_product_support_cleanup.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
