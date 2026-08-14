BEGIN;

-- A generic online-banking service agreement can be linked from a product
-- page but does not state that product's pricing. Keep the row for audit
-- history while removing it from future evidence collection scope.
UPDATE source_registry_item
SET
    status = 'inactive',
    change_reason = 'excluded_generic_service_agreement_companion_2026_08_12',
    updated_at = now()
WHERE country_code = 'US'
  AND status = 'active'
  AND discovery_role IN ('supporting_html', 'linked_pdf')
  AND discovery_metadata->>'selection_path' IN (
      'selected_detail_companion',
      'selected_existing_detail_companion'
  )
  AND (
      lower(normalized_url) LIKE '%/online-banking/service-agreement%'
      OR lower(normalized_url) LIKE '%/service-agreement.go%'
  );

INSERT INTO migration_history (migration_name)
VALUES ('0037_us_pricing_companion_scope_cleanup.sql')
ON CONFLICT (migration_name) DO NOTHING;

COMMIT;
